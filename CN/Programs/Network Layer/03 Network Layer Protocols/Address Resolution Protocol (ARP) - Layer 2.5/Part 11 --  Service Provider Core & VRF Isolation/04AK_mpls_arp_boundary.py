"""
Core Logic: In a standard enterprise network, a packet traversing 10 routers will 
trigger an ARP resolution at every single hop (Module 04Z). If a Service Provider 
core has 500 routers, running ARP and BGP lookups at every hop for millions of 
customer IPs would melt the silicon.

Multiprotocol Label Switching (MPLS) completely changes the dataplane physics.
1. Customer Edge (CE1) sends a standard Ethernet/IP frame to the Provider Edge (PE1).
2. PE1 intercepts the frame. Instead of doing a standard IP routing lookup and ARPing 
   for the next hop toward the destination, PE1 strips the customer's Layer 2 header 
   and PUSHES a 32-bit MPLS Label (e.g., Label 50) onto the packet.
3. The packet enters the Provider (P) core. The core routers NEVER look at the IP 
   address, and they NEVER generate ARP requests for the customer's IP. They purely 
   SWAP the MPLS label (e.g., Label 50 -> Label 72) in hardware and forward it.
4. At the egress Provider Edge (PE2), the label is POPPED.
5. PE2 now looks at the exposed IP packet, ARPs for the destination Customer Edge (CE2), 
   and delivers the standard Ethernet frame.

The MPLS Core is a macro-level "ARP-less" transport zone for customer traffic.
"""

import sys
import shutil
import time
from typing import Any, Dict

class MPLSARPBoundaryEngine:
    mpls_state: Dict[str, Any]

    def __init__(self) -> None:
        self.mpls_state = {}
        
        # MPLS Topology
        self.ce1_ip = "10.0.1.10"
        self.ce2_ip = "10.0.2.10"
        
        # MAC Addresses
        self.ce1_mac = "CE:01:00:00:00:00"
        self.pe1_mac = "PE:01:00:00:00:00"
        self.pe2_mac = "PE:02:00:00:00:00"
        self.ce2_mac = "CE:02:00:00:00:00"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_mpls_forwarding(self) -> None:
        """Simulates the L2 MAC stripping and MPLS Label Switched Path (LSP)."""
        
        flow = []
        frames = []
        
        # HOP 1: CE1 to PE1 (Standard IP Routing / ARP)
        flow.append("1. [Ingress Edge]: CE1 ARPs for Default Gateway (PE1).")
        frame_1 = {
            "stage": "CE1 -> PE1 (Customer Ethernet)",
            "encap": f"[ L2 MAC: {self.ce1_mac} -> {self.pe1_mac} ] | [ L3 IP: {self.ce1_ip} -> {self.ce2_ip} ] | [ Payload ]",
            "arp_used": "YES (CE1 resolved PE1's MAC)"
        }
        frames.append(frame_1)
        
        # HOP 2: PE1 to Core P-Router (MPLS Push)
        flow.append("2. [PE1 Ingress]: Strips Customer L2 MAC Header entirely.")
        flow.append("3. [PE1 VRF]: Performs L3 VPN lookup. PUSHES MPLS Transport Label 104.")
        frame_2 = {
            "stage": "PE1 -> P-Router (MPLS Core Entry)",
            "encap": f"[ P-Link L2 ] | [ MPLS LABEL: 104 ] | [ L3 IP: {self.ce1_ip} -> {self.ce2_ip} ] | [ Payload ]",
            "arp_used": "NO (Customer IP shielded by Label)"
        }
        frames.append(frame_2)
        
        # HOP 3: Core P-Router to PE2 (MPLS Swap)
        flow.append("4. [Core P-Router]: Reads Label 104. Does NOT look at L3 IP Header.")
        flow.append("5. [Core P-Router]: SWAPS Label 104 -> Label 202. Forwards to PE2 at wire-speed.")
        frame_3 = {
            "stage": "P-Router -> PE2 (MPLS Core Exit)",
            "encap": f"[ P-Link L2 ] | [ MPLS LABEL: 202 ] | [ L3 IP: {self.ce1_ip} -> {self.ce2_ip} ] | [ Payload ]",
            "arp_used": "NO (Pure Silicon Label Switching)"
        }
        frames.append(frame_3)
        
        # HOP 4: PE2 to CE2 (MPLS Pop & Standard ARP)
        flow.append("6. [PE2 Egress]: Receives frame. POPS MPLS Label 202. Customer IP packet exposed.")
        flow.append(f"7. [PE2 VRF]: ARPs for Final Destination ({self.ce2_ip}) on the customer-facing interface.")
        frame_4 = {
            "stage": "PE2 -> CE2 (Customer Ethernet Restored)",
            "encap": f"[ L2 MAC: {self.pe2_mac} -> {self.ce2_mac} ] | [ L3 IP: {self.ce1_ip} -> {self.ce2_ip} ] | [ Payload ]",
            "arp_used": "YES (PE2 resolved CE2's MAC)"
        }
        frames.append(frame_4)

        insight = (
            "By pushing an MPLS label at the edge, the Service Provider achieves two massive victories: "
            "1) Core routers do not need to hold millions of customer routes in memory, and "
            "2) The customer's overlapping L3 IP/ARP spaces are completely isolated from the ISP's underlay transport."
        )

        self.mpls_state = {
            "flow": flow,
            "frames": frames,
            "action": "END-TO-END LABEL SWITCHED PATH (LSP) SUCCESS",
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.mpls_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AK: MPLS ARP BOUNDARY & LABEL SWITCHING ENGINE ".center(width))
        print("=" * width)
        
        print(" [i] DATAPLANE ENCAPSULATION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] WIRE ENCAPSULATION STATE (HOP-BY-HOP):")
        time.sleep(0.3)
        for frame in state['frames']:
            print(f"\n     [{frame['stage']}]")
            print(f"     Structure : {frame['encap']}")
            print(f"     Cust. ARP : {frame['arp_used']}")
            time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f"     -> Outcome          : [ {state['action']} ]")
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = MPLSARPBoundaryEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AK_MPLS_ARP_BOUNDARY INITIALIZED ".center(width))
    print(" Type 'start' to simulate the MPLS Label Switched Path, or 'quit' to exit.".center(width))
    print("=" * width)

    while True:
        try:
            cmd = input("\n[?] Command (start/quit) [Default: start] : ").strip().lower() or "start"
            if cmd in ['quit', 'exit']: sys.exit(0)
            
            engine.execute_mpls_forwarding()
            engine.render_ui()
            break  # Run once to show the path clearly
            
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()