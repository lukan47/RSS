from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class VMPowerState(str, Enum):
    ON = "on"
    OFF = "off"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


class OSType(str, Enum):
    RHEL = "rhel"
    CENTOS = "centos"
    UBUNTU = "ubuntu"
    DEBIAN = "debian"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class HypervisorType(str, Enum):
    ESXI = "esxi"
    PROXMOX = "proxmox"


class VM(BaseModel):
    id: str
    name: str
    power_state: VMPowerState
    ip_address: Optional[str] = None
    os_type: Optional[OSType] = None
    cpu_count: int = 0
    memory_mb: int = 0
    hypervisor: HypervisorType
    guest_os: Optional[str] = None
    node: Optional[str] = None  # Proxmox node name


class Template(BaseModel):
    id: str
    name: str
    os_type: Optional[OSType] = None
    hypervisor: HypervisorType
    description: Optional[str] = None


class Network(BaseModel):
    id: str
    name: str


class VMCreateSpec(BaseModel):
    name: str
    template_id: str
    cpu_count: int = 2
    memory_mb: int = 4096
    storage_gb: int = 40
    network_id: Optional[str] = None
    hypervisor: HypervisorType = HypervisorType.ESXI
    node: Optional[str] = None  # required for Proxmox


class SSHCredentials(BaseModel):
    username: str
    password: Optional[str] = None
    private_key: Optional[str] = None  # PEM string
    port: int = 22


class DeploymentSpec(BaseModel):
    vm_create_spec: Optional[VMCreateSpec] = None
    vm_id: Optional[str] = None  # use an existing VM instead of creating
    ssh_credentials: SSHCredentials
    os_type: Optional[OSType] = None  # override auto-detect
    run_prep: bool = True
    run_perf_test: bool = True


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class LogLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class LogEntry(BaseModel):
    timestamp: datetime
    level: LogLevel
    message: str


class Deployment(BaseModel):
    id: str
    vm_id: Optional[str] = None
    vm_name: Optional[str] = None
    status: DeploymentStatus
    logs: List[LogEntry] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None


class HypervisorSettings(BaseModel):
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
    active_hypervisor: str = "esxi"
    default_ssh_user: str = "root"
    default_ssh_password: str = ""
    default_ssh_key_path: str = ""
