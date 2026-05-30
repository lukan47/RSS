"""
Proxmox VE adapter using the Proxmox REST API.

Supports both username/password auth (ticket) and API token auth.
VMs in Proxmox are scoped to nodes; this adapter defaults to the first
available node but allows per-VM targeting via the ``node`` field.
"""

from typing import Any, Dict, List, Optional

import httpx

from models import (
    HypervisorType,
    Network,
    OSType,
    Template,
    VM,
    VMCreateSpec,
    VMPowerState,
)
from .base import HypervisorBase

_POWER_MAP = {
    "running": VMPowerState.ON,
    "stopped": VMPowerState.OFF,
    "paused": VMPowerState.SUSPENDED,
}

_OS_HINTS: Dict[str, OSType] = {
    "rhel": OSType.RHEL,
    "centos": OSType.CENTOS,
    "ubuntu": OSType.UBUNTU,
    "debian": OSType.DEBIAN,
    "win": OSType.WINDOWS,
    "windows": OSType.WINDOWS,
}


def _guess_os(name: str) -> Optional[OSType]:
    lower = name.lower()
    for hint, os_type in _OS_HINTS.items():
        if hint in lower:
            return os_type
    return None


class ProxmoxHypervisor(HypervisorBase):
    def __init__(
        self,
        host: str,
        user: str,
        password: str = "",
        token_id: str = "",
        token_secret: str = "",
        verify_ssl: bool = False,
    ):
        self._base = f"https://{host}:8006/api2/json"
        self._user = user
        self._password = password
        self._token_id = token_id
        self._token_secret = token_secret
        self._verify_ssl = verify_ssl
        self._ticket: Optional[str] = None
        self._csrf: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(verify=self._verify_ssl, timeout=30)
        return self._client

    def _token_header(self) -> Dict[str, str]:
        realm, name = self._user.split("@") if "@" in self._user else (self._user, self._user)
        return {"Authorization": f"PVEAPIToken={self._user}!{self._token_id}={self._token_secret}"}

    async def _ensure_ticket(self) -> None:
        if self._ticket:
            return
        client = await self._get_client()
        resp = await client.post(
            f"{self._base}/access/ticket",
            data={"username": self._user, "password": self._password},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        self._ticket = data["ticket"]
        self._csrf = data["CSRFPreventionToken"]

    def _use_token_auth(self) -> bool:
        return bool(self._token_id and self._token_secret)

    async def _headers(self) -> Dict[str, str]:
        if self._use_token_auth():
            return self._token_header()
        await self._ensure_ticket()
        return {
            "CSRFPreventionToken": self._csrf or "",
            "Cookie": f"PVEAuthCookie={self._ticket}",
        }

    async def _get(self, path: str) -> Any:
        client = await self._get_client()
        resp = await client.get(f"{self._base}{path}", headers=await self._headers())
        resp.raise_for_status()
        return resp.json().get("data", resp.json())

    async def _post(self, path: str, data: Any = None) -> Any:
        client = await self._get_client()
        resp = await client.post(
            f"{self._base}{path}", headers=await self._headers(), data=data
        )
        resp.raise_for_status()
        return resp.json().get("data")

    async def _delete(self, path: str) -> Any:
        client = await self._get_client()
        resp = await client.delete(f"{self._base}{path}", headers=await self._headers())
        resp.raise_for_status()
        return resp.json().get("data")

    async def _default_node(self) -> str:
        nodes = await self._get("/nodes")
        if not nodes:
            raise RuntimeError("No Proxmox nodes found")
        return nodes[0]["node"]

    def _parse_vm(self, raw: Dict, node: str) -> VM:
        vm_id = str(raw["vmid"])
        name = raw.get("name", vm_id)
        return VM(
            id=f"{node}/{vm_id}",
            name=name,
            power_state=_POWER_MAP.get(raw.get("status", ""), VMPowerState.UNKNOWN),
            cpu_count=raw.get("cpus", 0),
            memory_mb=raw.get("maxmem", 0) // 1024 // 1024,
            os_type=_guess_os(name),
            hypervisor=HypervisorType.PROXMOX,
            node=node,
        )

    async def list_vms(self) -> List[VM]:
        nodes = await self._get("/nodes")
        vms: List[VM] = []
        for node_info in nodes:
            node = node_info["node"]
            raw_vms = await self._get(f"/nodes/{node}/qemu")
            vms.extend(self._parse_vm(v, node) for v in raw_vms)
        return vms

    def _split_id(self, vm_id: str):
        parts = vm_id.split("/", 1)
        return (parts[0], parts[1]) if len(parts) == 2 else (None, parts[0])

    async def get_vm(self, vm_id: str) -> VM:
        node, vmid = self._split_id(vm_id)
        if not node:
            node = await self._default_node()
        data = await self._get(f"/nodes/{node}/qemu/{vmid}/status/current")
        data["vmid"] = vmid
        vm = self._parse_vm(data, node)
        vm.ip_address = await self.get_vm_ip(vm_id)
        return vm

    async def create_vm(self, spec: VMCreateSpec) -> VM:
        node = spec.node or await self._default_node()
        existing = await self._get(f"/nodes/{node}/qemu")
        next_id = max((int(v["vmid"]) for v in existing), default=100) + 1

        if spec.template_id:
            # Clone from template
            tmpl_node, tmpl_id = self._split_id(spec.template_id)
            if not tmpl_node:
                tmpl_node = node
            await self._post(
                f"/nodes/{tmpl_node}/qemu/{tmpl_id}/clone",
                data={
                    "newid": next_id,
                    "name": spec.name,
                    "target": node,
                    "full": 1,
                },
            )
        else:
            await self._post(
                f"/nodes/{node}/qemu",
                data={
                    "vmid": next_id,
                    "name": spec.name,
                    "cores": spec.cpu_count,
                    "memory": spec.memory_mb,
                },
            )

        return await self.get_vm(f"{node}/{next_id}")

    async def delete_vm(self, vm_id: str) -> None:
        node, vmid = self._split_id(vm_id)
        if not node:
            node = await self._default_node()
        await self._delete(f"/nodes/{node}/qemu/{vmid}")

    async def power_on(self, vm_id: str) -> None:
        node, vmid = self._split_id(vm_id)
        if not node:
            node = await self._default_node()
        await self._post(f"/nodes/{node}/qemu/{vmid}/status/start")

    async def power_off(self, vm_id: str) -> None:
        node, vmid = self._split_id(vm_id)
        if not node:
            node = await self._default_node()
        await self._post(f"/nodes/{node}/qemu/{vmid}/status/stop")

    async def get_vm_ip(self, vm_id: str) -> Optional[str]:
        node, vmid = self._split_id(vm_id)
        if not node:
            node = await self._default_node()
        try:
            ifaces = await self._get(f"/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces")
            for iface in ifaces.get("result", []):
                for addr in iface.get("ip-addresses", []):
                    ip = addr.get("ip-address", "")
                    if ip and not ip.startswith("127.") and ":" not in ip:
                        return ip
        except Exception:
            pass
        return None

    async def list_templates(self) -> List[Template]:
        nodes = await self._get("/nodes")
        templates: List[Template] = []
        for node_info in nodes:
            node = node_info["node"]
            vms = await self._get(f"/nodes/{node}/qemu")
            for v in vms:
                if v.get("template") == 1:
                    vmid = str(v["vmid"])
                    name = v.get("name", vmid)
                    templates.append(
                        Template(
                            id=f"{node}/{vmid}",
                            name=name,
                            os_type=_guess_os(name),
                            hypervisor=HypervisorType.PROXMOX,
                        )
                    )
        return templates

    async def list_networks(self) -> List[Network]:
        try:
            node = await self._default_node()
            nets = await self._get(f"/nodes/{node}/network")
            return [
                Network(id=n.get("iface", ""), name=n.get("iface", ""))
                for n in nets
                if n.get("type") in ("bridge", "bond")
            ]
        except Exception:
            return []

    async def test_connection(self) -> bool:
        try:
            self._ticket = None
            await self._get("/nodes")
            return True
        except Exception:
            return False
