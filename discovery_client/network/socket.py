"""
Socket utilities for UDP discovery.

Provides low-level UDP socket operations for sending discovery requests
and receiving server responses.
"""
import socket
from typing import List, Tuple, Optional, Set
from discovery_client.config import ClientConfig
from discovery_client.results import DiscoveryResult
from discovery_client.network.interfaces import InterfaceInfo, select_interfaces
from discovery_client.network.utils import broadcast_from_ip_and_mask


# Default broadcast address for single broadcast discovery
DEFAULT_BROADCAST_ADDRESS = "255.255.255.255"


def parse_response(response: bytes, prefix: bytes) -> Optional[Tuple[str, int]]:
    """
    Parse a discovery response to extract IP and port.
    
    Expected format: "SERVER_IP:<ip>[:port]"
    Examples:
        - "SERVER_IP:192.168.1.100:8000" -> ("192.168.1.100", 8000)
        - "SERVER_IP:192.168.1.100" -> ("192.168.1.100", 8000)  # default port
    
    Args:
        response: Raw bytes received from server
        prefix: Expected response prefix (e.g., b"SERVER_IP:")
    
    Returns:
        Tuple of (ip, port) if parsing succeeds, None otherwise.
        Port defaults to 8000 if not specified in response.
    
    Example:
        >>> parse_response(b"SERVER_IP:192.168.1.100:8000", b"SERVER_IP:")
        ('192.168.1.100', 8000)
        >>> parse_response(b"SERVER_IP:10.0.0.5", b"SERVER_IP:")
        ('10.0.0.5', 8000)
    """
    if not response.startswith(prefix):
        return None
    
    # Extract the part after the prefix
    try:
        content = response[len(prefix):].decode('utf-8', errors='ignore').strip()
    except (UnicodeDecodeError, AttributeError):
        return None
    
    # Parse IP and optional port
    # Format: <ip>[:port]
    if ':' in content:
        parts = content.split(':', 1)
        ip_str = parts[0].strip()
        try:
            port = int(parts[1].strip())
            if not (1 <= port <= 65535):
                return None
        except (ValueError, IndexError):
            return None
    else:
        ip_str = content.strip()
        port = 8000  # Default port for django-udp-discovery
    
    # Basic IP validation
    if not ip_str:
        return None
    
    # Validate IP format (basic check - more thorough validation can be added)
    try:
        parts = ip_str.split('.')
        if len(parts) != 4:
            return None
        for part in parts:
            num = int(part)
            if not (0 <= num <= 255):
                return None
    except (ValueError, AttributeError):
        return None
    
    return (ip_str, port)


