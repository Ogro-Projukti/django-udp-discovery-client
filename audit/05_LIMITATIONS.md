# Known Limitations Audit

## Overview

This section documents all known limitations of the current implementation, with special focus on VLAN/segmented network support, which is the primary limitation for corporate network deployments.

---

## Overall Limitations Assessment

### Critical Limitations: ⚠️
1. **VLAN/Segmented Network Support** - Only works within same broadcast domain
2. **IPv6 Support** - IPv4 only
3. **Retry Logic** - Not implemented (config exists but unused)

### Minor Limitations: ℹ️
1. **Multicast Support** - Broadcast only
2. **Async API** - Synchronous only
3. **Performance** - Sequential interface scanning

---

## 1. VLAN/Segmented Network Limitation

### 1.1 Problem Description

**Status**: ⚠️ **Critical Limitation**

**Issue**: The current implementation uses UDP broadcast discovery, which only works within the same broadcast domain (typically a /24 network segment). On large corporate networks that are segmented into multiple VLANs, servers on different network segments will not be discovered.

**Root Cause**: UDP broadcasts do not cross router boundaries. Routers do not forward broadcast traffic by default, so broadcasts are confined to the local broadcast domain.

---

### 1.2 Technical Details

#### How It Works (Current Implementation)

1. **Interface Enumeration**: Discovers all network interfaces
2. **Broadcast Calculation**: Computes broadcast address from interface IP and netmask
   - Example: `10.15.34.66/18` → Broadcast: `10.15.63.255`
3. **UDP Broadcast**: Sends `DISCOVER_SERVER` to broadcast address
4. **Response Collection**: Listens for `SERVER_IP:` responses

#### The Problem

**Example Network:**
```
Corporate Network: 10.15.0.0/18 (16,384 hosts)
├── 10.15.0.0/24   (VLAN 1 - Segment 1)
├── 10.15.1.0/24   (VLAN 2 - Segment 2)
├── 10.15.34.0/24  (VLAN 35 - Client segment) ← Client is here
├── ...
└── 10.15.63.0/24  (VLAN 64 - Segment 64)
```

**Client Location**: `10.15.34.66` (on `10.15.34.0/24`)

**What Happens:**
- Client calculates broadcast: `10.15.63.255` (for /18 network)
- Client sends broadcast to `10.15.63.255:9999`
- **Reality**: Broadcast only reaches `10.15.34.255` (actual broadcast domain)
- **Result**: Servers on `10.15.0.0/24`, `10.15.1.0/24`, etc. do NOT receive the broadcast

**Why It Works on Mobile Hotspot:**
- Mobile hotspot: `192.168.133.173/24` (254 hosts)
- Single broadcast domain - no segmentation
- All devices receive broadcasts ✅

---

### 1.3 Detection & Warnings

**Current Implementation:**

The code includes detection for segmented networks:

```python
def detect_segmented_network(interfaces: List[InterfaceInfo]) -> Optional[dict]:
    # Detects large subnets (prefix < 24) on corporate networks
    # Only warns if no servers found
```

**Detection Criteria:**
1. Network prefix < 24 (large subnet)
2. Corporate IP range (10.x.x.x or 172.16-31.x.x)
3. Broadcast domain differs from calculated broadcast

**Warning Message:**
```
WARNING: Segmented Network Detected
==========================================
Interface: MediaTek Wi-Fi 6 MT7921 Wireless LAN Card (10.15.34.66)
Network: 10.15.0.0/18 (16,384 hosts)
Calculated broadcast: 10.15.63.255
Likely broadcast domain: 10.15.34.255
Network may be segmented into 64 /24 segments (VLANs).

ISSUE: The current implementation uses UDP broadcast discovery, which only
reaches devices in the same broadcast domain (typically /24 segment).
If servers are on different network segments, they will NOT be discovered.
```

**Status**: ✅ **Good** - Detection works, but only warns after discovery fails

---

### 1.4 Impact Assessment

**Affected Scenarios:**

| Network Type | Status | Impact |
|--------------|--------|--------|
| Home Network (/24) | ✅ Works | No impact |
| Mobile Hotspot (/24) | ✅ Works | No impact |
| Small Office (/24) | ✅ Works | No impact |
| Corporate Network (/18, /16) | ⚠️ Limited | **High Impact** |
| Multi-VLAN Networks | ⚠️ Limited | **High Impact** |

**User Impact:**
- **Low Impact**: Home networks, mobile hotspots, small offices
- **High Impact**: Corporate networks, large organizations, multi-building campuses

**Workarounds:**
1. Ensure server and client are on same /24 segment
2. Use direct IP connection if server IP is known
3. Implement subnet scanning for known IP ranges (future feature)
4. Contact network administrator for broadcast permissions

---

### 1.5 Future Solution (Planned)

**Proposed Implementation:**

Combine broadcast with unicast scanning:

```python
# Future API
config = ClientConfig(
    discovery_mode="hybrid",  # broadcast + unicast
    vlan_scan=True,
    subnet_ranges=["10.15.0.0/24", "10.15.1.0/24", "10.15.34.0/24"]
)

servers = discover(config=config)
```

**Implementation Strategy:**
1. **Phase 1**: Detect segmented networks
2. **Phase 2**: Allow user to specify known subnet ranges
3. **Phase 3**: Unicast scan specified subnets
4. **Phase 4**: Combine broadcast + unicast results
5. **Phase 5**: Auto-detect and scan common subnet ranges

**Priority**: High (post-release)

