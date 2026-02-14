#!/usr/bin/env python3
"""
Sanity check script for django-udp-discovery-client.

Verifies that the installed package can perform UDP discovery on the local
network. Run after pip install (e.g. pip install django-udp-discovery-client[network]):

    python scripts/sanity_check.py

Or from the repo root when installed in editable mode:

    python scripts/sanity_check.py

Prints active interfaces with broadcast addresses, runs discovery, and shows
a table of discovered servers. If no servers are found on a segmented network
(large corporate subnet), prints a helpful explanation.
"""
from __future__ import print_function

import sys


def main():
    # Use the installed package (no path hacks)
    try:
        from discovery_client import load_config, discover
        from discovery_client.network.interfaces import get_interfaces, select_interfaces
        from discovery_client.network.socket import detect_segmented_network, get_interface_broadcast
    except ImportError as e:
        print("Error: Could not import discovery_client.", file=sys.stderr)
        print("Install the package first: pip install django-udp-discovery-client[network]", file=sys.stderr)
        print("Details:", e, file=sys.stderr)
        return 1

    config = load_config()

    # --- List active interfaces and broadcast addresses ---
    print("Network interfaces (used for discovery)")
    print("-" * 60)
    try:
        all_interfaces = get_interfaces()
        selected = select_interfaces(config)
    except ImportError as e:
        print("Warning: Could not enumerate interfaces (missing netifaces/ifaddr).")
        print("Install with: pip install django-udp-discovery-client[network]")
        print("Discovery will still be attempted but may fail or use limited interfaces.")
        all_interfaces = []
        selected = []

    selected_names = {s.name for s in selected}

    if not all_interfaces:
        print("No active IPv4 interfaces found.")
    else:
        for iface in all_interfaces:
            try:
                broadcast = get_interface_broadcast(iface)
            except ValueError:
                broadcast = "(unable to compute)"
            used = " [SELECTED]" if iface.name in selected_names else ""
            print("  {}  {} / {}  -> broadcast {} {}".format(
                iface.name, iface.ip, iface.netmask, broadcast, used
            ))

    if selected:
        print("\nBroadcast addresses used for discovery:")
        for iface in selected:
            try:
                broadcast = get_interface_broadcast(iface)
                print("  {} -> {}:{}".format(iface.name, broadcast, config.discovery_port))
            except ValueError:
                print("  {} -> (skipped, invalid broadcast)".format(iface.name))

    # --- Check for segmented network before discovery ---
    segmented_info = None
    if selected:
        segmented_info = detect_segmented_network(selected)

    # --- Run discovery ---
    print("\nRunning discovery (timeout={}s, port={})...".format(config.timeout, config.discovery_port))
    import logging
    logging.getLogger("django_udp_discovery_client").setLevel(logging.ERROR)
    results = discover(config=config)

    # --- Results table ---
    print("\nDiscovery results")
    print("-" * 60)
    if not results:
        print("  No servers found.")
        if segmented_info:
            print("\nSegmented network detected")
            print("-" * 60)
            print("  Interface: {} ({})".format(segmented_info["interface"], segmented_info["ip"]))
            print("  Network:   {} (prefix /{}, {} hosts)".format(
                segmented_info["network"],
                segmented_info["prefix"],
                segmented_info["total_hosts"],
            ))
            print("  Broadcast used:  {}".format(segmented_info["calculated_broadcast"]))
            print("  Likely /24 segment: {}".format(segmented_info["likely_broadcast_domain"]))
            print("\n  UDP broadcast only reaches the same broadcast domain (often one /24).")
            print("  If servers are on other VLANs/segments, they will not respond.")
            print("  Workarounds: run client and servers on same segment, or use direct IP.")
        else:
            print("  Tip: Ensure django-udp-discovery servers are running and listening on port {}.".format(config.discovery_port))
        return 0

    # Format: IP, Port, Response (truncate long response)
    col_ip = 18
    col_port = 8
    col_response = 44
    header = "{:<{}} {:<{}} {:<{}}".format("IP", col_ip, "Port", col_port, "Response", col_response)
    print(header)
    print("-" * len(header))
    for r in results:
        resp_str = r.raw_response.decode("utf-8", errors="replace").strip()
        if len(resp_str) > col_response:
            resp_str = resp_str[: col_response - 3] + "..."
        print("{:<{}} {:<{}} {:<{}}".format(r.ip, col_ip, r.port, col_port, resp_str, col_response))
    print("\nTotal: {} server(s)".format(len(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
