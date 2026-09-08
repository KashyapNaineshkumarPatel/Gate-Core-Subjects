"""
Core Logic: A fundamental GATE concept is the distinction between End-to-End delivery (IP) 
and Hop-by-Hop delivery (MAC).

When a packet travels through multiple routers:
1. The Layer 3 IP Header (Source IP, Destination IP) NEVER changes (assuming no NAT). 
   It represents the true mathematical end-to-end endpoints.
2. The Layer 2 Ethernet Header (Source MAC, Destination MAC) changes at EVERY router.

How ARP drives this:
- Host A wants to reach Host B. It ARPs for Router 1's MAC. 
  [Frame 1: Src MAC = Host A, Dst MAC = Router 1_In]
- Router 1 receives the frame, strips the L2 header, decrements the IP TTL, and checks its routing table.
- Router 1 needs to forward to Router 2. Router 1 ARPs for Router 2's MAC.
  [Frame 2: Src MAC = Router 1_Out, Dst MAC = Router 2_In]
- Router 2 receives the frame, strips the L2 header, decrements TTL, and checks its routing table.
- Router 2 realizes Host B is directly connected. Router 2 ARPs for Host B's MAC.
  [Frame 3: Src MAC = Router 2_Out, Dst MAC = Host B]
"""

import sys
import shutil
import time
from typing import Any, Dict

class HopByHopRewriteEngine:
    routing_state: Dict[str, Any]

    def __init__(self) -> None:
        self.routing_state = {}
        
        # Simulated Network Topology & ARP Tables
        self.topology = {
            "Host_A": {"ip": "10.0.1.50", "mac": "AA:AA:AA:AA:AA:AA"},
            "Router_1": {
                "ingress_ip": "10.0.1.1", "ingress_mac": "R1:IN:00:00:00:01",
                "egress_ip": "10.0.2.1", "egress_mac": "R1:OU:00:00:00:02"
            },
            "Router_2": {
                "ingress_ip": "10.0.2.2", "ingress_mac": "R2:IN:00:00:00:01",
                "egress_ip": "10.0.3.1", "egress_mac": "R2:OU:00:00:00:02"
            },
            "Host_B": {"ip": "10.0.3.100", "mac": "BB:BB:BB:BB:BB:BB"}
        }

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def execute_packet_walk(self) -> None:
        """Simulates the L2 MAC rewrite and L3 IP retention across multiple hops."""
        
        flow = []
        frames = []
        
        src_ip = self.topology["Host_A"]["ip"]
        dst_ip = self.topology["Host_B"]["ip"]
        
        # HOP 1: Host A to Router 1
        flow.append("1. [Host A]: Dest IP is on remote subnet. ARPs for Default Gateway (Router 1).")
        frame_1 = {
            "hop": "Hop 1 (Host A -> Router 1)",
            "l3_src": src_ip, "l3_dst": dst_ip,
            "l2_src": self.topology["Host_A"]["mac"],
            "l2_dst": self.topology["Router_1"]["ingress_mac"]
        }
        frames.append(frame_1)
        
        # HOP 2: Router 1 to Router 2
        flow.append("2. [Router 1]: Strips L2 Header. Decrements TTL. Routes packet to Router 2.")
        flow.append("3. [Router 1]: ARPs for Router 2's ingress interface. Generates NEW L2 Header.")
        frame_2 = {
            "hop": "Hop 2 (Router 1 -> Router 2)",
            "l3_src": src_ip, "l3_dst": dst_ip,
            "l2_src": self.topology["Router_1"]["egress_mac"],
            "l2_dst": self.topology["Router_2"]["ingress_mac"]
        }
        frames.append(frame_2)
        
        # HOP 3: Router 2 to Host B
        flow.append("4. [Router 2]: Strips L2 Header. Decrements TTL. Network matches directly connected subnet.")
        flow.append("5. [Router 2]: ARPs directly for Host B. Generates NEW L2 Header.")
        frame_3 = {
            "hop": "Hop 3 (Router 2 -> Host B)",
            "l3_src": src_ip, "l3_dst": dst_ip,
            "l2_src": self.topology["Router_2"]["egress_mac"],
            "l2_dst": self.topology["Host_B"]["mac"]
        }
        frames.append(frame_3)
        
        flow.append("6. [Host B]: Receives frame. Dest MAC matches NIC. Dest IP matches OS.")

        insight = "If a GATE question asks how many times the IP address changes between A and B, the answer is 0. If it asks how many times the MAC address changes, count the number of distinct physical wires (hops) the packet traverses. The MAC is rewritten at every single router egress port."

        self.routing_state = {
            "flow": flow,
            "frames": frames,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.routing_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04Z: HOP-BY-HOP MAC REWRITE ENGINE ".center(width))
        print("=" * width)
        
        print(" [i] ROUTING DECISION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] WIRE ENCAPSULATION STATE AT EACH HOP:")
        time.sleep(0.3)
        for frame in state['frames']:
            print(f"\n     [{frame['hop']}]")
            print(f"     L3 IP Header  | Src IP : {frame['l3_src']:<15} | Dst IP : {frame['l3_dst']}")
            print(f"     L2 MAC Header | Src MAC: {frame['l2_src']} | Dst MAC: {frame['l2_dst']}")
            time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f" [!] GATE EXAM INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = HopByHopRewriteEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04Z_HOP_BY_HOP_MAC_REWRITE INITIALIZED ".center(width))
    print(" Type 'start' to simulate the multi-hop rewrite, or 'quit' to exit.".center(width))
    print("=" * width)

    while True:
        try:
            cmd = input("\n[?] Command (start/quit) [Default: start] : ").strip().lower() or "start"
            if cmd in ['quit', 'exit']: sys.exit(0)
            
            engine.execute_packet_walk()
            engine.render_ui()
            break # Run once then prompt again or exit naturally
            
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()