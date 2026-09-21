"""
Core Logic: This is the #1 most tested concept in GATE Computer Networks routing questions.
When Host A wants to send a packet to Host B, it does NOT simply broadcast an ARP request 
for Host B's IP address. 

Before generating an ARP request, the OS network stack must mathematically determine if 
the destination is on the LOCAL subnet or a REMOTE subnet.

The mathematical trap (The Bitwise AND):
1. Host A performs a Bitwise AND of its own IP and its Subnet Mask to find its Network ID.
2. Host A performs a Bitwise AND of the Destination IP and its Subnet Mask to find the Target Network ID.
3. LOCAL SUBNET (Matches): If the Network IDs are identical, the destination is on the 
   same wire. The host generates an ARP Request directly for the Destination IP.
4. REMOTE SUBNET (Mismatch): If the Network IDs differ, the destination is behind a router. 
   The host MUST generate an ARP Request for the DEFAULT GATEWAY'S IP. 

If GATE candidates forget this step, they incorrectly assume the Source MAC will map to 
the Destination MAC across routers, completely failing the numerical question.
"""

import sys
import shutil
import time
import ipaddress
from typing import Any, Dict

class DefaultGatewayTrapEngine:
    trap_state: Dict[str, Any]

    def __init__(self) -> None:
        self.trap_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            ipaddress.IPv4Address(ip_input.strip())
            return ip_input.strip()
        except ValueError:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv4 address.")

    def execute_routing_physics(self, host_ip: str, subnet_mask: str, dest_ip: str, gateway_ip: str) -> None:
        """Simulates the bitwise AND OS routing decision before ARP generation."""
        
        flow = []
        
        # 1. Mathematical Parsing
        host_iface = ipaddress.IPv4Interface(f"{host_ip}/{subnet_mask}")
        host_net_id = host_iface.network.network_address
        
        dest_addr = ipaddress.IPv4Address(dest_ip)
        dest_net_id = ipaddress.IPv4Network(f"{dest_ip}/{subnet_mask}", strict=False).network_address
        
        flow.append(f"1. [Host OS]: App wants to send payload to Destination {dest_ip}.")
        flow.append(f"2. [Host OS]: Executing Bitwise AND -> (Host IP {host_ip} & Mask {subnet_mask})")
        flow.append(f"   -> Host Network ID Calculated  : {host_net_id}")
        flow.append(f"3. [Host OS]: Executing Bitwise AND -> (Dest IP {dest_ip} & Mask {subnet_mask})")
        flow.append(f"   -> Target Network ID Calculated: {dest_net_id}")
        
        # 2. Decision Engine
        if host_net_id == dest_net_id:
            flow.append("4. [Routing Table]: Network IDs MATCH. Destination is on the LOCAL subnet.")
            flow.append(f"5. [ARP Engine]: Generating ARP Request for DESTINATION IP -> 'Who has {dest_ip}?'")
            action = "DIRECT ARP (Local Link)"
            arp_target = dest_ip
            insight = "Because the destination is local, the MAC address acquired will belong to the actual destination host. Switches will forward this strictly at Layer 2."
        else:
            flow.append("4. [Routing Table]: Network IDs MISMATCH. Destination is on a REMOTE subnet.")
            flow.append(f"5. [Routing Table]: Forwarding payload to Default Gateway -> {gateway_ip}.")
            flow.append(f"6. [ARP Engine]: Generating ARP Request for GATEWAY IP -> 'Who has {gateway_ip}?'")
            action = "DEFAULT GATEWAY TRAP (Remote Routed)"
            arp_target = gateway_ip
            insight = "GATE TRAP: The host ARPs for the Router's MAC, not the Destination's MAC. The resulting Ethernet frame will have [Dst MAC: Router, Dst IP: Final Target]. The IP header never changes, but the MAC header stops at the router."

        self.trap_state = {
            "host_ip": host_ip,
            "mask": subnet_mask,
            "dest_ip": dest_ip,
            "gateway_ip": gateway_ip,
            "host_net": str(host_net_id),
            "dest_net": str(dest_net_id),
            "flow": flow,
            "action": action,
            "arp_target": arp_target,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.trap_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04Y: DEFAULT GATEWAY TRAP ENGINE (GATE PHYSICS) ".center(width))
        print("=" * width)
        
        print(f" [+] HOST OS IP CONFIGURATION:")
        print(f"     -> Source IP Address    : {state['host_ip']}")
        print(f"     -> Subnet Mask          : {state['mask']}")
        print(f"     -> Default Gateway      : {state['gateway_ip']}")
        print(f"     -> Final Destination IP : {state['dest_ip']}")
        print("-" * width)
        
        print(" [i] BITWISE ROUTING SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] LAYER 2 ARP OUTCOME:")
        time.sleep(0.3)
        print(f"     -> Forwarding Decision  : [ {state['action']} ]")
        print(f"     -> ARP Request Target   : {state['arp_target']}")
        
        print("-" * width)
        print(f" [!] GATE EXAM INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = DefaultGatewayTrapEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04Y_DEFAULT_GATEWAY_TRAP INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Host Network Stack Bitwise Logic:")
            print("    (Tip: Try Dest 192.168.1.50 for Local, or 8.8.8.8 for Remote Gateway Trap)")
            
            hip_in = input("    Host IP Address      [Default: 192.168.1.10]    : ").strip() or "192.168.1.10"
            if hip_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            mask_in = input("    Subnet Mask          [Default: 255.255.255.0]   : ").strip() or "255.255.255.0"
            gw_in = input("    Default Gateway      [Default: 192.168.1.1]     : ").strip() or "192.168.1.1"
            dest_in = input("    Final Destination IP [Default: 8.8.8.8]         : ").strip() or "8.8.8.8"
            
            host_ip = engine.validate_ip(hip_in, "Host IP")
            mask = engine.validate_ip(mask_in, "Subnet Mask")
            gateway_ip = engine.validate_ip(gw_in, "Default Gateway")
            dest_ip = engine.validate_ip(dest_in, "Destination IP")
            
            engine.execute_routing_physics(host_ip, mask, dest_ip, gateway_ip)
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