#!/usr/bin/env python3
"""
Network diagnostic script to analyze why UDP discovery fails on corporate networks.
This script helps identify network configuration issues.
"""
import socket
import ipaddress
from discovery_client.network.interfaces import get_interfaces
from discovery_client.network.utils import broadcast_from_ip_and_mask

def analyze_network_config():
    """Analyze network interfaces and their broadcast capabilities."""
    print("=" * 70)
    print("NETWORK INTERFACE ANALYSIS")
    print("=" * 70)
    
    try:
        interfaces = get_interfaces()
        print(f"\nFound {len(interfaces)} active network interface(s):\n")
        
        for i, iface in enumerate(interfaces, 1):
            print(f"Interface {i}: {iface.name}")
            print(f"  IP Address:     {iface.ip}")
            print(f"  Netmask:        {iface.netmask}")
            print(f"  Broadcast:      {iface.broadcast}")
            
            # Calculate network info
            try:
                network = ipaddress.IPv4Network(f"{iface.ip}/{iface.netmask}", strict=False)
                print(f"  Network:        {network.network_address}/{network.prefixlen}")
                print(f"  Network Range:  {network.network_address} - {network.broadcast_address}")
                print(f"  Total Hosts:    {network.num_addresses:,}")
                
                # Check if this is a large subnet (potential issue)
                if network.prefixlen < 24:
                    print(f"  ⚠️  WARNING: Large subnet (/{network.prefixlen}) - broadcast may not reach all hosts")
                    print(f"     Corporate networks often segment large subnets with routers/switches")
                
            except Exception as e:
                print(f"  ⚠️  Error calculating network info: {e}")
            
            print()
        
    except Exception as e:
        print(f"❌ Error enumerating interfaces: {e}")
        return

