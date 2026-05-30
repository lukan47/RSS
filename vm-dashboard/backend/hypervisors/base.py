from abc import ABC, abstractmethod
from typing import List, Optional
from models import VM, Template, VMCreateSpec, Network


class HypervisorBase(ABC):
    @abstractmethod
    async def list_vms(self) -> List[VM]: ...

    @abstractmethod
    async def get_vm(self, vm_id: str) -> VM: ...

    @abstractmethod
    async def create_vm(self, spec: VMCreateSpec) -> VM: ...

    @abstractmethod
    async def delete_vm(self, vm_id: str) -> None: ...

    @abstractmethod
    async def power_on(self, vm_id: str) -> None: ...

    @abstractmethod
    async def power_off(self, vm_id: str) -> None: ...

    @abstractmethod
    async def get_vm_ip(self, vm_id: str) -> Optional[str]: ...

    @abstractmethod
    async def list_templates(self) -> List[Template]: ...

    @abstractmethod
    async def list_networks(self) -> List[Network]: ...

    @abstractmethod
    async def test_connection(self) -> bool: ...
