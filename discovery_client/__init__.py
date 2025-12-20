__version__ = "0.0.0"

from discovery_client.config import ClientConfig, load_config
from discovery_client.results import DiscoveryResult
from discovery_client.network.socket import discover_servers_single_broadcast
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
        OSError: If socket operations fail (currently caught and returns empty list)
        
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
        ✅ Basic single broadcast discovery implemented.
        Sends one UDP broadcast packet and collects responses until timeout.
        Future enhancements may include:
        - Multiple broadcast targets (per interface)
        - Multicast support
        - Retry logic
        - Interface filtering integration
    """
    if config is None:
        config = load_config()
    
    # Perform discovery using single broadcast
    try:
        return discover_servers_single_broadcast(config)
    except OSError as e:
        # Socket errors - return empty list (could be logged in future)
        return []


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
        ✅ Implemented as wrapper around discover().
        Returns the first discovered server or None if no servers are found.
    """
    if config is None:
        config = load_config()
    
    # Call discover() and return first result
    servers = discover(config)
    if servers:
        return servers[0]
    return None