def test_broadcast_send():
    """Test if we can send UDP broadcast packets."""
    print("=" * 70)
    print("UDP BROADCAST SEND TEST")
    print("=" * 70)
    
    interfaces = get_interfaces()
    if not interfaces:
        print("❌ No interfaces available for testing")
        return
    
    test_port = 9999
    test_message = b"DISCOVER_SERVER"
    
    for iface in interfaces:
        print(f"\nTesting interface: {iface.name} ({iface.ip})")
        print(f"  Broadcast address: {iface.broadcast}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1.0)
            
            # Try sending to interface-specific broadcast
            sock.sendto(test_message, (iface.broadcast, test_port))
            print(f"  ✅ Successfully sent broadcast to {iface.broadcast}:{test_port}")
            
            # Try sending to global broadcast
            try:
                sock.sendto(test_message, ("255.255.255.255", test_port))
                print(f"  ✅ Successfully sent broadcast to 255.255.255.255:{test_port}")
            except Exception as e:
                print(f"  ⚠️  Failed to send to 255.255.255.255: {e}")
            
            sock.close()
            
        except OSError as e:
            print(f"  ❌ Failed to send broadcast: {e}")
            print(f"     This may indicate firewall blocking or network restrictions")
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")

def test_broadcast_receive():
    """Test if we can receive UDP broadcast responses."""
    print("\n" + "=" * 70)
    print("UDP BROADCAST RECEIVE TEST")
    print("=" * 70)
    print("\nListening for UDP responses on port 9999 for 3 seconds...")
    print("(Start a test server on another machine to see if responses are received)\n")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(3.0)
        sock.bind(('', 9999))  # Bind to all interfaces
        
        print("Socket bound and listening...")
        
        try:
            data, addr = sock.recvfrom(4096)
            print(f"✅ Received response from {addr[0]}:{addr[1]}")
            print(f"   Data: {data}")
        except socket.timeout:
            print("⏱️  No responses received (timeout)")
            print("   This is normal if no server is running, but could also indicate:")
            print("   - Firewall blocking incoming UDP packets")
            print("   - Network segmentation preventing broadcast responses")
        except Exception as e:
            print(f"❌ Error receiving: {e}")
        
        sock.close()
        
    except OSError as e:
        print(f"❌ Failed to create receive socket: {e}")
        print("   This may indicate permission issues or port conflicts")

def analyze_corporate_network_issues():
    """Provide analysis of common corporate network issues."""
    print("\n" + "=" * 70)
    print("CORPORATE NETWORK ISSUE ANALYSIS")
    print("=" * 70)
    
    interfaces = get_interfaces()
    
    for iface in interfaces:
        try:
            network = ipaddress.IPv4Network(f"{iface.ip}/{iface.netmask}", strict=False)
            
            # Check for corporate network characteristics
            issues = []
            recommendations = []
            
            # Large subnet check
            if network.prefixlen < 24:
                issues.append(f"Large subnet (/{network.prefixlen}) with {network.num_addresses:,} hosts")
                recommendations.append(
                    "Large subnets are often segmented by routers/switches. "
                    "UDP broadcasts typically only reach devices in the same broadcast domain."
                )
            
            # Private IP ranges
            if network.is_private:
                if network.prefixlen <= 16:
                    issues.append("Very large private network (likely corporate)")
                    recommendations.append(
                        "Corporate networks often use VLANs and network segmentation. "
                        "Broadcast packets may be blocked by switches or routers."
                    )
            
            # 10.x.x.x networks are often corporate
            if iface.ip.startswith("10."):
                issues.append("10.x.x.x network (commonly used in corporate environments)")
                recommendations.append(
                    "Corporate networks typically have:\n"
                    "  - Firewall rules blocking UDP broadcasts\n"
                    "  - Network segmentation (VLANs, switches, routers)\n"
                    "  - Broadcast storm protection\n"
                    "  - Security policies restricting broadcast traffic"
                )
            
            if issues:
                print(f"\n🔍 Interface: {iface.name} ({iface.ip})")
                print(f"   Potential Issues:")
                for issue in issues:
                    print(f"     • {issue}")
                print(f"   Recommendations:")
                for rec in recommendations:
                    print(f"     • {rec}")
        
        except Exception as e:
            print(f"⚠️  Could not analyze {iface.name}: {e}")

def main():
    """Run all diagnostic tests."""
    print("\n" + "=" * 70)
    print("UDP DISCOVERY NETWORK DIAGNOSTIC TOOL")
    print("=" * 70)
    print("\nThis tool helps diagnose why UDP discovery works on some networks")
    print("but not others (e.g., mobile hotspot vs corporate network).\n")
    
    analyze_network_config()
    test_broadcast_send()
    test_broadcast_receive()
    analyze_corporate_network_issues()
    
    print("\n" + "=" * 70)
    print("SUMMARY & SOLUTIONS")
    print("=" * 70)
    print("""
Common reasons why UDP discovery fails on corporate networks:

1. NETWORK SEGMENTATION
   - Large subnets (/18, /16) are often segmented by routers/switches
   - Broadcast packets only reach devices in the same broadcast domain
   - Solution: Use multicast or direct IP scanning instead of broadcast

2. FIREWALL RULES
   - Corporate firewalls often block UDP broadcast traffic
   - Windows Firewall may block broadcasts on domain networks
   - Solution: Configure firewall exceptions or use allowed ports

3. BROADCAST DOMAIN LIMITATIONS
   - Switches may not forward broadcast traffic between VLANs
   - Routers do not forward broadcast traffic by default
   - Solution: Ensure server and client are on the same VLAN/subnet

4. BROADCAST STORM PROTECTION
   - Network equipment may rate-limit or block excessive broadcasts
   - Solution: Reduce broadcast frequency or use alternative discovery

RECOMMENDED SOLUTIONS:

1. Use interface-specific broadcast addresses (already implemented)
2. Try increasing timeout to account for network latency
3. Check Windows Firewall settings for UDP port 9999
4. Verify server and client are on the same network segment
5. Consider using multicast (239.255.255.250) instead of broadcast
6. For large networks, consider direct IP scanning of known ranges
7. Check with network administrator about broadcast restrictions

For testing, try:
  - Temporarily disable Windows Firewall
  - Connect both devices to the same switch (not through router)
  - Use a smaller test network first
    """)

if __name__ == "__main__":
    main()

