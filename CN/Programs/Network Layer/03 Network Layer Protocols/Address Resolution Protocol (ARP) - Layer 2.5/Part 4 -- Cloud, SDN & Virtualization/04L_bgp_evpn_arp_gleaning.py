"""
Core Logic: In a modern datacenter, scaling Layer 2 networks across thousands of racks 
using VXLAN requires a control plane to prevent catastrophic broadcast storms. BGP EVPN 
(Ethernet Virtual Private Network) is the industry standard for this.

Instead of flooding an ARP Request across the entire VXLAN fabric, the local Top-of-Rack 
(Leaf) switch actively "snoops" or "gleans" the ARP packet sent by a newly booted server. 

When a server sends a Gratuitous ARP or standard ARP Request:
1. The local Leaf switch (VTEP) intercepts the payload.
2. It extracts the Sender Hardware Address (MAC) and Sender Protocol Address (IP).
3. It packages this binding into a BGP EVPN Route Type 2 (MAC/IP Advertisement).
4. It sends this BGP Update to the Spine switches, which reflect it to all other Leafs.

Because every Leaf switch now has a BGP routing table containing every MAC and IP in the 
fabric, when a server ARPs for a remote IP, the local Leaf can answer immediately (ARP 
Suppression/Proxy) or route directly. ARP is transformed from a noisy Layer 2 broadcast 
into a silent, scalable Layer 3 BGP routing update.
"""

import sys
import shutil
import time
import re
import ipaddress
from typing import Any, Dict

class BGPEVPNARPGleaningEngine:
    evpn_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.evpn_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            ipaddress.IPv4Address(ip_input.strip())
            return ip_input.strip()
        except ValueError:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv4 address.")

    def validate_mac(self, mac_input: str, name: str) -> str:
        cleaned = re.sub(r'[:\-\.\s]', '', mac_input).upper()
        if len(cleaned) != 12 or not all(c in '0123456789ABCDEF' for c in cleaned):
            raise ValueError(f"Syntax Error: Invalid MAC format for {name}. Expected 12 hex chars.")
        return ":".join([cleaned[i:i+2] for i in range(0, 12, 2)])
        
    def validate_vni(self, vni_input: str) -> str:
        try:
            val = int(vni_input)
            if not (1 <= val <= 16777215): # 24-bit VXLAN ID
                raise ValueError()
            return str(val)
        except ValueError:
            raise ValueError("Bounds Error: VNI must be a 24-bit integer (1 to 16777215).")

    def execute_evpn_gleaning(self, host_ip: str, host_mac: str, vni: str, leaf_ip: str) -> None:
        """Simulates the VXLAN VTEP extracting ARP data and generating a BGP Type 2 Update."""
        
        # Simulated Network Physics
        route_distinguisher = f"{leaf_ip}:{vni}"
        route_target = f"target:65000:{vni}"
        esi = "00:00:00:00:00:00:00:00:00:00" # Ethernet Segment Identifier (Single-homed)
        
        arp_flow = []
        arp_flow.append(f"1. [Host]: Boots up and transmits ARP Broadcast (SPA: {host_ip}, SHA: {host_mac}).")
        arp_flow.append("2. [Leaf-1 VTEP]: Intercepts the ARP payload on the physical ingress port.")
        arp_flow.append("3. [Leaf-1 VTEP]: 'Gleans' the IP-to-MAC binding and updates local hardware CAM/ARP tables.")
        arp_flow.append("4. [Leaf-1 Control Plane]: Triggers BGP EVPN Route Type 2 generation.")
        
        # Constructing the BGP NLRI (Network Layer Reachability Information)
        bgp_nlri = {
            "Route Type": "2 (MAC/IP Advertisement)",
            "Route Distinguisher": route_distinguisher,
            "ESI": esi,
            "Ethernet Tag ID": "0",
            "MAC Address Length": "48",
            "MAC Address": host_mac,
            "IP Address Length": "32",
            "IP Address": host_ip,
            "MPLS Label 1 (L2 VNI)": vni
        }
        
        arp_flow.append(f"5. [Spine Fabric]: BGP Route Reflector distributes this NLRI to all other Leaf switches.")

        insight = (
            "By translating raw ARP broadcasts into structured BGP routing updates, EVPN completely "
            "decouples the control plane from the data plane. If a virtual machine live-migrates (vMotion) "
            "to a new rack, it sends a Gratuitous ARP. The new Leaf gleans it, sends a BGP update with a "
            "higher sequence number, and the entire datacenter fabric instantly repoints traffic to the new rack."
        )

        self.evpn_state = {
            "host_ip": host_ip,
            "host_mac": host_mac,
            "vni": vni,
            "rd": route_distinguisher,
            "rt": route_target,
            "flow": arp_flow,
            "nlri": bgp_nlri,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.evpn_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04L: BGP EVPN ARP GLEANING ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] DATACENTER VTEP CONFIGURATION:")
        print(f"     -> VXLAN Network ID (VNI) : {state['vni']}")
        print(f"     -> Route Distinguisher    : {state['rd']}")
        print(f"     -> Route Target (Export)  : {state['rt']}")
        print("-" * width)
        
        print(" [i] ARP INTERCEPTION & GLEANING SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.3)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] BGP EVPN NLRI PAYLOAD (TYPE 2 ROUTE):")
        time.sleep(0.4)
        for key, value in state['nlri'].items():
            print(f"     -> {key:<22} : {value}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL FABRIC INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = BGPEVPNARPGleaningEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04L_BGP_EVPN_ARP_GLEANING INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Bare-Metal Server Booting in Rack 1:")
            
            ip_in = input("    Host IPv4 Address [Default: 10.10.10.50]   : ").strip() or "10.10.10.50"
            if ip_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            mac_in = input("    Host MAC Address  [Default: AA:BB:CC:11:22:33] : ").strip() or "AA:BB:CC:11:22:33"
            vni_in = input("    Layer 2 VNI Segment [Default: 50100]       : ").strip() or "50100"
            leaf_ip = input("    Leaf Switch Loopback IP [Default: 1.1.1.1] : ").strip() or "1.1.1.1"
            
            host_ip = engine.validate_ip(ip_in, "Host IP")
            host_mac = engine.validate_mac(mac_in, "Host MAC")
            vni = engine.validate_vni(vni_in)
            leaf_ip_clean = engine.validate_ip(leaf_ip, "Leaf IP")
            
            engine.execute_evpn_gleaning(host_ip, host_mac, vni, leaf_ip_clean)
            engine.render_ui()
            
        except ValueError as ve:
            print(f"\n[X] INTERCEPT TRIGGERED:\n    {ve}")
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()