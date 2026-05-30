from fastapi import APIRouter
from models import HypervisorSettings
from dependencies import rebuild_hypervisor, get_current_settings
import state

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=HypervisorSettings)
async def get_settings():
    return get_current_settings()


@router.put("", response_model=HypervisorSettings)
async def update_settings(new_settings: HypervisorSettings):
    state.current_settings = new_settings
    rebuild_hypervisor(new_settings)
    return new_settings


@router.post("/test")
async def test_connection():
    from dependencies import get_hypervisor
    hv = get_hypervisor()
    if hv is None:
        return {"ok": False, "message": "Hypervisor not configured"}
    ok = await hv.test_connection()
    return {"ok": ok, "message": "Connection successful" if ok else "Connection failed"}
