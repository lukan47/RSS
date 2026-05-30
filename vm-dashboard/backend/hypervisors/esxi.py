"""
ESXi / vCenter adapter using the vSphere REST API (v7.0+).

All requests use a session token obtained at construction time.
SSL verification is disabled by default because vCenter commonly uses
self-signed certificates in lab environments.
"""

import ssl
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
    "POWERED_ON": VMPowerState.ON,
    "POWERED_OFF": VMPowerState.OFF,
    "SUSPENDED": VMPowerState.SUSPENDED,
}

_OS_HINTS: Dict[str, OSType] = {
    "rhel": OSType.RHEL,
    "centos": OSType.CENTOS,
    "ubuntu": OSType.UBUNTU,
    "debian": OSType.DEBIAN,
    "windows": OSType.WINDOWS,
}


def _guess_os(guest_os: str) -> Optional[OSType]:
    lower = guest_os.lower()
    for hint, os_type in _OS_HINTS.items():
        if hint in lower:
            return os_type
    return None


class ESXiHypervisor(HypervisorBase):
    def __init__(self, host: str, user: str, password: str, verify_ssl: bool = False):
        self._base = f"https://{host}/api"
        self._auth = (user, password)
        self._verify_ssl = verify_ssl
        self._session_id: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(verify=self._verify_ssl, timeout=30)
        return self._client

    async def _ensure_session(self) -> str:
        if self._session_id:
            return self._session_id
        client = await self._get_client()
        resp = await client.post(
            f"{self._base}/session",
            auth=self._auth,
        )
        resp.raise_for_status()
        self._session_id = resp.json()
        return self._session_id

    async def _get(self, path: str, **kwargs) -> Any:
        sid = await self._ensure_session()
        client = await self._get_client()
        resp = await client.get(
            f"{self._base}{path}",
            headers={"vmware-api-session-id": sid},
            **kwargs,
        )
        if resp.status_code == 401:
            self._session_id = None
            sid = await self._ensure_session()
            resp = await client.get(
                f"{self._base}{path}",
                headers={"vmware-api-session-id": sid},
                **kwargs,
            )
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json: Any = None, **kwargs) -> Any:
        sid = await self._ensure_session()
        client = await self._get_client()
        resp = await client.post(
            f"{self._base}{path}",
            headers={"vmware-api-session-id": sid},
            json=json,
            **kwargs,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else None

    async def _delete(self, path: str) -> None:
        sid = await self._ensure_session()
        client = await self._get_client()
        resp = await client.delete(
            f"{self._base}{path}",
            headers={"vmware-api-session-id": sid},
        )
        resp.raise_for_status()

    def _parse_vm(self, raw: Dict) -> VM:
        vm_id = raw.get("vm", raw.get("id", ""))
        guest_os = raw.get("guest_OS", "")
        return VM(
            id=vm_id,
            name=raw.get("name", vm_id),
            power_state=_POWER_MAP.get(raw.get("power_state", ""), VMPowerState.UNKNOWN),
            cpu_count=raw.get("cpu_count", 0),
            memory_mb=raw.get("memory_size_MiB", 0),
            os_type=_guess_os(guest_os),
            guest_os=guest_os,
            hypervisor=HypervisorType.ESXI,
        )

    async def list_vms(self) -> List[VM]:
        data = await self._get("/vcenter/vm")
        return [self._parse_vm(v) for v in data]

    async def get_vm(self, vm_id: str) -> VM:
        data = await self._get(f"/vcenter/vm/{vm_id}")
        data["vm"] = vm_id
        vm = self._parse_vm(data)
        vm.ip_address = await self.get_vm_ip(vm_id)
        return vm

    async def create_vm(self, spec: VMCreateSpec) -> VM:
        body: Dict[str, Any] = {
            "spec": {
                "name": spec.name,
                "guest_OS": "RHEL_9_64",  # default; real deployments clone from template
            }
        }
        if spec.template_id:
            # Use instant clone / linked clone from library item
            body = {
                "spec": {
                    "source": spec.template_id,
                    "name": spec.name,
                    "hardware_customization": {
                        "cpu_update": {"num_cpus": spec.cpu_count},
                        "memory_update": {"memory": spec.memory_mb},
                    },
                }
            }
            result = await self._post("/vcenter/vm?action=instant-clone", json=body)
        else:
            result = await self._post("/vcenter/vm", json=body)

        vm_id = result if isinstance(result, str) else result.get("value", result)
        return await self.get_vm(vm_id)

    async def delete_vm(self, vm_id: str) -> None:
        await self._delete(f"/vcenter/vm/{vm_id}")

    async def power_on(self, vm_id: str) -> None:
        await self._post(f"/vcenter/vm/{vm_id}/power?action=start")

    async def power_off(self, vm_id: str) -> None:
        await self._post(f"/vcenter/vm/{vm_id}/power?action=stop")

    async def get_vm_ip(self, vm_id: str) -> Optional[str]:
        try:
            data = await self._get(f"/vcenter/vm/{vm_id}/guest/networking/interfaces")
            for iface in data:
                for addr in iface.get("ip", {}).get("ip_addresses", []):
                    ip = addr.get("ip_address", "")
                    if ip and not ip.startswith("127.") and ":" not in ip:
                        return ip
        except Exception:
            pass
        return None

    async def list_templates(self) -> List[Template]:
        try:
            items = await self._get("/content/library/item")
            templates = []
            for item_id in items:
                try:
                    item = await self._get(f"/content/library/item/{item_id}")
                    templates.append(
                        Template(
                            id=item_id,
                            name=item.get("name", item_id),
                            os_type=_guess_os(item.get("description", "")),
                            hypervisor=HypervisorType.ESXI,
                            description=item.get("description"),
                        )
                    )
                except Exception:
                    continue
            return templates
        except Exception:
            return []

    async def list_networks(self) -> List[Network]:
        try:
            data = await self._get("/vcenter/network")
            return [Network(id=n.get("network", n.get("id", "")), name=n.get("name", "")) for n in data]
        except Exception:
            return []

    async def test_connection(self) -> bool:
        try:
            self._session_id = None
            await self._ensure_session()
            return True
        except Exception:
            return False
