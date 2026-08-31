"""
Core Logic: In a legacy network, ARP relies on physical broadcasts (FF:FF:FF:FF:FF:FF). 
If a data center has 10,000 Virtual Machines, a single ARP broadcast forces 9,999 other 
VMs to interrupt their CPUs, process the packet, and discard it. This causes massive 
"Broadcast Storms" that cripple datacenter bandwidth.

Enterprise Software-Defined Networking (SDN) solutions like VMware NSX solve this using 
ARP Suppression. 

Because the hypervisor (ESXi) boots the VM, it already knows the VM's IP and MAC address. 
It securely sends this data to a centralized NSX Controller cluster via an API. The 
Controller pushes a global IP-MAC database down to every hypervisor's virtual switch (vSwitch).

When VM-A sends an ARP broadcast for VM-B:
1. The local vSwitch intercepts the broadcast before it ever touches the physical wire.
2. The vSwitch queries its local NSX Controller database.
3. If a match is found, the vSwitch drops the broadcast (Suppression) and instantly 
   generates a Unicast ARP Reply directly back to VM-A.

The physical datacenter network never sees a single ARP broadcast, saving massive 
amounts of CPU cycles and 10/40/100Gbps fabric bandwidth.
"""

import sys
import shutil
import time
from typing import Any, Dict

class NSXARPSuppressionEngine:
    nsx_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.nsx_state = {}
        
        # Simulated NSX Controller Distributed Database
        self.controller_db = {
            "10.50.1.10": "00:50:56:AB:CD:01",
            "10.50.1.11": "00:50:56:AB:CD:02",
            "10.50.1.12": "00:50:56:AB:CD:03",
            "10.50.1.13": "00:50:56:AB:CD:04"
        }

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_ip(self, ip_input: str) -> str:
        ip = ip_input.strip()
        parts = ip.split('.')
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            raise ValueError("Syntax Error: Must be a valid IPv4 address format (e.g., 10.50.1.10).")
        return ip

    def execute_suppression_physics(self, target_ip: str) -> None:
        """Simulates VMware NSX vSwitch intercepting and suppressing ARP."""
        
        arp_flow = []
        action = ""
        wire_status = ""
        insight = ""
        
        arp_flow.append("1. [VM-A]: Generates standard L2 ARP Broadcast (FF:FF:FF:FF:FF:FF).")
        arp_flow.append("2. [vSwitch]: Traps broadcast payload at the hypervisor kernel boundary.")
        
        if target_ip in self.controller_db:
            # Controller hit - Suppress and Proxy
            target_mac = self.controller_db[target_ip]
            arp_flow.append(f"3. [vSwitch]: Queries local NSX DB. MATCH FOUND for {target_ip} -> {target_mac}.")
            arp_flow.append("4. [vSwitch]: SUPPRESSES physical broadcast. Packet dropped from physical uplink.")
            arp_flow.append(f"5. [vSwitch]: Generates synthetic Unicast ARP Reply to VM-A on behalf of {target_ip}.")
            
            action = "ARP SUPPRESSED (Proxy Reply Injected)"
            wire_status = "0 Bytes transmitted to physical fabric. CPU interrupts saved on 9,999 VMs."
            
            insight = (
                "This is the core of modern cloud networking. By converting a reactive broadcast protocol "
                "into a proactive, API-driven database lookup, SDN eliminates the scaling limit of Layer 2 domains."
            )
        else:
            # Controller miss - Fallback to flooding
            arp_flow.append(f"3. [vSwitch]: Queries local NSX DB. NO MATCH FOUND for {target_ip}.")
            arp_flow.append("4. [vSwitch]: Fallback triggered. Encapsulates broadcast into Geneve/VXLAN tunnel.")
            arp_flow.append("5. [Physical]: Floods encapsulated broadcast across the physical spine-leaf fabric.")
            
            action = "ARP FLOODED (BUM Traffic Replication)"
            wire_status = "Broadcast hits physical fabric. Wasting bandwidth and CPU cycles across the datacenter."
            
            insight = (
                "If an IP isn't in the NSX Controller (e.g., a physical bare-metal server, or a rogue device), "
                "SDN must fall back to legacy flooding. This BUM (Broadcast, Unknown Unicast, Multicast) traffic "
                "is exactly what network architects try to minimize."
            )

        self.nsx_state = {
            "target_ip": target_ip,
            "flow": arp_flow,
            "action": action,
            "wire_status": wire_status,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.nsx_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04K: VMWARE NSX ARP SUPPRESSION ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] DISTRIBUTED CONTROLLER DATABASE:")
        print("     [ IP Address ]      [ MAC Address ]")
        for ip, mac in self.controller_db.items():
            print(f"     -> {ip:<15} : {mac}")
        print("-" * width)
        
        print(f" [i] HYPERVISOR ARP INTERCEPTION (Target: {state['target_ip']}):")
        for step in state['flow']:
            time.sleep(0.3)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] FABRIC BANDWIDTH PHYSICS:")
        time.sleep(0.3)
        print(f"     -> SDN Action       : [ {state['action']} ]")
        time.sleep(0.2)
        print(f"     -> Wire Impact      : {state['wire_status']}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL CLOUD INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = NSXARPSuppressionEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04K_VMWARE_NSX_ARP_SUPPRESSION INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate VM generating an ARP Request:")
            print("    (Tip: Use 10.50.1.11 to see SDN Suppression, or 10.50.9.99 to see Fabric Flooding)")
            ip_in = input("    Target IPv4 to resolve [Default: 10.50.1.11] : ").strip() or "10.50.1.11"
            
            if ip_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            target_ip = engine.validate_ip(ip_in)
            
            engine.execute_suppression_physics(target_ip)
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