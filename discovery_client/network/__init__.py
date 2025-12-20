"""Network utilities for UDP discovery client."""

from discovery_client.network.utils import (
    netmask_to_prefix,
    prefix_to_netmask,
    network_from_ip_and_mask,
    broadcast_from_ip_and_mask,
)
from discovery_client.network.interfaces import (
    get_interfaces,
    select_interfaces,
    InterfaceInfo,
)

__all__ = [
    'netmask_to_prefix',
    'prefix_to_netmask',
    'network_from_ip_and_mask',
    'broadcast_from_ip_and_mask',
    'get_interfaces',
    'select_interfaces',
    'InterfaceInfo',
]

