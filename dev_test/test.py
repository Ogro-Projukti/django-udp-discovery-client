#!/usr/bin/env python3
# """
# Example script to discover django-udp-discovery servers.
# This script works as a pure Python library - no Django required.
# """
from discovery_client import discover, discover_one, ClientConfig

# # Option 1: Discover all servers
print("Discovering all servers...")
servers = discover()
print(f"Found {len(servers)} server(s):")
for server in servers:
    print(f"  - {server.ip}:{server.port}")
    server_url = f"http://{server.ip}:{server.port}"
    print(f"    URL: {server_url}")

# # Option 2: Discover just one server
print("\nDiscovering single server...")
server = discover_one()
if server:
    print(f"Found server at {server.ip}:{server.port}")
    print(f"Server URL: http://{server.ip}:{server.port}")
else:
    print("No servers found")

# Option 3: Custom configuration
# print("\nUsing custom configuration...")
# config = ClientConfig(
#     timeout=.5,  # Wait up to 10 seconds
#     discovery_port=9999,  # Discovery port
# )
# servers = discover(config=config)
# print(f"Found {len(servers)} server(s) with custom config - {servers}")