---

## 2. IPv6 Support

### 2.1 Current Limitation

**Status**: ❌ **Not Supported**

**Issue**: Only IPv4 addresses are supported. IPv6 networks are not discovered.

**Impact**: 
- Low for most use cases (IPv4 still dominant)
- Medium for IPv6-only networks
- High for dual-stack environments wanting IPv6 discovery

**Current Code:**
```python
# Only processes IPv4
if ip.is_IPv4:
    # Process IPv4 interface
```

**Future Solution:**
- Add IPv6 interface enumeration
- Add IPv6 broadcast/multicast support
- Support both IPv4 and IPv6 simultaneously

**Priority**: Medium (future enhancement)

---

## 3. Retry Logic

### 3.1 Current Limitation

**Status**: ⚠️ **Config Exists but Not Used**

**Issue**: The `retries` configuration option exists in `ClientConfig` but is not implemented in the discovery logic.

**Current Code:**
```python
@dataclass
class ClientConfig:
    retries: int = 3  # Defined but not used
```

**Impact**: 
- Low - Discovery still works (single attempt)
- Medium - Network congestion may cause missed discoveries

**Recommendation:**
- Either implement retry logic or remove the config option
- Retry logic would help with transient network issues

**Priority**: Medium

---

## 4. Multicast Support

### 4.1 Current Limitation

**Status**: ❌ **Not Supported**

**Issue**: Only UDP broadcast is supported. Multicast discovery is not implemented.

**Impact**: 
- Low for most networks (broadcast works fine)
- Medium for networks where multicast is preferred
- High for networks that block broadcast but allow multicast

**Future Solution:**
```python
config = ClientConfig(
    discovery_method="multicast",  # or "broadcast", "both"
    multicast_group="239.255.255.250"
)
```

**Priority**: Low (future enhancement)

---

## 5. Async API

### 5.1 Current Limitation

**Status**: ❌ **Not Supported**

**Issue**: Only synchronous API is available. No async/await support.

**Impact**: 
- Low for most use cases
- Medium for async applications wanting non-blocking discovery

**Current API:**
```python
servers = discover()  # Blocks until timeout
```

**Future API:**
```python
servers = await discover_async()  # Non-blocking
```

**Priority**: Low (future enhancement)

---

## 6. Performance Limitations

### 6.1 Sequential Interface Scanning

**Status**: ⚠️ **Minor Limitation**

**Issue**: Interfaces are scanned sequentially, not in parallel.

**Current Implementation:**
```python
for iface in interfaces:
    send_discovery_request(...)  # Sequential
```

**Impact**: 
- Low for most use cases (few interfaces)
- Medium for systems with many network interfaces

**Future Solution:**
- Parallel interface scanning using threading or asyncio
- Concurrent socket operations

**Priority**: Low (optimization)

---

## 7. Documentation of Limitations

### 7.1 Current Documentation

**Status**: ⚠️ **Partially Documented**

**Where Documented:**
- ✅ Diagnosis files in `dev_test/` directory
- ✅ Code comments in `detect_segmented_network()`
- ⚠️ README.md - Mentioned but not prominent
- ❌ No dedicated "Known Limitations" section

**Recommendation:**
- Add prominent "Known Limitations" section to README
- Include VLAN limitation in quick start
- Add troubleshooting guide

---

## 8. Limitations Summary Table

| Limitation | Severity | Impact | Workaround | Future Plan |
|------------|----------|--------|------------|-------------|
| VLAN/Segmented Networks | ⚠️ High | Corporate networks | Same segment, direct IP | Hybrid broadcast+unicast |
| IPv6 Support | ❌ Medium | IPv6-only networks | Use IPv4 | Add IPv6 support |
| Retry Logic | ⚠️ Low | Transient failures | Manual retry | Implement retries |
| Multicast | ❌ Low | Some networks | Use broadcast | Add multicast |
| Async API | ❌ Low | Async apps | Use sync API | Add async API |
| Performance | ⚠️ Low | Many interfaces | Acceptable | Parallel scanning |

---

## 9. Recommendations

### Before Release:
1. ✅ Add "Known Limitations" section to README
2. ✅ Document VLAN limitation prominently
3. ✅ Add troubleshooting guide
4. ✅ Update CHANGELOG with limitations

### Post-Release:
1. **High Priority**: Implement VLAN/segmented network support
2. **Medium Priority**: Implement retry logic or remove config
3. **Low Priority**: Add IPv6, multicast, async API support

---

## 10. User Communication

### 10.1 Error Messages

**Current**: Warning messages are logged when segmented networks are detected.

**Recommendation**: Make warnings more actionable:
- Suggest known subnet ranges
- Provide code examples for workarounds
- Link to documentation

### 10.2 Documentation

**Recommendation**: Add clear examples:

```python
# For corporate networks with VLANs:
# Option 1: Ensure server is on same segment
# Option 2: Use direct IP (if known)
server_ip = "10.15.34.100"
server_url = f"http://{server_ip}:8000"

# Option 3: Future - subnet scanning
# config = ClientConfig(subnet_ranges=["10.15.34.0/24"])
# servers = discover(config=config)
```

---

## Conclusion

The **primary limitation** is VLAN/segmented network support, which affects corporate network deployments. This is well-understood, detected, and planned for future implementation. Other limitations are minor and don't significantly impact the core use case (LAN network discovery).

**Overall Assessment**: ✅ **Limitations are acceptable for initial release** with clear documentation and future roadmap.