def create_discovery_socket(timeout: float) -> socket.socket:
    """
    Create and configure a UDP socket for discovery.
    
    Args:
        timeout: Socket timeout in seconds
    
    Returns:
        Configured UDP socket with broadcast enabled
    
    Raises:
        OSError: If socket creation or configuration fails
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Enable broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Set timeout
    sock.settimeout(timeout)
    
    return sock


def send_discovery_request(
    sock: socket.socket,
    message: bytes,
    port: int,
    broadcast_address: str = DEFAULT_BROADCAST_ADDRESS
) -> None:
    """
    Send a UDP discovery request to the broadcast address.
    
    Args:
        sock: UDP socket (must have SO_BROADCAST enabled)
        message: Discovery message to send (e.g., b"DISCOVER_SERVER")
        port: UDP port to send to
        broadcast_address: Broadcast address (default: "255.255.255.255")
    
    Raises:
        OSError: If send fails
    """
    sock.sendto(message, (broadcast_address, port))


def receive_responses(
    sock: socket.socket,
    config: ClientConfig,
    max_responses: Optional[int] = None
) -> List[DiscoveryResult]:
    """
    Receive and parse discovery responses until timeout.
    
    Args:
        sock: UDP socket with timeout set
        config: ClientConfig with response_prefix for parsing
        max_responses: Maximum number of responses to collect (None = unlimited)
    
    Returns:
        List of DiscoveryResult objects for valid responses
    
    Note:
        This function will continue receiving until socket timeout.
        Invalid responses (wrong prefix) are silently ignored.
    """
    results = []
    
    while True:
        try:
            # Receive response
            data, addr = sock.recvfrom(4096)  # Max UDP packet size is typically 65507
            
            # Parse response
            parsed = parse_response(data, config.response_prefix)
            if parsed is None:
                # Invalid response, ignore
                continue
            
            ip, port = parsed
            
            # Create DiscoveryResult
            try:
                result = DiscoveryResult(
                    ip=ip,
                    port=port,
                    raw_response=data,
                    extra={"source_address": addr[0]}  # Store source IP for reference
                )
                results.append(result)
                
                # Check if we've reached max responses
                if max_responses is not None and len(results) >= max_responses:
                    break
                    
            except ValueError:
                # Invalid DiscoveryResult (e.g., invalid IP/port), ignore
                continue
                
        except socket.timeout:
            # Timeout reached, stop receiving
            break
        except OSError:
            # Socket error, stop receiving
            break
    
    return results


def discover_servers_single_broadcast(
    config: ClientConfig,
    broadcast_address: str = DEFAULT_BROADCAST_ADDRESS
) -> List[DiscoveryResult]:
    """
    Perform UDP discovery using a single broadcast address.
    
    This is the core discovery function that:
    1. Creates a UDP socket with broadcast enabled
    2. Sends discovery message to broadcast address
    3. Receives and parses responses until timeout
    4. Returns list of discovered servers
    
    Args:
        config: ClientConfig with discovery settings
        broadcast_address: Broadcast address to use (default: "255.255.255.255")
    
    Returns:
        List of DiscoveryResult objects for discovered servers.
        Returns empty list if no servers respond or timeout occurs.
    
    Raises:
        OSError: If socket operations fail
    
    Example:
        >>> from discovery_client import ClientConfig
        >>> config = ClientConfig(timeout=5.0)
        >>> servers = discover_servers_single_broadcast(config)
        >>> for server in servers:
        ...     print(f"Found: {server.ip}:{server.port}")
    """
    sock = None
    try:
        # Create and configure socket
        sock = create_discovery_socket(config.timeout)
        
        # Send discovery request
        send_discovery_request(
            sock,
            config.discovery_message,
            config.discovery_port,
            broadcast_address
        )
        
        # Receive responses
        results = receive_responses(sock, config)
        
        return results
        
    finally:
        # Clean up socket
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass  # Ignore errors during cleanup


def get_interface_broadcast(iface: InterfaceInfo) -> str:
    """
    Get broadcast address for an interface.
    
    Uses the interface's broadcast address if present, otherwise computes it
    from the interface's IP and netmask.
    
    Args:
        iface: InterfaceInfo object
    
    Returns:
        Broadcast address as string
    
    Raises:
        ValueError: If broadcast cannot be computed (invalid IP/netmask)
    """
    if iface.broadcast:
        return iface.broadcast
    
    # Compute broadcast from IP and netmask
    return broadcast_from_ip_and_mask(iface.ip, iface.netmask)


def deduplicate_results(results: List[DiscoveryResult]) -> List[DiscoveryResult]:
    """
    Remove duplicate DiscoveryResult objects based on (ip, port) key.
    
    Keeps the first occurrence of each unique (ip, port) combination.
    
    Args:
        results: List of DiscoveryResult objects (may contain duplicates)
    
    Returns:
        List of unique DiscoveryResult objects (no duplicates by ip:port)
    
    Example:
        >>> results = [
        ...     DiscoveryResult(ip="192.168.1.100", port=8000, raw_response=b"response1"),
        ...     DiscoveryResult(ip="192.168.1.100", port=8000, raw_response=b"response2"),
        ...     DiscoveryResult(ip="10.0.0.5", port=9000, raw_response=b"response3"),
        ... ]
        >>> unique = deduplicate_results(results)
        >>> len(unique)
        2
    """
    seen: Set[Tuple[str, int]] = set()
    unique_results = []
    
    for result in results:
        key = (result.ip, result.port)
        if key not in seen:
            seen.add(key)
            unique_results.append(result)
    
    return unique_results


def discover_servers_multi_interface(config: ClientConfig) -> List[DiscoveryResult]:
    """
    Perform UDP discovery using multiple network interfaces.
    
    This function:
    1. Selects interfaces based on config (whitelist/blacklist)
    2. Sends discovery messages to each interface's broadcast address
    3. Receives responses from all interfaces on a single socket
    4. Deduplicates results by (ip, port)
    
    Args:
        config: ClientConfig with discovery settings and interface filters
    
    Returns:
        List of unique DiscoveryResult objects for discovered servers.
        Returns empty list if no servers respond or timeout occurs.
    
    Raises:
        OSError: If socket operations fail
        ImportError: If network interface libraries are not available
    
    Example:
        >>> from discovery_client import ClientConfig
        >>> config = ClientConfig(timeout=5.0)
        >>> servers = discover_servers_multi_interface(config)
        >>> for server in servers:
        ...     print(f"Found: {server.ip}:{server.port}")
    """
    # Select interfaces based on config
    interfaces = select_interfaces(config)
    
    if not interfaces:
        # No interfaces selected, return empty list
        return []
    
    sock = None
    try:
        # Create a single socket for receiving responses from all interfaces
        sock = create_discovery_socket(config.timeout)
        
        # Send discovery request to each interface's broadcast address
        for iface in interfaces:
            try:
                # Get broadcast address for this interface
                broadcast_addr = get_interface_broadcast(iface)
                
                # Send discovery request to this interface's broadcast
                send_discovery_request(
                    sock,
                    config.discovery_message,
                    config.discovery_port,
                    broadcast_addr
                )
            except (ValueError, OSError):
                # Skip this interface if broadcast cannot be computed or send fails
                # Continue with other interfaces
                continue
        
        # Receive responses from all interfaces
        results = receive_responses(sock, config)
        
        # Deduplicate results by (ip, port)
        unique_results = deduplicate_results(results)
        
        return unique_results
        
    finally:
        # Clean up socket
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass  # Ignore errors during cleanup
