"""
Core Logic: In GATE routing questions, a common trick involves a host with a 
misconfigured Subnet Mask. 

Suppose a company network is physically divided into multiple /24 subnets. 
Host A is on 10.1.1.0/24. 
Host B is on 10.1.2.0/24.
They are separated by a router.

If a junior admin accidentally configures Host A with a /16 subnet mask (255.255.0.0) 
instead of /24 (255.255.255.0), the Bitwise AND logic breaks:
1. Host A (10.1.1.50) wants to ping Host B (10.1.2.50).
2. Host A applies its misconfigured /16 mask to Host B's IP.
3. Host A calculates the Target Network ID as 10.1.0.0.
4. Host A calculates its own Network ID as 10.1.0.0.
5. Host A incorrectly believes Host B is on the LOCAL physical switch.
6. Host A completely ignores its Default Gateway.
7. Host A broadcasts an ARP Request: "Who has 10.1.2.50?"
8. The router receives the broadcast, but because it is a router, it drops L2 broadcasts 
   and does not reply (unless Proxy ARP is enabled). 
9. Host A's ARP request times out. The ping fails with "Destination Host Unreachable," 
   even though the routing tables on the routers are perfectly fine.
"""

import sys
import shutil
import time
import ipaddress
from typing import Any, Dict

class ARPMisfireEngine:
    misfire_state: Dict[str, Any]

    def __init__(self) -> None:
        self.misfire_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            ipaddress.IPv4Address(ip_input.strip())
            return ip_input.strip()
        except ValueError:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv4 address.")

    def execute_misfire_physics(self, host_ip: str, bad_mask: str, dest_ip: str, gateway_ip: str) -> None:
        """Simulates the routing failure caused by a misconfigured subnet mask."""
        
        flow = []
        
        # 1. Mathematical Parsing with Misconfigured Mask
        host_iface = ipaddress.IPv4Interface(f"{host_ip}/{bad_mask}")
        host_net_id = host_iface.network.network_address
        
        dest_net_id = ipaddress.IPv4Network(f"{dest_ip}/{bad_mask}", strict=False).network_address
        
        flow.append(f"1. [Host OS]: App wants to send payload to Destination {dest_ip}.")
        flow.append(f"2. [Host OS]: Executing Bitwise AND -> (Host IP {host_ip} & Misconfigured Mask {bad_mask})")
        flow.append(f"   -> Calculated Host Net ID  : {host_net_id}")
        flow.append(f"3. [Host OS]: Executing Bitwise AND -> (Dest IP {dest_ip} & Misconfigured Mask {bad_mask})")
        flow.append(f"   -> Calculated Target Net ID: {dest_net_id}")
        
        # 2. Decision Engine (The Flaw)
        if host_net_id == dest_net_id:
            flow.append("4. [Routing Logic]: FALSE POSITIVE! Host believes Destination is on the LOCAL subnet.")
            flow.append(f"5. [Routing Logic]: Host ignores Default Gateway ({gateway_ip}).")
            flow.append(f"6. [ARP Engine]: Generates L2 Broadcast -> 'Who has {dest_ip}?'")
            flow.append("7. [Fabric]: Switch floods broadcast. Router receives it.")
            flow.append("8. [Router]: Drops L2 broadcast. Does not reply (Proxy ARP disabled by default).")
            flow.append("9. [Host OS]: ARP Timeout. Packet dropped internally.")
            
            action = "ARP MISFIRE / TIMEOUT (Routing Blackhole)"
            color = "CRITICAL FAILURE - HOST ISOLATION"
            insight = "GATE TRAP: When a mask is 'too wide' (e.g., /16 instead of /24), the host attempts Layer 2 ARP resolution across a Layer 3 boundary. The packet never even reaches the router's dataplane. The failure happens entirely on the source host."
        else:
            flow.append("4. [Routing Logic]: Network IDs Mismatch. Host routes to Default Gateway.")
            flow.append(f"5. [ARP Engine]: Generates L2 Broadcast -> 'Who has {gateway_ip}?'")
            flow.append("6. [Fabric]: Router replies with MAC. Traffic forwarded successfully.")
            
            action = "NORMAL ROUTED FORWARDING"
            color = "NOMINAL"
            insight = "The subnet mask provided was narrow enough to correctly identify the destination as a remote network."

        self.misfire_state = {
            "host_ip": host_ip,
            "mask": bad_mask,
            "dest_ip": dest_ip,
            "gateway_ip": gateway_ip,
            "host_net": str(host_net_id),
            "dest_net": str(dest_net_id),
            "flow": flow,
            "action": action,
            "color": color,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.misfire_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AA: SUBNET MASK ARP MISFIRE ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] HOST OS MISCONFIGURATION:")
        print(f"     -> Source IP Address    : {state['host_ip']}")
        print(f"     -> Subnet Mask          : {state['mask']} (Misconfigured/Too Wide)")
        print(f"     -> Default Gateway      : {state['gateway_ip']}")
        print(f"     -> Final Destination IP : {state['dest_ip']}")
        print("-" * width)
        
        print(" [i] FLAWED BITWISE ROUTING SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] DATAPLANE OUTCOME:")
        time.sleep(0.3)
        print(f"     -> Action           : [ {state['action']} ]")
        print(f"     -> Dataplane State  : {state['color']}")
        
        print("-" * width)
        print(f" [!] GATE EXAM INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = ARPMisfireEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AA_SUBNET_MASK_ARP_MISFIRE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Subnet Mask Misfire:")
            print("    (Tip: Leave defaults to see how a /16 mask breaks communication to a remote /24 subnet)")
            
            hip_in = input("    Host IP Address      [Default: 10.1.1.50]   : ").strip() or "10.1.1.50"
            if hip_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            mask_in = input("    Host Subnet Mask     [Default: 255.255.0.0] : ").strip() or "255.255.0.0"
            gw_in = input("    Default Gateway      [Default: 10.1.1.1]    : ").strip() or "10.1.1.1"
            dest_in = input("    Final Destination IP [Default: 10.1.2.50]   : ").strip() or "10.1.2.50"
            
            host_ip = engine.validate_ip(hip_in, "Host IP")
            mask = engine.validate_ip(mask_in, "Subnet Mask")
            gateway_ip = engine.validate_ip(gw_in, "Default Gateway")
            dest_ip = engine.validate_ip(dest_in, "Destination IP")
            
            engine.execute_misfire_physics(host_ip, mask, dest_ip, gateway_ip)
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