"""
Core Logic: According to strict OSI rules, a host should only send an ARP broadcast 
for destinations on its exact local subnet. For remote destinations, it should ARP 
for its Default Gateway. 

However, network administrators frequently misconfigure subnet masks (e.g., setting a 
/16 mask instead of a /24). When this happens, a host mistakenly believes a remote IP 
is locally attached and broadcasts an ARP request for it. 

Standard routers will drop this broadcast, breaking connectivity. RFC 1027 introduced 
Proxy ARP to "save" misconfigured hosts. If a router has Proxy ARP enabled on an interface, 
hears an ARP request for a target IP, and knows a route to that target IP, the router 
will deliberately lie. It will send an ARP Reply claiming *its own MAC address* belongs 
to the remote target IP.

The sender unknowingly forwards the physical Ethernet frames to the router, and the 
router handles the Layer 3 forwarding. While helpful for misconfigurations or legacy 
dial-up networks, Proxy ARP is a massive security risk, allowing attackers to easily 
blackhole or hijack subnets.
"""

import sys
import shutil
import time
import ipaddress
from typing import Any, Dict

class ProxyARPEngine:
    proxy_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.proxy_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            ipaddress.IPv4Address(ip_input.strip())
            return ip_input.strip()
        except ValueError:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv4 address.")

    def validate_mask(self, mask_input: str) -> str:
        try:
            # Test if it's a valid CIDR prefix or netmask
            if mask_input.startswith('/'):
                prefix = int(mask_input[1:])
                if not (0 <= prefix <= 32):
                    raise ValueError()
                return mask_input.strip()
            else:
                ipaddress.IPv4Network(f"0.0.0.0/{mask_input.strip()}", strict=False)
                return mask_input.strip()
        except ValueError:
            raise ValueError("Syntax Error: Invalid Subnet Mask format (e.g., /16 or 255.255.0.0).")

    def execute_proxy_arp_evaluation(self, sender_ip: str, sender_mask: str, target_ip: str, proxy_enabled: bool) -> None:
        """Simulates subnet logic and the Router's Proxy ARP interception."""
        
        # 1. Host Routing Decision (The Misconfiguration check)
        try:
            if sender_mask.startswith('/'):
                sender_network = ipaddress.IPv4Network(f"{sender_ip}{sender_mask}", strict=False)
            else:
                sender_network = ipaddress.IPv4Network(f"{sender_ip}/{sender_mask}", strict=False)
                
            target = ipaddress.IPv4Address(target_ip)
            
        except ValueError as e:
            raise ValueError(f"IP Calculation Error: {e}")

        sender_thinks_local = target in sender_network
        
        # Simulated Network Physics
        router_mac = "AA:BB:CC:DD:EE:FF"
        host_action = ""
        router_action = ""
        final_result = ""
        
        if not sender_thinks_local:
            host_action = "Host correctly determines Target is REMOTE. Host sends ARP for its Default Gateway."
            router_action = "Router replies normally for its own IP."
            final_result = "NORMAL ROUTING. Proxy ARP not invoked."
        else:
            host_action = f"Host mistakenly thinks {target_ip} is LOCAL due to mask. Broadcasts ARP Request for {target_ip}."
            
            if proxy_enabled:
                router_action = f"Router intercepts ARP for {target_ip}. Router checks routing table, finds route, and replies with its OWN MAC: {router_mac}."
                final_result = "PROXY SUCCESS (DECEPTION). Host communicates with target via the Router."
            else:
                router_action = f"Router sees ARP for {target_ip}. Proxy ARP is disabled. Router strictly drops the broadcast."
                final_result = "COMMUNICATION FAILURE. Host receives no ARP reply. Connection drops."

        insight = (
            "Proxy ARP abstracts Layer 3 routing topology away from Layer 2 hosts. "
            "While it acts as a band-aid for bad subnet masking, it is dangerous. If two routers "
            "have Proxy ARP enabled, they will both reply to the broadcast, creating a race condition "
            "where the host's traffic is load-balanced into unpredictable, asymmetric routing paths."
        )

        self.proxy_state = {
            "sender_ip": sender_ip,
            "sender_mask": sender_mask,
            "target_ip": target_ip,
            "thinks_local": sender_thinks_local,
            "proxy_enabled": proxy_enabled,
            "host_action": host_action,
            "router_action": router_action,
            "final_result": final_result,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.proxy_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04G: RFC 1027 PROXY ARP TRAP ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] HOST CONFIGURATION & LOGIC:")
        print(f"     -> Sender IP/Mask     : {state['sender_ip']} mask {state['sender_mask']}")
        print(f"     -> Target IP          : {state['target_ip']}")
        
        local_eval = "YES (Misconfigured Mask)" if state['thinks_local'] else "NO (Correct Routing)"
        print(f"     -> Evaluated as Local : {local_eval}")
        print("-" * width)
        
        print(" [i] WIRE-LEVEL RESOLUTION:")
        time.sleep(0.3)
        print(f"     -> Host Action        : {state['host_action']}")
        time.sleep(0.3)
        print(f"     -> Router Action      : {state['router_action']}")
        print("-" * width)
        
        print(" [!] FINAL TRAFFIC STATE:")
        time.sleep(0.3)
        print(f"     -> Outcome            : [ {state['final_result']} ]")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = ProxyARPEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04G_RFC1027_PROXY_ARP_TRAP INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure Host and Target IP logic:")
            print("    (Tip: Use Sender 192.168.1.10/16 and Target 192.168.2.50 to simulate misconfiguration)")
            
            sip_in = input("    Sender IP Address      [Default: 192.168.1.10] : ").strip() or "192.168.1.10"
            if sip_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            mask_in = input("    Sender Subnet Mask     [Default: /16]          : ").strip() or "/16"
            tip_in = input("    Target IP Address      [Default: 192.168.2.50] : ").strip() or "192.168.2.50"
            
            print("\n[?] Configure Default Gateway Proxy ARP State:")
            proxy_in = input("    Enable Proxy ARP on Router? (Y/N) [Default: Y] : ").strip().upper() or "Y"
            
            sender_ip = engine.validate_ip(sip_in, "Sender IP")
            sender_mask = engine.validate_mask(mask_in)
            target_ip = engine.validate_ip(tip_in, "Target IP")
            proxy_enabled = proxy_in == "Y"
            
            engine.execute_proxy_arp_evaluation(sender_ip, sender_mask, target_ip, proxy_enabled)
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