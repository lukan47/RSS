"""
Deployment pipeline: create VM → power on → wait for SSH →
detect OS → run prep script → run perf test → collect results.

Log entries are pushed to an asyncio.Queue so the WebSocket handler
can stream them in real time without blocking.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from models import (
    Deployment,
    DeploymentSpec,
    DeploymentStatus,
    LogEntry,
    LogLevel,
    OSType,
)
from hypervisors.base import HypervisorBase
from provisioner.ssh_manager import SSHManager, wait_for_ssh

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"

_OS_DIR: Dict[OSType, str] = {
    OSType.RHEL: "rhel",
    OSType.CENTOS: "rhel",
    OSType.UBUNTU: "ubuntu",
    OSType.DEBIAN: "ubuntu",
    OSType.WINDOWS: "windows",
}


class DeploymentPipeline:
    def __init__(self, hypervisor: HypervisorBase):
        self._hv = hypervisor
        # deployment_id → asyncio.Queue of LogEntry (None = closed)
        self._queues: Dict[str, asyncio.Queue] = {}
        self._deployments: Dict[str, Deployment] = {}

    def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        return self._deployments.get(deployment_id)

    def all_deployments(self):
        return list(self._deployments.values())

    async def subscribe(self, deployment_id: str) -> asyncio.Queue:
        """Return a queue that receives LogEntry objects (None = done)."""
        q: asyncio.Queue = asyncio.Queue()
        # Replay existing logs
        dep = self._deployments.get(deployment_id)
        if dep:
            for entry in dep.logs:
                await q.put(entry)
            if dep.status in (DeploymentStatus.COMPLETED, DeploymentStatus.FAILED):
                await q.put(None)
                return q
        self._queues.setdefault(deployment_id, q)
        return q

    async def start(self, spec: DeploymentSpec) -> Deployment:
        dep_id = f"dep-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        dep = Deployment(
            id=dep_id,
            status=DeploymentStatus.PENDING,
            started_at=datetime.now(timezone.utc),
        )
        self._deployments[dep_id] = dep
        asyncio.create_task(self._run(dep_id, spec))
        return dep

    async def _log(self, dep_id: str, message: str, level: LogLevel = LogLevel.INFO) -> None:
        entry = LogEntry(timestamp=datetime.now(timezone.utc), level=level, message=message)
        dep = self._deployments[dep_id]
        dep.logs.append(entry)
        q = self._queues.get(dep_id)
        if q:
            await q.put(entry)

    async def _run(self, dep_id: str, spec: DeploymentSpec) -> None:
        dep = self._deployments[dep_id]
        dep.status = DeploymentStatus.RUNNING
        ssh: Optional[SSHManager] = None

        try:
            # Step 1: Resolve VM
            if spec.vm_create_spec:
                await self._log(dep_id, f"Creating VM '{spec.vm_create_spec.name}'...")
                vm = await self._hv.create_vm(spec.vm_create_spec)
                dep.vm_id = vm.id
                dep.vm_name = vm.name
                await self._log(dep_id, f"VM created: {vm.id}", LogLevel.SUCCESS)
            else:
                vm = await self._hv.get_vm(spec.vm_id)
                dep.vm_id = vm.id
                dep.vm_name = vm.name
                await self._log(dep_id, f"Using existing VM: {vm.name}")

            # Step 2: Power on
            await self._log(dep_id, "Powering on VM...")
            await self._hv.power_on(vm.id)

            # Step 3: Wait for IP
            await self._log(dep_id, "Waiting for VM to get an IP address (up to 5 min)...")
            ip = await self._wait_for_ip(dep_id, vm.id, timeout=300)
            await self._log(dep_id, f"VM IP: {ip}", LogLevel.SUCCESS)

            # Step 4: Wait for SSH
            await self._log(dep_id, f"Connecting via SSH to {ip}...")
            ssh = await wait_for_ssh(ip, spec.ssh_credentials, timeout=300)
            await self._log(dep_id, "SSH connection established.", LogLevel.SUCCESS)

            # Step 5: Detect OS
            os_type = spec.os_type
            if os_type is None:
                await self._log(dep_id, "Detecting OS...")
                os_type = await ssh.detect_os()
                await self._log(dep_id, f"Detected OS: {os_type.value}", LogLevel.SUCCESS)

            os_dir = _OS_DIR.get(os_type, "rhel")

            # Step 6: Prep
            if spec.run_prep:
                await self._log(dep_id, "Running prep script (installing test tools)...")
                await self._run_script(dep_id, ssh, os_type, os_dir, "prep")

            # Step 7: Perf test
            if spec.run_perf_test:
                await self._log(dep_id, "Running performance tests...")
                results = await self._run_script(dep_id, ssh, os_type, os_dir, "perf_test", capture=True)
                dep.results = {"raw_output": results}
                await self._log(dep_id, "Performance test completed.", LogLevel.SUCCESS)

            dep.status = DeploymentStatus.COMPLETED
            await self._log(dep_id, "Deployment pipeline finished successfully.", LogLevel.SUCCESS)

        except Exception as exc:
            dep.status = DeploymentStatus.FAILED
            await self._log(dep_id, f"Pipeline failed: {exc}", LogLevel.ERROR)
        finally:
            dep.completed_at = datetime.now(timezone.utc)
            if ssh:
                await ssh.disconnect()
            q = self._queues.get(dep_id)
            if q:
                await q.put(None)

    async def _wait_for_ip(self, dep_id: str, vm_id: str, timeout: float = 300) -> str:
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            ip = await self._hv.get_vm_ip(vm_id)
            if ip:
                return ip
            await asyncio.sleep(10)
        raise TimeoutError(f"VM {vm_id} did not receive an IP address within {timeout}s")

    async def _run_script(
        self,
        dep_id: str,
        ssh: SSHManager,
        os_type: OSType,
        os_dir: str,
        script_name: str,
        capture: bool = False,
    ) -> str:
        is_windows = os_type == OSType.WINDOWS
        ext = "ps1" if is_windows else "sh"
        script_path = SCRIPTS_DIR / os_dir / f"{script_name}.{ext}"

        if not script_path.exists():
            await self._log(dep_id, f"Script not found: {script_path}", LogLevel.WARNING)
            return ""

        script_content = script_path.read_text()
        remote_path = f"/tmp/{script_name}.{ext}" if not is_windows else f"C:\\Temp\\{script_name}.{ext}"

        # Create temp dir on Windows
        if is_windows:
            await ssh.run("New-Item -ItemType Directory -Force -Path C:\\Temp | Out-Null")

        await ssh.upload_string(script_content, remote_path)

        if is_windows:
            cmd = f"powershell -ExecutionPolicy Bypass -File {remote_path}"
        else:
            await ssh.run(f"chmod +x {remote_path}")
            cmd = f"bash {remote_path}"

        code, stdout, stderr = await ssh.run(cmd)

        for line in (stdout + stderr).splitlines():
            if line.strip():
                await self._log(dep_id, f"  {line}")

        if code != 0:
            await self._log(dep_id, f"Script exited with code {code}", LogLevel.WARNING)

        return stdout
