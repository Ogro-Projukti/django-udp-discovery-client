# django-udp-discovery-client

A pure Python client library for discovering `django-udp-discovery` servers on local networks using UDP broadcast. This library works as a standalone Python package and does not require Django.

## Features

- **UDP-based service discovery** - Discover `django-udp-discovery` servers on local networks
- **Multi-interface support** - Automatically discovers servers across all network interfaces
- **Pure Python library** - No Django required (works with any Python script)
- **Simple API** - Easy-to-use `discover()` and `discover_one()` functions
- **Cross-platform** - Works on Windows, Linux, and macOS
- **Configurable** - Environment variable support and runtime configuration
- **Robust error handling** - Graceful failure with comprehensive logging

## Installation

### From PyPI (when published)

```bash
pip install django-udp-discovery-client
```

### From source

```bash
git clone https://github.com/Ogro-Projukti/django-udp-discovery-client.git
cd django-udp-discovery-client
pip install .
```

### Development installation

```bash
git clone https://github.com/Ogro-Projukti/django-udp-discovery-client.git
cd django-udp-discovery-client
pip install -e .
```

## Quick Start

### Basic Usage

```python
from discovery_client import discover, discover_one, DiscoveryResult

# Discover all servers on the local network
servers = discover()
for server in servers:
    print(f"Found server: {server.ip}:{server.port}")
    print(f"  Raw response: {server.raw_response}")

# Discover a single server (returns first found)
server = discover_one()
if server:
    print(f"Found server at {server.ip}:{server.port}")
else:
    print("No servers found")
```

### Using with django-udp-discovery

This client is designed to work with `django-udp-discovery` servers. Here's a complete example:

**1. Django Server Setup** (using django-udp-discovery)

In your Django project's `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'django_udp_discovery',
]

# django-udp-discovery configuration
DISCOVERY_PORT = 9999  # Default discovery port
DISCOVERY_MESSAGE = "DISCOVER_SERVER"  # Discovery message
DISCOVERY_RESPONSE_PREFIX = "SERVER_IP:"  # Response prefix
```

**2. Python Client Script**

Create a simple Python script to discover the Django server:

```python
#!/usr/bin/env python3
"""
Example script to discover django-udp-discovery servers.
This script works as a pure Python library - no Django required.
"""
from discovery_client import discover, discover_one, ClientConfig

# Option 1: Discover all servers
print("Discovering all servers...")
servers = discover()
print(f"Found {len(servers)} server(s):")
for server in servers:
    print(f"  - {server.ip}:{server.port}")
    server_url = f"http://{server.ip}:{server.port}"
    print(f"    URL: {server_url}")

# Option 2: Discover just one server
print("\nDiscovering single server...")
server = discover_one()
if server:
    print(f"Found server at {server.ip}:{server.port}")
    print(f"Server URL: http://{server.ip}:{server.port}")
else:
    print("No servers found")

# Option 3: Custom configuration
print("\nUsing custom configuration...")
config = ClientConfig(
    timeout=10.0,  # Wait up to 10 seconds
    discovery_port=9999,  # Discovery port
)
servers = discover(config=config)
print(f"Found {len(servers)} server(s) with custom config")
```

**3. Run the Example**

```bash
# Terminal 1: Start your Django server with django-udp-discovery
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Run the discovery client script
python discover_servers.py
```

**Note**: This client is a **pure Python library** and does not require Django. It can be used from any Python script to discover `django-udp-discovery` servers on your local network.

### DiscoveryResult

The `discover()` and `discover_one()` functions return `DiscoveryResult` objects:

```python
from discovery_client import DiscoveryResult

# DiscoveryResult fields:
result.ip            # IPv4 address (str): "192.168.1.100"
result.port           # Port number (int): 8000
result.raw_response   # Raw bytes received: b"SERVER_IP:192.168.1.100:8000"
result.extra          # Optional metadata dict (for future use)
```

### Discovery Protocol

This client implements the discovery protocol for `django-udp-discovery` servers:

- **Discovery Message**: `"DISCOVER_SERVER"` (sent via UDP broadcast)
- **Response Prefix**: `"SERVER_IP:"` (expected in server responses)
- **Response Format**: `"SERVER_IP:<ip>:<port>"` (e.g., `"SERVER_IP:192.168.1.100:8000"`)

The client sends UDP discovery requests and collects responses from servers that match the protocol.

**Multi-Interface Discovery:**
- Discovery automatically sends broadcast packets to each selected network interface
- Broadcast addresses are derived from each interface's IP and netmask
- If an interface lacks a broadcast address, it is automatically computed
- Results are deduplicated by (ip, port) to ensure each server appears only once
- Interface selection respects whitelist/blacklist configuration (see Interface Selection & Filtering)

### Interface Selection & Filtering

You can control which network interfaces are used for discovery using whitelist and blacklist filters:

```python
from discovery_client import ClientConfig, load_config
from discovery_client.network.interfaces import select_interfaces

