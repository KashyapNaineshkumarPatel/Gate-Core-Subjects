"""
Core Logic: In standard Reverse Proxy Load Balancing (Module 04AB), the Load Balancer 
(LB) becomes a bottleneck because ALL return traffic from the backend servers must 
flow back through the LB to the client.

Direct Server Return (DSR) solves this. 
In DSR, the LB only intercepts the incoming request. It changes the Destination MAC 
to a backend server, but leaves the Destination IP as the VIP. 
The backend server processes the request and sends the massive HTTP response 
DIRECTLY back to the client, bypassing the LB entirely.

The ARP Danger:
For the backend server to accept a packet destined for the VIP, the VIP must be 
configured on the server's local loopback interface (lo). 
However, if the backend server replies to ARP broadcasts for the VIP, it will race 
against the Load Balancer. The client's ARP cache will flap, and traffic will 
bypass the LB entirely, destroying the cluster.

To fix this, Linux kernel parameters MUST be heavily modified on the backend:
- net.ipv4.conf.all.arp_ignore = 1 (Do not reply to ARP if IP is not on the receiving interface)
- net.ipv4.conf.all.arp_announce = 2 (Always use the best local IP for ARP requests)
"""

import sys
import shutil
import time
from typing import Any, Dict

class DSRARPSuppressionEngine:
    dsr_state: Dict[str, Any]

    def __init__(self) -> None:
        self.dsr_state = {}
        
        # DSR Topology
        self.vip = "10.100.1.50"
        self.lb_mac = "LB:00:11:22:33:44"
        self.client_ip = "192.168.5.50"
        self.client_mac = "CC:LL:II:EE:NN:TT"
        
        # Backend Node
        self.backend_ip = "172.16.1.11"
        self.backend_mac = "BB:BB:BB:22:22:22"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def execute_dsr_physics(self, suppression_enabled: bool) -> None:
        """Simulates DSR traffic flow with and without ARP suppression."""
        
        flow = []
        frames = []
        action = ""
        insight = ""
        
        flow.append(f"1. [Client]: Broadcasts ARP Request -> 'Who has VIP {self.vip}?'")
        
        if not suppression_enabled:
            # The Disaster Scenario
            flow.append(f"2. [Load Balancer]: Replies '{self.vip} is at {self.lb_mac}'.")
            flow.append(f"3. [Backend OS]: Loopback interface sees ARP. Replies '{self.vip} is at {self.backend_mac}'.")
            flow.append("4. [Fabric]: Race condition! Switch MAC table flapping.")
            flow.append("5. [Client]: Receives Backend's ARP reply last. Cache overwritten.")
            
            frame_1 = {
                "stage": "Ingress (Client -> Backend)",
                "l3_src": self.client_ip, "l3_dst": self.vip,
                "l2_src": self.client_mac, "l2_dst": self.backend_mac
            }
            frames.append(frame_1)
            
            flow.append("6. [Client]: Sends L3 payload DIRECTLY to Backend MAC, bypassing LB.")
            action = "CATASTROPHIC FAILURE (Load Balancing Defeated)"
            insight = "Without arp_ignore=1, the backend server claims the VIP on the physical wire. The Load Balancer is completely bypassed, and this single backend node will be crushed by all incoming traffic."
            
        else:
            # The Correct DSR Scenario
            flow.append("2. [Backend OS]: arp_ignore=1 strictly suppresses ARP reply for loopback VIP.")
            flow.append(f"3. [Load Balancer]: Replies '{self.vip} is at {self.lb_mac}'. Client cache stable.")
            
            frame_1 = {
                "stage": "Ingress (Client -> LB)",
                "l3_src": self.client_ip, "l3_dst": self.vip,
                "l2_src": self.client_mac, "l2_dst": self.lb_mac
            }
            frames.append(frame_1)
            
            flow.append("4. [Load Balancer]: Receives frame. Alters ONLY Layer 2 Destination MAC.")
            
            frame_2 = {
                "stage": "Steering (LB -> Backend)",
                "l3_src": self.client_ip, "l3_dst": self.vip,  # NO NAT! IP remains intact.
                "l2_src": self.lb_mac, "l2_dst": self.backend_mac
            }
            frames.append(frame_2)
            
            flow.append("5. [Backend OS]: Receives frame on physical NIC. Accepts it because VIP is on loopback.")
            flow.append("6. [Backend OS]: Processes request. Routes HTTP response DIRECTLY to client.")
            
            frame_3 = {
                "stage": "Direct Server Return (Backend -> Client)",
                "l3_src": self.vip, "l3_dst": self.client_ip,
                "l2_src": self.backend_mac, "l2_dst": self.client_mac
            }
            frames.append(frame_3)
            
            action = "DSR SUCCESS (Asymmetric Routing Enabled)"
            insight = "DSR is incredibly powerful for video streaming (like Netflix). A 10kb request hits the LB, but the 5GB video response bypasses the LB, saving massive bandwidth. Strict ARP suppression in the Linux kernel is the only thing making this possible."

        self.dsr_state = {
            "suppression": suppression_enabled,
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.dsr_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AC: DSR ARP SUPPRESSION ENGINE ".center(width))
        print("=" * width)
        
        supp_text = "ENABLED (arp_ignore=1, arp_announce=2)" if state['suppression'] else "DISABLED (Default Linux Kernel)"
        print(f" [+] BACKEND KERNEL STATE:")
        print(f"     -> ARP Suppression  : {supp_text}")
        print(f"     -> VIP Interface    : Loopback (lo)")
        print("-" * width)
        
        print(" [i] ARP RESOLUTION & DATAPLANE SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] ENCAPSULATION STATES (ASYMMETRIC ROUTING):")
        time.sleep(0.3)
        for frame in state['frames']:
            print(f"\n     [{frame['stage']}]")
            print(f"     L3 IP Header  | Src IP : {frame['l3_src']:<15} | Dst IP : {frame['l3_dst']}")
            print(f"     L2 MAC Header | Src MAC: {frame['l2_src']:<15} | Dst MAC: {frame['l2_dst']}")
            time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f" [!] ARCHITECTURAL ENGINEERING OUTCOME: [ {state['action']} ]")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = DSRARPSuppressionEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AC_DSR_ARP_SUPPRESSION INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure Backend Linux Kernel:")
            print("    1. Enable strict ARP suppression (arp_ignore=1) [Proper DSR]")
            print("    2. Leave default kernel settings [Disaster Mode]")
            
            choice = input("    Select configuration (1/2) [Default: 1] : ").strip() or "1"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            suppression = (choice == "1")
            
            engine.execute_dsr_physics(suppression)
            engine.render_ui()
            
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()