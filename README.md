# django-udp-discovery-client

A Django client library for discovering django-udp-discovery servers on LAN using UDP multicast/broadcast protocols.

## Features

- UDP-based service discovery on local networks
- Simple and lightweight client implementation
- Django integration ready
- Cross-platform support (Windows, Linux, macOS)

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
from discovery_client import discover

# Discover servers on the local network
servers = discover()
for server in servers:
    print(f"Found server: {server}")
```

### Django Integration

```python
# In your Django settings or views
from discovery_client import discover

# Discover available servers
available_servers = discover(timeout=5)
```

## Requirements

- Python >= 3.8
- Django (version requirements TBD)

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
