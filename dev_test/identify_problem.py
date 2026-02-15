#!/usr/bin/env python3
"""
Diagnostic script to identify the specific problem preventing UDP discovery:
1. Network segmentation (VLANs) - Large /18 subnet divided into segments
2. Router blocking - Routers don't forward broadcast traffic
3. Firewall blocking - Firewall may block UDP broadcasts

This script performs targeted tests to identify which issue is causing the failure.
"""
import socket
import ipaddress
import subprocess
import sys
import time
from typing import List, Tuple, Optional
from discovery_client.network.interfaces import get_interfaces
from discovery_client.network.utils import broadcast_from_ip_and_mask
from discovery_client.config import ClientConfig

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def test_1_firewall_outbound():
    """Test 1: Check if firewall blocks OUTBOUND UDP broadcasts."""
    print_header("TEST 1: Firewall - Outbound UDP Broadcast")
    print("Testing if firewall blocks sending UDP broadcast packets...\n")
    
    interfaces = get_interfaces()
    results = []
    
    for iface in interfaces:
        if iface.ip.startswith("169.254"):  # Skip link-local addresses
            continue
            
        print(f"Testing interface: {iface.name} ({iface.ip})")
        print(f"  Broadcast: {iface.broadcast}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.1)
            
            # Try sending broadcast
            sock.sendto(b"TEST", (iface.broadcast, 9999))
            print_success(f"Outbound broadcast sent successfully to {iface.broadcast}:9999")
            results.append(("outbound", iface.name, True, None))
            sock.close()
            
        except OSError as e:
            error_msg = str(e)
            print_error(f"Failed to send broadcast: {error_msg}")
            results.append(("outbound", iface.name, False, error_msg))
            
            if "10051" in error_msg or "unreachable" in error_msg.lower():
                print_warning("  → This suggests network unreachability, not necessarily firewall")
            elif "10013" in error_msg or "permission" in error_msg.lower():
                print_warning("  → This suggests firewall or permission issue")
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            results.append(("outbound", iface.name, False, str(e)))
    
    return results

def test_2_firewall_inbound():
    """Test 2: Check if firewall blocks INBOUND UDP responses."""
    print_header("TEST 2: Firewall - Inbound UDP Responses")
    print("Testing if firewall blocks receiving UDP responses...\n")
    print("This test requires a server to be running. If no server is available,")
    print("we'll test if the socket can bind and listen.\n")
    
    try:
        # Try to bind and listen on the discovery port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(2.0)
        
        try:
            sock.bind(('', 9999))
            print_success("Socket successfully bound to port 9999")
            print_info("Listening for responses for 2 seconds...")
            
            try:
                data, addr = sock.recvfrom(4096)
                print_success(f"Received response from {addr[0]}:{addr[1]}")
                print_info(f"  Data: {data[:50]}")
                sock.close()
                return [("inbound", "port_9999", True, "Response received")]
            except socket.timeout:
                print_warning("No responses received (timeout)")
                print_info("  → This is normal if no server is running")
                print_info("  → However, it could also indicate firewall blocking responses")
                sock.close()
                return [("inbound", "port_9999", "unknown", "No server to test")]
        except OSError as e:
            error_msg = str(e)
            print_error(f"Failed to bind to port 9999: {error_msg}")
            if "10048" in error_msg or "address already in use" in error_msg.lower():
                print_warning("  → Port is already in use (another process?)")
            elif "10013" in error_msg or "permission" in error_msg.lower():
                print_warning("  → This suggests firewall or permission issue")
            sock.close()
            return [("inbound", "port_9999", False, error_msg)]
            
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return [("inbound", "port_9999", False, str(e))]

def test_3_network_segmentation():
    """Test 3: Check if network is segmented (VLANs)."""
    print_header("TEST 3: Network Segmentation (VLANs)")
    print("Analyzing network configuration to detect segmentation...\n")
    
    interfaces = get_interfaces()
    results = []
    
    for iface in interfaces:
        if iface.ip.startswith("169.254"):  # Skip link-local
            continue
            
        print(f"Interface: {iface.name} ({iface.ip})")
        
        try:
            # Parse network
            network = ipaddress.IPv4Network(f"{iface.ip}/{iface.netmask}", strict=False)
            prefix = network.prefixlen
            total_hosts = network.num_addresses
            
            print(f"  Network: {network.network_address}/{prefix}")
            print(f"  Total hosts: {total_hosts:,}")
            print(f"  Broadcast: {iface.broadcast}")
            
            # Check for segmentation indicators
            issues = []
            is_segmented = False
            
            # Large subnet check
            if prefix < 24:
                print_warning(f"  Large subnet (/{prefix}) - likely segmented")
                issues.append(f"Large subnet (/{prefix}) with {total_hosts:,} hosts")
                is_segmented = True
                
                # Calculate potential segments
                if prefix <= 18:
                    # /18 can be divided into 64 /24 segments
                    segments = 2 ** (24 - prefix)
                    print_info(f"  → This /{prefix} network can be divided into {segments} /24 segments")
                    print_info(f"  → Broadcast to {iface.broadcast} may only reach your /24 segment")
            
            # Corporate network check
            if iface.ip.startswith("10."):
                print_warning("  10.x.x.x network - commonly segmented in corporate environments")
                issues.append("Corporate network (10.x.x.x)")
                is_segmented = True
            
            # Calculate actual broadcast domain (assume /24 for most cases)
            if prefix < 24:
                # Calculate what the actual broadcast domain likely is
                ip_obj = ipaddress.IPv4Address(iface.ip)
                network_24 = ipaddress.IPv4Network(f"{iface.ip}/24", strict=False)
                actual_broadcast = str(network_24.broadcast_address)
                
                if actual_broadcast != iface.broadcast:
                    print_warning(f"  Calculated /18 broadcast: {iface.broadcast}")
                    print_warning(f"  Actual /24 broadcast domain: {actual_broadcast}")
                    print_info(f"  → Broadcasts to {iface.broadcast} may only reach {actual_broadcast}")
                    issues.append(f"Broadcast domain mismatch: /18 vs /24")
            
            results.append({
                "interface": iface.name,
                "ip": iface.ip,
                "network": str(network),
                "prefix": prefix,
                "is_segmented": is_segmented,
                "issues": issues,
                "calculated_broadcast": iface.broadcast,
                "likely_broadcast_domain": actual_broadcast if prefix < 24 else iface.broadcast
            })
            
            print()
            
        except Exception as e:
            print_error(f"Error analyzing {iface.name}: {e}")
            results.append({
                "interface": iface.name,
                "error": str(e)
            })
    
    return results

def test_4_router_forwarding():
    """Test 4: Check if routers block broadcast forwarding."""
    print_header("TEST 4: Router Broadcast Forwarding")
    print("Testing if routers forward broadcast traffic...\n")
    print("This test requires a server on a different network segment.\n")
    print("If you know the server's IP, we can test connectivity.\n")
    
    # Get the main interface
    interfaces = [iface for iface in get_interfaces() 
                  if not iface.ip.startswith("169.254") and not iface.ip.startswith("172.28")]
    
    if not interfaces:
        print_error("No suitable interface found for testing")
        return []
    
    main_iface = interfaces[0]
    print(f"Main interface: {main_iface.name} ({main_iface.ip})")
    
    try:
        network = ipaddress.IPv4Network(f"{main_iface.ip}/{main_iface.netmask}", strict=False)
        prefix = network.prefixlen
        
        print(f"Network: {network.network_address}/{prefix}")
        print(f"Broadcast: {main_iface.broadcast}")
        
        if prefix < 24:
            # Calculate network segments
            network_24 = ipaddress.IPv4Network(f"{main_iface.ip}/24", strict=False)
            print(f"\nActual broadcast domain (likely /24): {network_24.broadcast_address}")
            print(f"Calculated /{prefix} broadcast: {main_iface.broadcast}")
            
            print_warning("\nRouter Forwarding Test:")
            print("  Routers typically DO NOT forward broadcast traffic.")
            print("  If your server is on a different /24 segment:")
            print(f"    - Server on 10.15.0.x → Won't receive broadcast from 10.15.34.x")
            print(f"    - Server on 10.15.34.x → Will receive broadcast (same segment)")
            
            # Test if we can reach other network segments
            print("\nTesting connectivity to other network segments...")
            
            # Try to ping gateway or other common IPs
            gateway = None
            try:
                # Try to get default gateway
                result = subprocess.run(
                    ["route", "print", "-4"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # Parse gateway from route output (simplified)
                for line in result.stdout.split('\n'):
                    if '0.0.0.0' in line and 'On-link' not in line:
                        parts = line.split()
                        if len(parts) > 2:
                            gateway = parts[2]
                            break
            except:
                pass
            
            if gateway:
                print_info(f"Default gateway: {gateway}")
                print_info("  → If server is beyond gateway, broadcast won't reach it")
            
            # Test ping to gateway
            if gateway:
                try:
                    result = subprocess.run(
                        ["ping", "-n", "1", "-w", "1000", gateway],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    if result.returncode == 0:
                        print_success(f"Gateway {gateway} is reachable")
                        print_warning("  → But broadcasts won't cross the gateway")
                    else:
                        print_warning(f"Gateway {gateway} is not reachable")
                except:
                    pass
        
        return [{
            "network": str(network),
            "prefix": prefix,
            "broadcast": main_iface.broadcast,
            "gateway": gateway
        }]
        
    except Exception as e:
        print_error(f"Error in router forwarding test: {e}")
        return []

def test_5_broadcast_reachability():
    """Test 5: Test actual broadcast reachability with a test server."""
    print_header("TEST 5: Broadcast Reachability Test")
    print("This test requires a test server on the network.\n")
    print("If you have a server running, we'll test if broadcasts reach it.\n")
    
    config = ClientConfig(timeout=3.0)
    interfaces = [iface for iface in get_interfaces() 
                  if not iface.ip.startswith("169.254")]
    
    results = []
    
    for iface in interfaces:
        print(f"\nTesting broadcast on: {iface.name} ({iface.ip})")
        print(f"  Sending to: {iface.broadcast}:{config.discovery_port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(3.0)
            
            # Send discovery request
            sock.sendto(config.discovery_message, (iface.broadcast, config.discovery_port))
            print_success("Discovery request sent")
            
            # Try to receive response
            try:
                data, addr = sock.recvfrom(4096)
                print_success(f"Received response from {addr[0]}:{addr[1]}")
                print_info(f"  Response: {data[:50]}")
                results.append({
                    "interface": iface.name,
                    "broadcast": iface.broadcast,
                    "received": True,
                    "responder": addr[0]
                })
            except socket.timeout:
                print_warning("No response received (timeout)")
                print_info("  → Possible causes:")
                print_info("    1. No server running on network")
                print_info("    2. Server on different network segment")
                print_info("    3. Firewall blocking responses")
                print_info("    4. Router not forwarding broadcast")
                results.append({
                    "interface": iface.name,
                    "broadcast": iface.broadcast,
                    "received": False,
                    "reason": "timeout"
                })
            
            sock.close()
            
        except Exception as e:
            print_error(f"Error: {e}")
            results.append({
                "interface": iface.name,
                "error": str(e)
            })
    
    return results

def scan_subnet_range(ip_range: str, port: int = 9999, timeout: float = 0.1) -> List[Tuple[str, int]]:
    """
    Scan a specific IP range for UDP discovery servers.
    
    Args:
        ip_range: IP range in CIDR notation (e.g., "10.15.34.0/24")
        port: UDP port to scan (default: 9999)
        timeout: Timeout per IP (default: 0.1 seconds)
    
    Returns:
        List of (ip, port) tuples for discovered servers
    """
    config = ClientConfig()
    servers = []
    
    try:
        network = ipaddress.IPv4Network(ip_range, strict=False)
        print(f"\nScanning {ip_range} ({network.num_addresses} addresses)...")
        
        for ip in network.hosts():  # Excludes network and broadcast
            ip_str = str(ip)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(timeout)
                sock.sendto(config.discovery_message, (ip_str, port))
                
                try:
                    sock.settimeout(0.5)  # Longer timeout for response
                    data, addr = sock.recvfrom(4096)
                    if data.startswith(config.response_prefix):
                        print_success(f"Found server at {ip_str}:{port}")
                        servers.append((ip_str, port))
                except socket.timeout:
                    pass
                finally:
                    sock.close()
            except Exception:
                pass
            
            # Progress indicator for large ranges
            if network.num_addresses > 100:
                if int(ip) % 50 == 0:
                    print(f"  Scanned {int(ip) - int(network.network_address)} addresses...")
        
        if not servers:
            print_warning(f"No servers found in {ip_range}")
        else:
            print_success(f"Found {len(servers)} server(s) in {ip_range}")
        
        return servers
        
    except Exception as e:
        print_error(f"Error scanning {ip_range}: {e}")
        return []


def analyze_results(firewall_outbound, firewall_inbound, segmentation, router, reachability):
    """Analyze all test results and provide diagnosis."""
    print_header("DIAGNOSIS: Root Cause Analysis")
    
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70 + "\n")
    
    # Analyze firewall
    firewall_issue = False
    print("1. FIREWALL ANALYSIS:")
    outbound_blocked = any(not r[2] for r in firewall_outbound if isinstance(r[2], bool))
    inbound_blocked = any(not r[2] for r in firewall_inbound if isinstance(r[2], bool))
    
    if outbound_blocked:
        print_error("   OUTBOUND: Firewall may be blocking UDP broadcast sends")
        firewall_issue = True
    else:
        print_success("   OUTBOUND: No firewall blocking detected")
    
    if inbound_blocked:
        print_error("   INBOUND: Firewall may be blocking UDP responses")
        firewall_issue = True
    else:
        print_warning("   INBOUND: Cannot determine (no server response)")
    
    # Analyze segmentation
    print("\n2. NETWORK SEGMENTATION ANALYSIS:")
    segmented = any(r.get("is_segmented", False) for r in segmentation)
    
    if segmented:
        print_error("   Network appears to be SEGMENTED (VLANs)")
        for r in segmentation:
            if r.get("is_segmented"):
                print_warning(f"   Interface {r['interface']}: {r['ip']}")
                for issue in r.get("issues", []):
                    print_warning(f"     - {issue}")
    else:
        print_success("   No obvious segmentation detected")
    
    # Analyze router forwarding
    print("\n3. ROUTER FORWARDING ANALYSIS:")
    if router:
        r = router[0]
        if r.get("prefix", 32) < 24:
            print_warning("   Large subnet detected - routers likely don't forward broadcasts")
            print_warning(f"   Broadcast to {r.get('broadcast')} may only reach /24 segment")
        else:
            print_success("   Small subnet - router forwarding not an issue")
    
    # Analyze reachability
    print("\n4. BROADCAST REACHABILITY:")
    if reachability:
        received = any(r.get("received", False) for r in reachability)
        if received:
            print_success("   Broadcasts ARE being received by servers")
        else:
            print_error("   Broadcasts are NOT being received")
            print_warning("   This confirms the problem exists")
    
    # Final diagnosis
    print("\n" + "=" * 70)
    print("FINAL DIAGNOSIS")
    print("=" * 70 + "\n")
    
    issues_found = []
    
    if firewall_issue:
        issues_found.append("FIREWALL BLOCKING")
        print_error("🔴 PRIMARY ISSUE: Firewall is blocking UDP traffic")
        print("   Solution: Configure Windows Firewall to allow UDP port 9999")
        print("   - Inbound and Outbound rules for UDP 9999")
    
    if segmented:
        issues_found.append("NETWORK SEGMENTATION")
        print_error("🔴 PRIMARY ISSUE: Network is segmented (VLANs)")
        print("   Solution: Ensure server is on same network segment (same /24)")
        print("   - Check server IP: should be on same /24 as client")
        print("   - If on different segment, use direct IP scanning")
    
    if router and router[0].get("prefix", 32) < 24:
        issues_found.append("ROUTER FORWARDING")
        print_error("🔴 PRIMARY ISSUE: Routers don't forward broadcast traffic")
        print("   Solution: Server must be on same broadcast domain")
        print("   - Broadcasts only reach devices on same /24 segment")
        print("   - Use direct IP connection if server is on different segment")
    
    if not issues_found:
        print_warning("⚠️  Could not definitively identify the issue")
        print("   Possible causes:")
        print("   - Server is not running")
        print("   - Server is on different network segment")
        print("   - Firewall blocking (but tests didn't detect it)")
        print("   - Network latency/timeout issues")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70 + "\n")
    
    if "FIREWALL BLOCKING" in issues_found:
        print("1. Configure Windows Firewall:")
        print("   - Open Windows Defender Firewall")
        print("   - Create Inbound Rule: UDP port 9999")
        print("   - Create Outbound Rule: UDP port 9999")
        print("   - Test with firewall temporarily disabled")
    
    if "NETWORK SEGMENTATION" in issues_found or "ROUTER FORWARDING" in issues_found:
        print("2. Verify Server Location:")
        print("   - Check server IP address (should be on same /24 as client)")
        print("   - If different segment, use direct IP scanning")
        print("   - Consider using multicast instead of broadcast")
    
    print("3. Alternative Solutions:")
    print("   - Use direct IP connection if server IP is known")
    print("   - Implement subnet scanning for known IP ranges")
    print("   - Use multicast discovery (239.255.255.250)")
    print("   - Contact network administrator for broadcast permissions")

def main():
    """Run all diagnostic tests."""
    print("\n" + "=" * 70)
    print("UDP DISCOVERY PROBLEM IDENTIFIER")
    print("=" * 70)
    print("\nThis script identifies which problem is preventing UDP discovery:")
    print("  1. Network Segmentation (VLANs)")
    print("  2. Router Broadcast Forwarding")
    print("  3. Firewall Blocking")
    print("\n")
    
    try:
        # Run all tests
        firewall_outbound = test_1_firewall_outbound()
        firewall_inbound = test_2_firewall_inbound()
        segmentation = test_3_network_segmentation()
        router = test_4_router_forwarding()
        reachability = test_5_broadcast_reachability()
        
        # Analyze results
        analyze_results(firewall_outbound, firewall_inbound, segmentation, router, reachability)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

