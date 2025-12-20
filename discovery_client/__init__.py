__version__ = "0.1.0"

import logging
from discovery_client.config import ClientConfig, load_config
from discovery_client.results import DiscoveryResult
from discovery_client.network.socket import (
    discover_servers_single_broadcast,
    discover_servers_multi_interface,
)
from typing import List, Optional

# Module-level logger
logger = logging.getLogger("django_udp_discovery_client")

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
    - Selects network interfaces based on config (whitelist/blacklist)
    - Sends "DISCOVER_SERVER" message via UDP broadcast to each interface's broadcast address
    - Listens for responses starting with "SERVER_IP:" prefix
    - Parses server IP and port from responses
    - Deduplicates results by (ip, port) to avoid duplicate entries
    - Returns a list of unique discovered servers
    
    Multi-Interface Behavior:
    - Discovery sends broadcast packets to each selected interface's broadcast address
    - Broadcast addresses are derived from each interface's IP and netmask
    - If an interface lacks a broadcast address, it is computed using the interface's
      IP and netmask
    - All responses are collected on a single socket and deduplicated before returning
    
    Args:
        config: Optional ClientConfig instance. If None, uses default configuration
                loaded from environment variables or defaults.
    
    Returns:
        List of DiscoveryResult objects, one for each discovered server.
        Returns empty list if no servers are found, if discovery times out,
        or if network errors occur. Network errors are logged but do not
        raise exceptions.
        
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
        ✅ Multi-interface broadcast discovery implemented.
        Sends UDP broadcast packets to each selected interface's broadcast address
        and collects responses. Results are deduplicated by (ip, port).
        Interface selection respects whitelist/blacklist configuration.
        Future enhancements may include:
        - Multicast support
        - Retry logic
    """
    if config is None:
        config = load_config()
    
    # Perform discovery using multi-interface broadcast
    try:
        logger.info("Starting server discovery")
        return discover_servers_multi_interface(config)
    except OSError as e:
        # Socket errors - return empty list
        logger.error(
            f"Network error during discovery: {e}. "
            "Discovery failed due to socket operation error.",
            exc_info=True
        )
        return []
    except ImportError as e:
        # Missing network libraries - return empty list
        logger.error(
            f"Missing network interface libraries: {e}. "
            "Install with: pip install django-udp-discovery-client[network]",
            exc_info=True
        )
        return []
    except Exception as e:
        # Unexpected errors - log and return empty list
        logger.error(
            f"Unexpected error during discovery: {e}",
            exc_info=True
        )
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
    logger.debug("discover_one() called - will return first server or None")
    servers = discover(config)
    if servers:
        logger.debug(f"discover_one() found server: {servers[0].ip}:{servers[0].port}")
        return servers[0]
    logger.debug("discover_one() found no servers")
    return None

