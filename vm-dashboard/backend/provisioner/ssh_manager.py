"""SSH manager — wraps asyncssh to run commands and upload files on remote VMs."""

import asyncio
from pathlib import Path
from typing import Optional, Tuple

import asyncssh

from models import OSType, SSHCredentials


class SSHManager:
    def __init__(self, host: str, creds: SSHCredentials):
        self._host = host
        self._creds = creds
        self._conn: Optional[asyncssh.SSHClientConnection] = None

    async def connect(self, timeout: float = 30) -> None:
        kwargs = dict(
            host=self._host,
            port=self._creds.port,
            username=self._creds.username,
            known_hosts=None,
            connect_timeout=timeout,
        )
        if self._creds.private_key:
            kwargs["client_keys"] = [asyncssh.import_private_key(self._creds.private_key)]
        elif self._creds.password:
            kwargs["password"] = self._creds.password

        self._conn = await asyncssh.connect(**kwargs)

    async def disconnect(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    async def run(self, command: str) -> Tuple[int, str, str]:
        if not self._conn:
            raise RuntimeError("SSH not connected")
        result = await self._conn.run(command, check=False)
        return result.exit_status, result.stdout or "", result.stderr or ""

    async def upload_file(self, local_path: str, remote_path: str) -> None:
        if not self._conn:
            raise RuntimeError("SSH not connected")
        await asyncssh.scp(local_path, (self._conn, remote_path))

    async def upload_string(self, content: str, remote_path: str) -> None:
        """Write a string directly to a remote file."""
        if not self._conn:
            raise RuntimeError("SSH not connected")
        async with self._conn.start_sftp_client() as sftp:
            async with sftp.open(remote_path, "w") as f:
                await f.write(content)

    async def detect_os(self) -> OSType:
        # Try Linux first
        code, stdout, _ = await self.run("cat /etc/os-release 2>/dev/null || true")
        if stdout:
            lower = stdout.lower()
            if "rhel" in lower or "red hat" in lower:
                return OSType.RHEL
            if "centos" in lower:
                return OSType.CENTOS
            if "ubuntu" in lower:
                return OSType.UBUNTU
            if "debian" in lower:
                return OSType.DEBIAN
            return OSType.UNKNOWN

        # Try Windows (PowerShell)
        code, stdout, _ = await self.run("(Get-WmiObject Win32_OperatingSystem).Caption")
        if stdout and "Windows" in stdout:
            return OSType.WINDOWS

        return OSType.UNKNOWN


async def wait_for_ssh(
    host: str,
    creds: SSHCredentials,
    timeout: float = 300,
    interval: float = 10,
) -> SSHManager:
    deadline = asyncio.get_event_loop().time() + timeout
    last_exc: Optional[Exception] = None
    while asyncio.get_event_loop().time() < deadline:
        try:
            mgr = SSHManager(host, creds)
            await mgr.connect(timeout=10)
            return mgr
        except Exception as exc:
            last_exc = exc
            await asyncio.sleep(interval)
    raise TimeoutError(f"SSH not available on {host} after {timeout}s: {last_exc}")
