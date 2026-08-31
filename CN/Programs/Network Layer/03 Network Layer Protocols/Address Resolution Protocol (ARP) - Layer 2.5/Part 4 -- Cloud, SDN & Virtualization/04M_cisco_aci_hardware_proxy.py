"""
Core Logic: In Cisco Application Centric Infrastructure (ACI), the Spine-Leaf fabric 
eliminates standard Spanning Tree Protocol (STP) and Layer 2 broadcast flooding entirely. 
It does this by enabling "Hardware Proxy" mode inside the Bridge Domain (BD).

In Cisco ACI:
1. Every Spine switch acts as an Oracle running COOP (Council of Oracle Protocol). 
   COOP maintains a real-time, hardware-synchronized database of every active Endpoint (EP) 
   in the fabric—mapping Endpoint MAC + IP to the specific Leaf VTEP (Tunnel Endpoint) hosting it.

2. When a host connected to Leaf-101 sends an ARP Request for a remote IP in the same Bridge Domain:
   - If ARP Flooding is disabled (Hardware Proxy mode): Leaf-101 does NOT flood the broadcast 
     to the fabric.
   - Leaf-101 encapsulates the ARP frame into an outer iVxLAN packet and sends it directly 
     to a Spine Switch (using the Spine Anycast Proxy VTEP address).
   - The Spine receives the VXLAN packet, inspects its hardware COOP database, and determines 
     which Leaf switch owns the target MAC/IP (e.g., Leaf-102).
   - The Spine rewrites the outer VXLAN destination header to Leaf-102's VTEP IP and forwards 
     it directly across the 40G/100G fabric via pure Unicast.
   - Leaf-102 decapsulates the iVxLAN frame and delivers the ARP Request strictly out of the 
     specific physical port attached to the target host.

If the target is not in the COOP database (COOP Miss), the Spine drops the packet to prevent 
fabric degradation. Broadcast storms are mathematically impossible because the physical 
Spine-Leaf fabric operates purely on Layer 3 Unicast routed paths.
"""

import sys
import shutil
import time
import ipaddress
import re
from typing import Any, Dict

