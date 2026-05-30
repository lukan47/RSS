"""
Hypervisor and pipeline factory.

The active hypervisor instance is rebuilt whenever settings change.
Using a module-level singleton avoids heavyweight re-construction on
every request while keeping the logic testable.
"""
from typing import Optional

import state
from config import settings as env_settings
from models import HypervisorSettings
from hypervisors.base import HypervisorBase
from hypervisors.esxi import ESXiHypervisor
from hypervisors.proxmox import ProxmoxHypervisor
from provisioner.pipeline import DeploymentPipeline


def _build_from_settings(s: HypervisorSettings) -> Optional[HypervisorBase]:
    if s.active_hypervisor == "proxmox" and s.proxmox_host:
        return ProxmoxHypervisor(
            host=s.proxmox_host,
            user=s.proxmox_user,
            password=s.proxmox_password,
            token_id=s.proxmox_token_id,
            token_secret=s.proxmox_token_secret,
            verify_ssl=s.proxmox_verify_ssl,
        )
    if s.esxi_host:
        return ESXiHypervisor(
            host=s.esxi_host,
            user=s.esxi_user,
            password=s.esxi_password,
            verify_ssl=s.esxi_verify_ssl,
        )
    return None


def _boot_settings() -> HypervisorSettings:
    return HypervisorSettings(
        esxi_host=env_settings.esxi_host,
        esxi_user=env_settings.esxi_user,
        esxi_password=env_settings.esxi_password,
        esxi_verify_ssl=env_settings.esxi_verify_ssl,
        proxmox_host=env_settings.proxmox_host,
        proxmox_user=env_settings.proxmox_user,
        proxmox_password=env_settings.proxmox_password,
        proxmox_token_id=env_settings.proxmox_token_id,
        proxmox_token_secret=env_settings.proxmox_token_secret,
        proxmox_verify_ssl=env_settings.proxmox_verify_ssl,
        active_hypervisor=env_settings.active_hypervisor,
        default_ssh_user=env_settings.default_ssh_user,
        default_ssh_password=env_settings.default_ssh_password,
        default_ssh_key_path=env_settings.default_ssh_key_path,
    )


def initialise() -> None:
    """Called at startup to build the hypervisor from env / .env file."""
    boot = _boot_settings()
    state.current_settings = boot
    state.hypervisor = _build_from_settings(boot)
    if state.hypervisor:
        state.pipeline = DeploymentPipeline(state.hypervisor)


def rebuild_hypervisor(new_settings: HypervisorSettings) -> None:
    state.hypervisor = _build_from_settings(new_settings)
    if state.hypervisor:
        state.pipeline = DeploymentPipeline(state.hypervisor)
    else:
        state.pipeline = None


def get_hypervisor() -> Optional[HypervisorBase]:
    return state.hypervisor


def get_pipeline(hv: HypervisorBase) -> DeploymentPipeline:
    if state.pipeline is None:
        state.pipeline = DeploymentPipeline(hv)
    return state.pipeline


def get_current_settings() -> HypervisorSettings:
    if state.current_settings is None:
        state.current_settings = _boot_settings()
    return state.current_settings
