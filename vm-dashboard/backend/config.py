from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    esxi_host: str = ""
    esxi_user: str = ""
    esxi_password: str = ""
    esxi_verify_ssl: bool = False

    proxmox_host: str = ""
    proxmox_user: str = ""
    proxmox_password: str = ""
    proxmox_token_id: str = ""
    proxmox_token_secret: str = ""
    proxmox_verify_ssl: bool = False

    default_ssh_user: str = "root"
    default_ssh_password: str = ""
    default_ssh_key_path: str = ""

    active_hypervisor: str = "esxi"  # "esxi" | "proxmox"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
