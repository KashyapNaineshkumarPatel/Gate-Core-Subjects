"""
Core Logic: In modern enterprise datacenters, horizontal scaling requires abstracting 
dozens of backend servers behind a single Virtual IP (VIP). To distribute this traffic, 
a Load Balancer (LB) or Application Delivery Controller (ADC) must manipulate the 
Layer 2 fabric via ARP Steering.

The mechanics of VIP ARP Steering:
1. The Load Balancer binds the cluster's VIP to its own external network interface.
2. When a client or gateway router broadcasts an ARP Request for the VIP, the LB 
   instantly replies with its own hardware MAC address.
3. The client encapsulates its L3 TCP/HTTP payload inside an L2 frame destined for 
   the LB's MAC, believing the LB is the final destination.
4. The LB intercepts the frame, terminates the connection (L4-L7 inspection), applies 
   a load-balancing algorithm (e.g., Round Robin, Least Connections), and selects a 
   backend node.
5. The LB then generates a NEW frame on its internal interface, steering the traffic 
   to the chosen backend server's real IP and real MAC.

This completely breaks the traditional 1-to-1 IP-to-MAC mapping. The VIP becomes an 
Anycast/Steering anchor, allowing the LB to pull all traffic to itself for software-defined 
routing.
"""

import sys
import shutil
import time
import ipaddress
from typing import Any, Dict

class AnycastARPSteeringEngine:
    steering_state: Dict[str, Any]

    def __init__(self) -> None:
        self.steering_state = {}
        
        # Load Balancer Configuration
        self.vip = "10.100.1.50"
        self.lb_mac = "LB:00:11:22:33:44"
        
        # Backend Server Pool
        self.backend_pool = [
            {"node": "Node_A", "ip": "172.16.1.10", "mac": "AA:AA:AA:11:11:11"},
            {"node": "Node_B", "ip": "172.16.1.11", "mac": "BB:BB:BB:22:22:22"},
            {"node": "Node_C", "ip": "172.16.1.12", "mac": "CC:CC:CC:33:33:33"}
        ]
        self.rr_index = 0  # Round Robin state pointer

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            ipaddress.IPv4Address(ip_input.strip())
            return ip_input.strip()
        except ValueError:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv4 address.")

    def execute_steering_physics(self, client_ip: str, client_mac: str) -> None:
        """Simulates the L2 ARP interception and L4 steering logic of a Load Balancer."""
        
        flow = []
        frames = []
        
        # Select Backend via Round Robin
        selected_backend = self.backend_pool[self.rr_index]
        self.rr_index = (self.rr_index + 1) % len(self.backend_pool)

        flow.append(f"1. [Client OS]: Application initiates TCP connection to VIP {self.vip}.")
        flow.append(f"2. [Client OS]: Broadcasts ARP Request -> 'Who has {self.vip}?'")
        flow.append(f"3. [Load Balancer]: Intercepts ARP. Replies -> '{self.vip} is at MAC {self.lb_mac}'.")
        
        # Frame 1: Client to LB
        frame_1 = {
            "stage": "Ingress (Client -> LB VIP)",
            "l3_src": client_ip, "l3_dst": self.vip,
            "l2_src": client_mac, "l2_dst": self.lb_mac
        }
        frames.append(frame_1)
        
        flow.append("4. [Load Balancer]: Receives frame. Strips L2 Header. Terminates TCP connection (L4).")
        flow.append(f"5. [Load Balancer]: Executes Round Robin selection. Target selected: {selected_backend['node']}.")
        flow.append(f"6. [Load Balancer]: ARPs for backend IP {selected_backend['ip']}. Resolves to {selected_backend['mac']}.")
        flow.append("7. [Load Balancer]: Rewrites headers (Reverse Proxy Mode). Dispatches payload to backend.")
        
        # Frame 2: LB to Backend Node
        frame_2 = {
            "stage": f"Egress (LB -> {selected_backend['node']})",
            "l3_src": self.vip, "l3_dst": selected_backend['ip'],  # Source NAT applied by LB
            "l2_src": self.lb_mac, "l2_dst": selected_backend['mac']
        }
        frames.append(frame_2)

        insight = (
            "Because the Load Balancer answers ARP for the VIP, the physical switch naturally "
            "learns that the VIP resides on the LB's physical switchport. All L2 traffic flows "
            "there seamlessly. The actual steering to the backend servers happens purely in "
            "software at Layers 3 and 4, utilizing completely different L2 MAC domains."
        )

        self.steering_state = {
            "client_ip": client_ip,
            "vip": self.vip,
            "selected_node": selected_backend['node'],
            "flow": flow,
            "frames": frames,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.steering_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AB: ANYCAST ARP STEERING (LOAD BALANCING) ".center(width))
        print("=" * width)
        
        print(f" [+] CLUSTER CONFIGURATION:")
        print(f"     -> Front-End VIP      : {state['vip']} (Bound to LB MAC)")
        print(f"     -> Load Balance Algo  : Round Robin")
        print(f"     -> Selected Backend   : {state['selected_node']}")
        print("-" * width)
        
        print(" [i] ARP INTERCEPTION & L4 STEERING SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] DATAPLANE ENCAPSULATION STATES:")
        time.sleep(0.3)
        for frame in state['frames']:
            print(f"\n     [{frame['stage']}]")
            print(f"     L3 IP Header  | Src IP : {frame['l3_src']:<15} | Dst IP : {frame['l3_dst']}")
            print(f"     L2 MAC Header | Src MAC: {frame['l2_src']:<15} | Dst MAC: {frame['l2_dst']}")
            time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = AnycastARPSteeringEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AB_ANYCAST_ARP_STEERING INITIALIZED ".center(width))
    print(" Type 'start' to simulate a client request, or 'quit' to exit.".center(width))
    print("=" * width)

    while True:
        try:
            cmd = input("\n[?] Command (start/quit) [Default: start] : ").strip().lower() or "start"
            if cmd in ['quit', 'exit']: sys.exit(0)
            
            client_ip = "192.168.5.50"
            client_mac = "CC:LL:II:EE:NN:TT"
            
            engine.execute_steering_physics(client_ip, client_mac)
            engine.render_ui()
            
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()