# Whitelist: only use specific interfaces
config = ClientConfig(interfaces_whitelist=["eth0", "wlan0"])
interfaces = select_interfaces(config)
# Returns only eth0 and wlan0 interfaces

# Blacklist: exclude specific interfaces
config = ClientConfig(interfaces_blacklist=["docker0", "veth*"])
interfaces = select_interfaces(config)
# Returns all interfaces except docker0 and veth* interfaces

# Both: whitelist first, then apply blacklist
config = ClientConfig(
    interfaces_whitelist=["eth0", "eth1", "wlan0"],
    interfaces_blacklist=["eth1"]
)
interfaces = select_interfaces(config)
# Returns eth0 and wlan0 (eth1 is blacklisted even though whitelisted)
```

**Filtering Rules:**
- **Whitelist**: If set, only interfaces whose `name` is in the whitelist are included
- **Blacklist**: If set, interfaces whose `name` is in the blacklist are excluded
- **Order**: Whitelist is applied first, then blacklist
- **Matching**: Interface name matching is **case-sensitive** and **exact** (e.g., `"eth0"` ≠ `"Eth0"`)
- **No filters**: If neither whitelist nor blacklist is set, all non-loopback interfaces are returned

**Configuration via Environment Variables:**
```bash
# Comma-separated interface names
export DISCOVERY_CLIENT_INTERFACES_WHITELIST="eth0,wlan0"
export DISCOVERY_CLIENT_INTERFACES_BLACKLIST="docker0,lo"
```

### Django Integration

```python
# In your Django settings or views
from discovery_client import discover, load_config

# Discover available servers with custom timeout
config = load_config(timeout=5.0)
available_servers = discover(config=config)

# Use discovered servers
for server in available_servers:
    server_url = f"http://{server.ip}:{server.port}"
    # Use server_url in your Django application
```

## Logging

The library uses Python's standard `logging` module with the logger name `django_udp_discovery_client`. You can configure logging to see discovery operations and debug network issues.

### Basic Logging Configuration

```python
import logging

# Configure logging for discovery client
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Django Logging Configuration

Add this to your Django `settings.py` to enable discovery client logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django_udp_discovery_client': {
            'handlers': ['console'],
            'level': 'INFO',  # Use 'DEBUG' for detailed discovery logs
            'propagate': False,
        },
    },
}
```

### Log Levels

- **DEBUG**: Detailed information about socket operations, response parsing, and interface selection
- **INFO**: Discovery start/stop, servers found, and timeouts
- **WARNING**: Invalid responses, interface send failures, missing broadcast addresses
- **ERROR**: Socket errors, network failures, and unexpected exceptions

### Example Log Output

```
INFO - django_udp_discovery_client - Starting multi-interface discovery
INFO - django_udp_discovery_client - Selected 2 interface(s) for discovery
INFO - django_udp_discovery_client - Sending discovery request to 192.168.1.255:9999
INFO - django_udp_discovery_client - Parsed valid response: server at 192.168.1.100:8000
INFO - django_udp_discovery_client - Discovery complete: 1 server(s) found
```

## Requirements

- Python >= 3.8
- **Optional**: `netifaces>=0.11.0` or `ifaddr>=0.2.0` for network interface enumeration
  - Install with: `pip install django-udp-discovery-client[network]`
  - Without these, discovery will still work but interface filtering may be limited

**Note**: This client is a **pure Python library** and does **not require Django**. It can be used from any Python script to discover `django-udp-discovery` servers. Django is only required on the **server side** (when using `django-udp-discovery`).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code of Conduct

This project adheres to a code of conduct. Please be respectful and constructive in all interactions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Repository

https://github.com/Ogro-Projukti/django-udp-discovery-client