class CiscoACIHardwareProxyEngine:
    aci_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.aci_state = {}

        # Simulated Spine COOP (Council of Oracle Protocol) Global Database
        self.coop_oracle_db = {
            "10.20.30.11": {
                "mac": "00:50:56:FE:00:11",
                "leaf_vtep": "10.0.0.101 (Leaf-101)",
                "port": "Eth1/10",
                "epg": "EPG_Web"
            },
            "10.20.30.12": {
                "mac": "00:50:56:FE:00:12",
                "leaf_vtep": "10.0.0.102 (Leaf-102)",
                "port": "Eth1/12",
                "epg": "EPG_App"
            },
            "10.20.30.13": {
                "mac": "00:50:56:FE:00:13",
                "leaf_vtep": "10.0.0.103 (Leaf-103)",
                "port": "Eth1/5",
                "epg": "EPG_DB"
            }
        }

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            ipaddress.IPv4Address(ip_input.strip())
            return ip_input.strip()
        except ValueError:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv4 address format.")

    def execute_aci_forwarding(self, sender_ip: str, target_ip: str, ingress_leaf: str) -> None:
        """Simulates Cisco ACI Hardware Proxy ARP forwarding via the Spine COOP database."""
        
        spine_anycast_vtep = "10.0.0.254 (Spine Anycast Proxy)"
        arp_flow = []
        action = ""
        fabric_impact = ""
        target_mac = "[UNKNOWN]"
        egress_vtep = "[UNKNOWN]"
        egress_port = "[UNKNOWN]"
        
        arp_flow.append(f"1. [Source EP ({sender_ip})]: Injects L2 ARP Broadcast (Dst: FF:FF:FF:FF:FF:FF) into {ingress_leaf}.")
        arp_flow.append(f"2. [{ingress_leaf} ASIC]: Hardware Proxy enabled on Bridge Domain. Broadcast intercepted.")
        arp_flow.append(f"3. [{ingress_leaf}]: Encapsulates payload into iVxLAN (VNID: 1500001).")
        arp_flow.append(f"4. [{ingress_leaf} -> Spine]: Forwards Unicast iVxLAN packet to {spine_anycast_vtep}.")

        if target_ip in self.coop_oracle_db:
            ep_info = self.coop_oracle_db[target_ip]
            target_mac = ep_info["mac"]
            egress_vtep = ep_info["leaf_vtep"]
            egress_port = ep_info["port"]

            arp_flow.append(f"5. [Spine COOP Oracle]: Ingress lookup on ZeroMQ database. MATCH: {target_ip} resides on {egress_vtep}.")
            arp_flow.append(f"6. [Spine Fabric]: Rewrites outer iVxLAN Dst IP to {egress_vtep}. Direct L3 Unicast forwarding.")
            arp_flow.append(f"7. [{egress_vtep}]: Decapsulates iVxLAN frame. Delivers ARP Request strictly out port {egress_port}.")
            
            action = "COOP HIT -> UNICAST SPINE PROXY ROUTED"
            fabric_impact = "0% Fabric Flooding. Packet delivered as precision Unicast across 40G/100G routed fabric."
            
            insight = (
                "Cisco ACI's Hardware Proxy decouples the physical fabric from Ethernet broadcast limits. "
                "By turning Spines into COOP Oracles that rewrite outer VXLAN headers on the fly, "
                "ACI can scale to tens of thousands of workloads in a single broadcast domain without "
                "wasting bandwidth on broadcast replication trees."
            )
        else:
            arp_flow.append(f"5. [Spine COOP Oracle]: Ingress lookup on ZeroMQ database. MISS: {target_ip} not found in fabric.")
            arp_flow.append("6. [Spine Fabric]: Drops packet at Spine ASIC boundary (Default BD Hardware Proxy behavior).")
            
            action = "COOP MISS -> SILENT DROP (Flood Suppressed)"
            fabric_impact = "Packet dropped. Eliminates silent IP scan floods and protects downstream Leaves from CPU starvation."
            
            insight = (
                "When an endpoint does not exist or has not transmitted traffic yet, COOP drops the proxy lookup. "
                "If silent hosts exist, administrators must configure 'ARP Flooding' or enable IP Gleaning "
                "on the Bridge Domain, trading off strict fabric isolation for discovery capability."
            )

        self.aci_state = {
            "sender_ip": sender_ip,
            "target_ip": target_ip,
            "ingress_leaf": ingress_leaf,
            "target_mac": target_mac,
            "egress_vtep": egress_vtep,
            "egress_port": egress_port,
            "flow": arp_flow,
            "action": action,
            "fabric_impact": fabric_impact,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.aci_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04M: CISCO ACI HARDWARE PROXY & COOP ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] ACTIVE FABRIC COOP (COUNCIL OF ORACLE PROTOCOL) DB:")
        print("     [ Endpoint IP ]    [ MAC Address ]        [ Egress Leaf VTEP ]   [ Port ]")
        for ip, data in self.coop_oracle_db.items():
            print(f"     -> {ip:<16} : {data['mac']} : {data['leaf_vtep']:<22} : {data['port']}")
        print("-" * width)
        
        print(f" [i] FABRIC PACKET TRAVERSAL (Target: {state['target_ip']}):")
        for step in state['flow']:
            time.sleep(0.3)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] ACI HARDWARE DATAPLANE OUTCOME:")
        time.sleep(0.3)
        print(f"     -> Forwarding Decision : [ {state['action']} ]")
        time.sleep(0.2)
        print(f"     -> Fabric Wire Impact  : {state['fabric_impact']}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL FABRIC INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = CiscoACIHardwareProxyEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04M_CISCO_ACI_HARDWARE_PROXY INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Cisco ACI Ingress Leaf Resolution:")
            print("    (Tip: Use 10.20.30.12 for COOP Hit on Leaf-102, or 10.20.30.99 for COOP Miss)")
            
            sip_in = input("    Source Host IPv4  [Default: 10.20.30.11]  : ").strip() or "10.20.30.11"
            if sip_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            tip_in = input("    Target Host IPv4  [Default: 10.20.30.12]  : ").strip() or "10.20.30.12"
            leaf_in = input("    Ingress Leaf Node [Default: Leaf-101]     : ").strip() or "Leaf-101"
            
            sender_ip = engine.validate_ip(sip_in, "Source IP")
            target_ip = engine.validate_ip(tip_in, "Target IP")
            
            engine.execute_aci_forwarding(sender_ip, target_ip, leaf_in)
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