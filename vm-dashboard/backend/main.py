from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.vms import router as vms_router
from api.deployments import router as deployments_router
from api.settings import router as settings_router
from dependencies import initialise


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialise()
    yield


app = FastAPI(title="VM Dashboard API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vms_router, prefix="/api")
app.include_router(deployments_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

# Serve the built React frontend in production
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
