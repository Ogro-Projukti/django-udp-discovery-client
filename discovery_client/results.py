"""
Discovery result data structures.

Defines the data model for discovered servers returned by the discovery API.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class DiscoveryResult:
    """
    Result from a successful server discovery.
    
    Represents a discovered django-udp-discovery server on the network.
    
    Attributes:
        ip: IPv4 address of the discovered server as string (e.g., "192.168.1.100")
        port: Port number of the discovered server (e.g., 8000)
        raw_response: Raw bytes received from the server in response to discovery
        extra: Optional dictionary for future metadata (default: None)
    
    Example:
        >>> result = DiscoveryResult(
        ...     ip="192.168.1.100",
        ...     port=8000,
        ...     raw_response=b"SERVER_IP:192.168.1.100:8000"
        ... )
        >>> print(f"Found server at {result.ip}:{result.port}")
        Found server at 192.168.1.100:8000
    """
    ip: str
    port: int
    raw_response: bytes
    extra: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate result fields."""
        # Validate IP format (basic check)
        if not self.ip or not isinstance(self.ip, str):
            raise ValueError(f"ip must be a non-empty string, got {type(self.ip).__name__}")
        
        # Validate port range
        if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
            raise ValueError(f"port must be an integer between 1 and 65535, got {self.port}")
        
        # Validate raw_response
        if not isinstance(self.raw_response, bytes):
            raise ValueError(f"raw_response must be bytes, got {type(self.raw_response).__name__}")
        
        # Validate extra if provided
        if self.extra is not None and not isinstance(self.extra, dict):
            raise ValueError(f"extra must be a dict or None, got {type(self.extra).__name__}")
