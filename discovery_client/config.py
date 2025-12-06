"""
Configuration module for UDP discovery client.

Provides ClientConfig dataclass with defaults, runtime overrides, and
environment variable support.
"""
import os
from dataclasses import dataclass, field
from typing import Optional, List, Union


def _normalize_to_bytes(value: Union[str, bytes]) -> bytes:
    """Convert string or bytes to bytes."""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode('utf-8')
    raise TypeError(f"Expected str or bytes, got {type(value).__name__}")


def _parse_bool(value: str) -> bool:
    """Parse boolean from environment variable string."""
    return value.lower() in ('true', '1', 'yes', 'on')


def _parse_list(value: str) -> List[str]:
    """Parse comma-separated list from environment variable string."""
    if not value.strip():
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


@dataclass
class ClientConfig:
    """
    Configuration for UDP discovery client.
    
    Supports defaults, runtime overrides via kwargs, and environment variable
    overrides. Environment variables use the prefix 'DISCOVERY_CLIENT_'.
    
    Attributes:
        discovery_port: UDP port for discovery (default: 9999)
        discovery_message: Message to send for discovery (default: "DISCOVER_SERVER")
        response_prefix: Expected prefix in server responses (default: "SERVER_IP:")
        timeout: Timeout in seconds for discovery operations (default: 5.0)
        retries: Number of retry attempts (default: 3)
        enable_subnet_scan: Whether to scan entire subnet (default: True)
        interfaces_whitelist: Optional list of network interfaces to use
        interfaces_blacklist: Optional list of network interfaces to exclude
    """
    discovery_port: int = 9999
    discovery_message: bytes = field(default_factory=lambda: b"DISCOVER_SERVER")
    response_prefix: bytes = field(default_factory=lambda: b"SERVER_IP:")
    timeout: float = 5.0
    retries: int = 3
    enable_subnet_scan: bool = True
    interfaces_whitelist: Optional[List[str]] = None
    interfaces_blacklist: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate and normalize configuration values."""
        # Validate port range
        if not (1 <= self.discovery_port <= 65535):
            raise ValueError(
                f"discovery_port must be between 1 and 65535, got {self.discovery_port}"
            )
        
        # Normalize message and prefix to bytes
        if isinstance(self.discovery_message, (str, bytes)):
            self.discovery_message = _normalize_to_bytes(self.discovery_message)
        else:
            raise TypeError(
                f"discovery_message must be str or bytes, got {type(self.discovery_message).__name__}"
            )
        
        if isinstance(self.response_prefix, (str, bytes)):
            self.response_prefix = _normalize_to_bytes(self.response_prefix)
        else:
            raise TypeError(
                f"response_prefix must be str or bytes, got {type(self.response_prefix).__name__}"
            )
        
        # Validate timeout
        if self.timeout <= 0:
            raise ValueError(f"timeout must be positive, got {self.timeout}")
        
        # Validate retries
        if self.retries < 0:
            raise ValueError(f"retries must be non-negative, got {self.retries}")
    
    @classmethod
    def from_env(cls, **overrides) -> 'ClientConfig':
        """
        Create ClientConfig from environment variables with optional overrides.
        
        Environment variables (all optional):
            DISCOVERY_CLIENT_PORT: Discovery port (int)
            DISCOVERY_CLIENT_MESSAGE: Discovery message (str/bytes)
            DISCOVERY_CLIENT_RESPONSE_PREFIX: Response prefix (str/bytes)
            DISCOVERY_CLIENT_TIMEOUT: Timeout in seconds (float)
            DISCOVERY_CLIENT_RETRIES: Number of retries (int)
            DISCOVERY_CLIENT_ENABLE_SUBNET_SCAN: Enable subnet scan (bool)
            DISCOVERY_CLIENT_INTERFACES_WHITELIST: Comma-separated interface names
            DISCOVERY_CLIENT_INTERFACES_BLACKLIST: Comma-separated interface names
        
        Args:
            **overrides: Runtime overrides that take precedence over env vars
        
        Returns:
            ClientConfig instance
        """
        env_prefix = "DISCOVERY_CLIENT_"
        
        # Build config dict from environment variables
        config_dict = {}
        
        # Port
        if 'discovery_port' not in overrides:
            port_str = os.environ.get(f"{env_prefix}PORT")
            if port_str:
                try:
                    config_dict['discovery_port'] = int(port_str)
                except ValueError:
                    raise ValueError(f"Invalid port value: {port_str}")
        
        # Message
        if 'discovery_message' not in overrides:
            message = os.environ.get(f"{env_prefix}MESSAGE")
            if message:
                config_dict['discovery_message'] = message
        
        # Response prefix
        if 'response_prefix' not in overrides:
            prefix = os.environ.get(f"{env_prefix}RESPONSE_PREFIX")
            if prefix:
                config_dict['response_prefix'] = prefix
        
        # Timeout
        if 'timeout' not in overrides:
            timeout_str = os.environ.get(f"{env_prefix}TIMEOUT")
            if timeout_str:
                try:
                    config_dict['timeout'] = float(timeout_str)
                except ValueError:
                    raise ValueError(f"Invalid timeout value: {timeout_str}")
        
        # Retries
        if 'retries' not in overrides:
            retries_str = os.environ.get(f"{env_prefix}RETRIES")
            if retries_str:
                try:
                    config_dict['retries'] = int(retries_str)
                except ValueError:
                    raise ValueError(f"Invalid retries value: {retries_str}")
        
        # Enable subnet scan
        if 'enable_subnet_scan' not in overrides:
            subnet_scan = os.environ.get(f"{env_prefix}ENABLE_SUBNET_SCAN")
            if subnet_scan:
                config_dict['enable_subnet_scan'] = _parse_bool(subnet_scan)
        
        # Interfaces whitelist
        if 'interfaces_whitelist' not in overrides:
            whitelist = os.environ.get(f"{env_prefix}INTERFACES_WHITELIST")
            if whitelist:
                config_dict['interfaces_whitelist'] = _parse_list(whitelist)
        
        # Interfaces blacklist
        if 'interfaces_blacklist' not in overrides:
            blacklist = os.environ.get(f"{env_prefix}INTERFACES_BLACKLIST")
            if blacklist:
                config_dict['interfaces_blacklist'] = _parse_list(blacklist)
        
        # Merge env vars with overrides (overrides take precedence)
        config_dict.update(overrides)
        
        return cls(**config_dict)


def load_config(**kwargs) -> ClientConfig:
    """
    Load and validate ClientConfig with optional overrides.
    
    This function creates a ClientConfig instance, reading defaults from
    environment variables (if set) and applying any runtime overrides.
    
    Args:
        **kwargs: Runtime overrides that take precedence over env vars and defaults
        
    Returns:
        Validated ClientConfig instance
        
    Example:
        >>> config = load_config(timeout=10.0, discovery_port=8888)
        >>> config = load_config()  # Uses defaults and env vars only
    """
    return ClientConfig.from_env(**kwargs)

