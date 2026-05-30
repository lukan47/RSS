from fastapi import APIRouter, HTTPException
from typing import List

from models import VM, Template, VMCreateSpec, Network
from dependencies import get_hypervisor

router = APIRouter(prefix="/vms", tags=["vms"])


@router.get("", response_model=List[VM])
async def list_vms():
    hv = get_hypervisor()
    if hv is None:
        return []
    return await hv.list_vms()


@router.get("/templates", response_model=List[Template])
async def list_templates():
    hv = get_hypervisor()
    if hv is None:
        return []
    return await hv.list_templates()


@router.get("/networks", response_model=List[Network])
async def list_networks():
    hv = get_hypervisor()
    if hv is None:
        return []
    return await hv.list_networks()


@router.get("/{vm_id}", response_model=VM)
async def get_vm(vm_id: str):
    hv = get_hypervisor()
    if hv is None:
        raise HTTPException(503, "Hypervisor not configured")
    return await hv.get_vm(vm_id)


@router.post("", response_model=VM, status_code=201)
async def create_vm(spec: VMCreateSpec):
    hv = get_hypervisor()
    if hv is None:
        raise HTTPException(503, "Hypervisor not configured")
    return await hv.create_vm(spec)


@router.delete("/{vm_id}", status_code=204)
async def delete_vm(vm_id: str):
    hv = get_hypervisor()
    if hv is None:
        raise HTTPException(503, "Hypervisor not configured")
    await hv.delete_vm(vm_id)


@router.post("/{vm_id}/power/on", status_code=204)
async def power_on(vm_id: str):
    hv = get_hypervisor()
    if hv is None:
        raise HTTPException(503, "Hypervisor not configured")
    await hv.power_on(vm_id)


@router.post("/{vm_id}/power/off", status_code=204)
async def power_off(vm_id: str):
    hv = get_hypervisor()
    if hv is None:
        raise HTTPException(503, "Hypervisor not configured")
    await hv.power_off(vm_id)
