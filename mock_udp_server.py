#!/usr/bin/env python3
"""
Mock UDP Discovery Server for Testing

This script creates a UDP server that responds to discovery requests.
Useful for testing the discovery client once it's implemented.

Usage:
    python mock_udp_server.py [--port PORT] [--response RESPONSE]

Example:
    python mock_udp_server.py --port 9999 --response "SERVER_IP:192.168.1.100:8000"
"""

import socket
import argparse
import sys
from typing import Optional


def create_mock_server(
    port: int = 9999,
    discovery_message: bytes = b"DISCOVER_SERVER",
    response_prefix: bytes = b"SERVER_IP:",
    server_ip: str = "192.168.1.100",
    server_port: int = 8000,
    timeout: float = 1.0
):
    """
    Create a UDP server that responds to discovery requests.
    
    Args:
        port: UDP port to listen on
        discovery_message: Message that triggers a response
        response_prefix: Prefix for the response message
        server_ip: IP address to include in response
        server_port: Port to include in response
        timeout: Socket timeout in seconds
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Enable socket reuse and broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        sock.bind(('', port))
        sock.settimeout(timeout)
        
        print(f"Mock UDP Discovery Server")
        print(f"=" * 50)
        print(f"Listening on port: {port}")
        print(f"Discovery message: {discovery_message}")
        print(f"Response format: {response_prefix.decode()}{server_ip}:{server_port}")
        print(f"Press Ctrl+C to stop")
        print(f"=" * 50)
        
        request_count = 0
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                request_count += 1
                
                print(f"\n[{request_count}] Received from {addr[0]}:{addr[1]}")
                print(f"    Data: {data}")
                
                if data == discovery_message:
                    response = f"{response_prefix.decode()}{server_ip}:{server_port}".encode()
                    sock.sendto(response, addr)
                    print(f"    ✓ Sent response: {response}")
                else:
                    print(f"    ⚠ Unknown message, ignoring")
                    
            except socket.timeout:
                # Timeout is expected, just continue
                continue
            except KeyboardInterrupt:
                print(f"\n\nShutting down...")
                print(f"Total requests handled: {request_count}")
                break
            except Exception as e:
                print(f"\n✗ Error: {e}")
                break
                
    except OSError as e:
        print(f"✗ Failed to bind to port {port}: {e}")
        print(f"  Port may be in use or requires elevated permissions")
        sys.exit(1)
    finally:
        sock.close()
        print("Server closed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Mock UDP Discovery Server for testing discovery client"
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9999,
        help='UDP port to listen on (default: 9999)'
    )
    parser.add_argument(
        '--discovery-message',
        type=str,
        default="DISCOVER_SERVER",
        help='Message that triggers response (default: DISCOVER_SERVER)'
    )
    parser.add_argument(
        '--response-prefix',
        type=str,
        default="SERVER_IP:",
        help='Prefix for response message (default: SERVER_IP:)'
    )
    parser.add_argument(
        '--server-ip',
        type=str,
        default="192.168.1.100",
        help='IP address to include in response (default: 192.168.1.100)'
    )
    parser.add_argument(
        '--server-port',
        type=int,
        default=8000,
        help='Port to include in response (default: 8000)'
    )
    
    args = parser.parse_args()
    
    create_mock_server(
        port=args.port,
        discovery_message=args.discovery_message.encode(),
        response_prefix=args.response_prefix.encode(),
        server_ip=args.server_ip,
        server_port=args.server_port
    )


if __name__ == "__main__":
    main()
