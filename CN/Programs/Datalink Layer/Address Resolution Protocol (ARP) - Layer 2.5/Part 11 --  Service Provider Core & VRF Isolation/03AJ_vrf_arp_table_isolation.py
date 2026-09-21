"""
Core Logic: In a standard enterprise router, there is only one Global Routing Table 
and one Global ARP Table. If you try to assign the IP 10.1.1.50 to two different 
MAC addresses on different interfaces, the router will crash or thrash, as IP 
addresses must be unique across the global table.

Service Providers (ISPs) host hundreds of different corporate customers (Tenants). 
Because of IPv4 exhaustion, every Tenant uses the exact same RFC 1918 private IP 
space internally (e.g., 10.0.0.0/8). 

If Tenant A and Tenant B both connect their branch offices to the same ISP router, 
their IP spaces will collide.

Virtual Routing and Forwarding (VRF) solves this by slicing the physical router 
into multiple, mathematically isolated virtual routers. 
1. The physical interface facing Tenant A is assigned to "VRF_A".
2. The physical interface facing Tenant B is assigned to "VRF_B".
3. The router maintains a completely independent ARP table for each VRF.
4. Tenant A's 10.1.1.50 safely maps to MAC_A, while Tenant B's 10.1.1.50 safely 
   maps to MAC_B. The hardware ASIC handles the overlapping IP spaces without collision.
"""

import sys
import shutil
import time
from typing import Any, Dict

class VRFARPTableIsolationEngine:
    vrf_state: Dict[str, Any]

    def __init__(self) -> None:
        self.vrf_state = {}
        
        # Interface to VRF Bindings
        self.interface_bindings = {
            "TenGigE0/0/1": "VRF_TENANT_A",
            "TenGigE0/0/2": "VRF_TENANT_B"
        }
        
        # Isolated ARP Tables in Memory
        self.arp_tables = {
            "GLOBAL": {},
            "VRF_TENANT_A": {},
            "VRF_TENANT_B": {}
        }
        
        # Simulated Network Topology (Overlapping IP spaces)
        self.tenant_a_host = {"ip": "10.1.1.50", "mac": "AA:AA:AA:11:11:11", "port": "TenGigE0/0/1"}
        self.tenant_b_host = {"ip": "10.1.1.50", "mac": "BB:BB:BB:22:22:22", "port": "TenGigE0/0/2"}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_vrf_physics(self, query_ip: str, ingress_port: str) -> None:
        """Simulates how the router isolates ARP learning and resolution per VRF."""
        
        flow = []
        
        # Phase 1: ARP Learning (Simulating router receiving ARP replies)
        flow.append("1. [Control Plane]: Router receives ARP Reply on TenGigE0/0/1.")
        flow.append(f"   -> Binding 10.1.1.50 to {self.tenant_a_host['mac']} in VRF_TENANT_A.")
        self.arp_tables["VRF_TENANT_A"]["10.1.1.50"] = self.tenant_a_host["mac"]
        
        flow.append("2. [Control Plane]: Router receives ARP Reply on TenGigE0/0/2.")
        flow.append(f"   -> Binding 10.1.1.50 to {self.tenant_b_host['mac']} in VRF_TENANT_B.")
        self.arp_tables["VRF_TENANT_B"]["10.1.1.50"] = self.tenant_b_host["mac"]
        
        flow.append("3. [ASIC Logic]: Overlapping IP 10.1.1.50 successfully mapped without collision.")
        
        # Phase 2: Forwarding Decision
        flow.append(f"\n4. [Dataplane Ingress]: Packet arrives on {ingress_port} destined for {query_ip}.")
        
        if ingress_port not in self.interface_bindings:
            flow.append("5. [ASIC Logic]: Interface not bound to a VRF. Dropping to Global Table.")
            action = "DROPPED (Global Table Miss)"
            resolved_mac = "NONE"
            insight = "If an interface isn't bound to a VRF, it uses the Global Routing Table. Since we isolated the tenants, the global table has no idea how to reach 10.1.1.50."
        else:
            vrf = self.interface_bindings[ingress_port]
            flow.append(f"5. [Port Security]: Interface {ingress_port} belongs to {vrf}.")
            flow.append(f"6. [ASIC Lookup]: Querying {vrf} ARP Table for {query_ip}.")
            
            if query_ip in self.arp_tables[vrf]:
                resolved_mac = self.arp_tables[vrf][query_ip]
                flow.append(f"7. [ASIC Lookup]: MATCH FOUND -> {resolved_mac}.")
                flow.append(f"8. [Dataplane Egress]: Rewriting L2 MAC and forwarding frame.")
                action = f"FORWARDED (Via {vrf})"
                insight = "The router uses the physical ingress interface to establish the VRF context. This mathematical boundary ensures Tenant A cannot accidentally route into Tenant B's network, even though they use the exact same IP subnets."
            else:
                resolved_mac = "NONE"
                action = "DROPPED (VRF ARP Miss)"
                insight = f"Target IP not found within the isolated {vrf} domain."

        self.vrf_state = {
            "ingress_port": ingress_port,
            "target_ip": query_ip,
            "flow": flow,
            "action": action,
            "resolved_mac": resolved_mac,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.vrf_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AJ: VRF ARP TABLE ISOLATION ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] HARDWARE VRF ARP TABLES:")
        for vrf_name, table in self.arp_tables.items():
            print(f"     -> {vrf_name:<16} : {table}")
        print("-" * width)
        
        print(" [i] DATAPLANE FORWARDING SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] FORWARDING OUTCOME:")
        time.sleep(0.3)
        print(f"     -> Action           : [ {state['action']} ]")
        print(f"     -> Dest MAC Written : {state['resolved_mac']}")
        
        print("\n" + "-" * width)
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = VRFARPTableIsolationEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AJ_VRF_ARP_TABLE_ISOLATION INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Ingress Traffic to Overlapping IP (10.1.1.50):")
            print("    1. Packet arrives from Tenant A (TenGigE0/0/1)")
            print("    2. Packet arrives from Tenant B (TenGigE0/0/2)")
            print("    3. Packet arrives from Global Internet (GigE0/0/0)")
            
            choice = input("    Select ingress interface (1/2/3) [Default: 1] : ").strip() or "1"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice == "1":
                ingress_port = "TenGigE0/0/1"
            elif choice == "2":
                ingress_port = "TenGigE0/0/2"
            elif choice == "3":
                ingress_port = "GigE0/0/0"
            else:
                raise ValueError("Selection Error: Please choose 1, 2, or 3.")
            
            target_ip = "10.1.1.50"
            
            engine.execute_vrf_physics(target_ip, ingress_port)
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