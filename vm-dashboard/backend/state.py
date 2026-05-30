"""Mutable application state shared across modules."""
from typing import Optional
from models import HypervisorSettings
from hypervisors.base import HypervisorBase
from provisioner.pipeline import DeploymentPipeline

current_settings: Optional[HypervisorSettings] = None
hypervisor: Optional[HypervisorBase] = None
pipeline: Optional[DeploymentPipeline] = None
