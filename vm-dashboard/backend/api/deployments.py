import asyncio
import json
from typing import List

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from models import Deployment, DeploymentSpec, LogEntry
from dependencies import get_hypervisor, get_pipeline

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.post("", response_model=Deployment, status_code=202)
async def start_deployment(spec: DeploymentSpec):
    hv = get_hypervisor()
    if hv is None:
        raise HTTPException(503, "Hypervisor not configured")
    pipeline = get_pipeline(hv)
    return await pipeline.start(spec)


@router.get("", response_model=List[Deployment])
async def list_deployments():
    hv = get_hypervisor()
    if hv is None:
        return []
    pipeline = get_pipeline(hv)
    return pipeline.all_deployments()


@router.get("/{deployment_id}", response_model=Deployment)
async def get_deployment(deployment_id: str):
    hv = get_hypervisor()
    if hv is None:
        raise HTTPException(503, "Hypervisor not configured")
    pipeline = get_pipeline(hv)
    dep = pipeline.get_deployment(deployment_id)
    if dep is None:
        raise HTTPException(404, "Deployment not found")
    return dep


@router.websocket("/{deployment_id}/logs")
async def stream_logs(websocket: WebSocket, deployment_id: str):
    await websocket.accept()
    hv = get_hypervisor()
    if hv is None:
        await websocket.send_text(json.dumps({"error": "Hypervisor not configured"}))
        await websocket.close()
        return

    pipeline = get_pipeline(hv)
    dep = pipeline.get_deployment(deployment_id)
    if dep is None:
        await websocket.send_text(json.dumps({"error": "Deployment not found"}))
        await websocket.close()
        return

    queue = await pipeline.subscribe(deployment_id)
    try:
        while True:
            entry = await asyncio.wait_for(queue.get(), timeout=30)
            if entry is None:
                await websocket.send_text(json.dumps({"done": True}))
                break
            await websocket.send_text(entry.model_dump_json())
    except asyncio.TimeoutError:
        pass
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
