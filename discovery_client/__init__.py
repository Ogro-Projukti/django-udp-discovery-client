__version__ = "0.0.0"

from discovery_client.config import ClientConfig, load_config
from discovery_client.results import DiscoveryResult
from typing import List, Optional

__all__ = [
    'ClientConfig',
    'load_config',
    'DiscoveryResult',
    'discover',
    'discover_one',
]


def discover(config: Optional[ClientConfig] = None) -> List[DiscoveryResult]:
    """
    Discover django-udp-discovery servers on the local network.
    
    Sends UDP discovery requests (DISCOVER_SERVER) to the network and collects
    responses from servers that respond with the SERVER_IP: prefix.
    
    This function implements the discovery protocol for django-udp-discovery servers:
    - Sends "DISCOVER_SERVER" message via UDP broadcast/multicast
    - Listens for responses starting with "SERVER_IP:" prefix
    - Parses server IP and port from responses
    - Returns a list of discovered servers
    
    Args:
        config: Optional ClientConfig instance. If None, uses default configuration
                loaded from environment variables or defaults.
    
    Returns:
        List of DiscoveryResult objects, one for each discovered server.
        Returns empty list if no servers are found or if discovery times out.
    
    Raises:
        NotImplementedError: Network implementation not yet complete.
                              This function is currently a stub that defines the API.
        
    Example:
        >>> from discovery_client import discover, load_config
        >>> 
        >>> # Use default configuration
        >>> servers = discover()
        >>> for server in servers:
        ...     print(f"Found server: {server.ip}:{server.port}")
        ...
        >>> # Use custom configuration
        >>> config = load_config(timeout=10.0, discovery_port=8888)
        >>> servers = discover(config=config)
    
    Note:
        This function is part of the django-udp-discovery protocol:
        - Discovery message: "DISCOVER_SERVER" (configurable via ClientConfig)
        - Response prefix: "SERVER_IP:" (configurable via ClientConfig)
        - Response format: "SERVER_IP:<ip>:<port>" (expected format)
    
    Implementation Status:
        ⚠️ API defined but network implementation pending.
        Currently raises NotImplementedError. Full implementation will include:
        - UDP socket creation and configuration
        - Broadcast/multicast sending
        - Response receiving with timeout
        - Response parsing
        - Interface filtering
        - Retry logic
    """
    if config is None:
        config = load_config()
    
    # TODO: Implement network discovery logic
    # This is a stub implementation that defines the API contract
    raise NotImplementedError(
        "discover() API is defined but network implementation is not yet complete. "
        "This function will send UDP discovery requests and collect server responses."
    )


def discover_one(config: Optional[ClientConfig] = None) -> Optional[DiscoveryResult]:
    """
    Discover a single django-udp-discovery server on the local network.
    
    Convenience function that returns the first discovered server, or None if
    no servers are found. This is useful when you only need one server and want
    to avoid waiting for multiple responses.
    
    Args:
        config: Optional ClientConfig instance. If None, uses default configuration
                loaded from environment variables or defaults.
    
    Returns:
        DiscoveryResult for the first discovered server, or None if no servers
        are found or if discovery times out.
    
    Raises:
        NotImplementedError: Network implementation not yet complete.
                              This function is currently a stub that defines the API.
    
    Example:
        >>> from discovery_client import discover_one
        >>> 
        >>> server = discover_one()
        >>> if server:
        ...     print(f"Found server at {server.ip}:{server.port}")
        ... else:
        ...     print("No servers found")
    
    Note:
        This function uses the same discovery protocol as discover(), but stops
        after finding the first server. The timeout and retry behavior is the
        same as discover().
    
    Implementation Status:
        ⚠️ API defined but network implementation pending.
        Currently raises NotImplementedError. Full implementation will call
        discover() and return the first result, or None if the list is empty.
    """
    if config is None:
        config = load_config()
    
    # TODO: Implement network discovery logic
    # This is a stub implementation that defines the API contract
    # When implemented, this will call discover() and return the first result
    raise NotImplementedError(
        "discover_one() API is defined but network implementation is not yet complete. "
        "This function will return the first discovered server or None."
    )

