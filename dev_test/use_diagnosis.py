#!/usr/bin/env python3
"""
Example usage of the diagnostic results to solve UDP discovery issues.

This script demonstrates how to use the findings from identify_problem.py
to work around network segmentation and router forwarding issues.
"""
from identify_problem import scan_subnet_range
from discovery_client import discover, ClientConfig
import ipaddress

def main():
    print("=" * 70)
    print("UDP DISCOVERY - WORKAROUND SOLUTIONS")
    print("=" * 70)
    print("\nBased on diagnostic results, here are workarounds:\n")
    
    # Get your network interface info
    from discovery_client.network.interfaces import get_interfaces
    
    interfaces = [iface for iface in get_interfaces() 
                  if not iface.ip.startswith("169.254") and not iface.ip.startswith("172.28")]
    
    if not interfaces:
        print("No suitable interface found")
        return
    
    main_iface = interfaces[0]
    print(f"Your network: {main_iface.ip}")
    
    # Calculate your /24 segment
    try:
        network = ipaddress.IPv4Network(f"{main_iface.ip}/24", strict=False)
        your_segment = str(network)
        print(f"Your /24 segment: {your_segment}\n")
    except:
        print("Could not determine network segment\n")
        return
    
    # Solution 1: Try standard discovery first
    print("=" * 70)
    print("SOLUTION 1: Standard Discovery (for same segment)")
    print("=" * 70)
    print("\nTrying standard UDP broadcast discovery...")
    print("(This works if server is on same /24 segment)\n")
    
    config = ClientConfig(timeout=5.0)
    servers = discover(config=config)
    
    if servers:
        print(f"✅ Found {len(servers)} server(s) using standard discovery:")
        for server in servers:
            print(f"   - {server.ip}:{server.port}")
        return
    else:
        print("❌ No servers found with standard discovery")
        print("   → Server may be on different network segment")
        print("   → Trying subnet scanning...\n")
    
    # Solution 2: Scan your /24 segment
    print("=" * 70)
    print("SOLUTION 2: Scan Your Network Segment")
    print("=" * 70)
    print(f"\nScanning {your_segment} for servers...")
    print("(This may take a while for /24 networks - 254 addresses)\n")
    
    servers = scan_subnet_range(your_segment, port=9999, timeout=0.1)
    
    if servers:
        print(f"\n✅ Found {len(servers)} server(s) in your segment:")
        for ip, port in servers:
            print(f"   - {ip}:{port}")
        return
    else:
        print("\n❌ No servers found in your segment")
        print("   → Server may be on a different segment")
        print("   → Trying common segments...\n")
    
    # Solution 3: Scan common segments (if /18 network)
    if main_iface.ip.startswith("10.15."):
        print("=" * 70)
        print("SOLUTION 3: Scan Common Network Segments")
        print("=" * 70)
        print("\nScanning common /24 segments in 10.15.0.0/18 network...")
        print("(This will take longer - scanning multiple segments)\n")
        
        # Scan a few common segments
        common_segments = [
            "10.15.0.0/24",   # First segment
            "10.15.1.0/24",   # Second segment
            "10.15.34.0/24",  # Your segment (already scanned, but try again)
            "10.15.35.0/24",  # Adjacent segment
        ]
        
        for segment in common_segments:
            if segment == your_segment:
                continue  # Already scanned
            
            print(f"\nScanning {segment}...")
            servers = scan_subnet_range(segment, port=9999, timeout=0.1)
            if servers:
                print(f"\n✅ Found {len(servers)} server(s) in {segment}:")
                for ip, port in servers:
                    print(f"   - {ip}:{port}")
                return
        
        print("\n❌ No servers found in common segments")
        print("   → Server may be on a different segment or not running")
        print("   → Consider using direct IP connection if server IP is known")
    
    # Solution 4: Direct IP (if known)
    print("\n" + "=" * 70)
    print("SOLUTION 4: Direct IP Connection")
    print("=" * 70)
    print("\nIf you know the server's IP address, use direct connection:")
    print("\n```python")
    print("server_ip = '10.15.34.100'  # Replace with actual server IP")
    print("server_url = f'http://{server_ip}:8000'")
    print("```")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print("""
1. Verify server is running and listening on UDP port 9999
2. Check server IP address - should be on same /24 segment as client
3. If server is on different segment, use direct IP connection
4. Check Windows Firewall on both client and server
5. Contact network administrator if server must be on different segment
    """)

if __name__ == "__main__":
    main()

