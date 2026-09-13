"""
Core Logic: The greatest flaw of IPv4 is the ARP Broadcast (FF:FF:FF:FF:FF:FF). 
Every time a device ARPs, every single node on the physical subnet must fire a 
hardware interrupt, wake its CPU, and inspect the payload, wasting massive amounts 
of battery and CPU cycles across the enterprise.

IPv6 eliminates Broadcasts entirely. ARP is dead. It is replaced by the ICMPv6 
Neighbor Discovery Protocol (NDP).

Instead of shouting to everyone, IPv6 uses Solicited-Node Multicast Addresses (SNMA).
1. Every IPv6 device takes the last 24 bits of its own IPv6 address.
2. It appends them to a reserved multicast prefix: FF02::1:FFxx:xxxx.
3. The device programs its Network Interface Card (NIC) to listen to a specific 
   Multicast Ethernet MAC address: 33:33:FF:xx:xx:xx.
4. When Host A wants to find Host B, it mathematically calculates Host B's SNMA 
   and Multicast MAC locally. 
5. Host A sends an ICMPv6 Neighbor Solicitation (NS) exactly to that Multicast MAC.
6. The network switch forwards the multicast. ONLY Host B (and any device sharing 
   those exact last 24 bits) wakes up. The other 99% of the subnet remains asleep.
"""

import sys
import shutil
import time
import ipaddress
import binascii
from typing import Any, Dict

class NDPSolicitedNodeEngine:
    ndp_state: Dict[str, Any]

    def __init__(self) -> None:
        self.ndp_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def validate_ipv6(self, ip_input: str, name: str) -> str:
        try:
            addr = ipaddress.IPv6Address(ip_input.strip())
            return str(addr.exploded)
        except ValueError:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv6 address.")

    def execute_ndp_physics(self, target_ipv6: str) -> None:
        """Simulates the mathematical derivation of SNMA and Multicast MAC for NDP."""
        
        flow = []
        
        # Parse the exploded IPv6 address (e.g., 2001:0db8:0000:0000:0000:0000:abcd:ef12)
        # We need the last 24 bits (6 hex chars). 
        # Removing colons leaves 32 hex chars. The last 6 are the 24 bits.
        clean_hex = target_ipv6.replace(":", "")
        last_24_bits = clean_hex[-6:]
        
        # 1. Derive Solicited-Node Multicast Address (SNMA)
        # Prefix: FF02::1:FF00:0/104
        snma = f"FF02:0000:0000:0000:0000:0001:FF{last_24_bits[:2]}:{last_24_bits[2:]}"
        compressed_snma = str(ipaddress.IPv6Address(snma))
        
        # 2. Derive Ethernet Multicast MAC Address
        # Prefix: 33:33:FF:xx:xx:xx
        multicast_mac = f"33:33:FF:{last_24_bits[:2]}:{last_24_bits[2:4]}:{last_24_bits[4:]}".upper()
        
        flow.append(f"1. [Host OS]: App wants to resolve Target IPv6 {ipaddress.IPv6Address(target_ipv6)}.")
        flow.append(f"2. [IPv6 Stack]: Extracting last 24 bits of Target IPv6 -> 0x{last_24_bits.upper()}.")
        flow.append(f"3. [NDP Engine]: Deriving Solicited-Node Multicast Address (SNMA).")
        flow.append(f"   -> SNMA: {compressed_snma}")
        flow.append(f"4. [NDP Engine]: Deriving Layer 2 Ethernet Multicast MAC.")
        flow.append(f"   -> MAC : {multicast_mac}")
        
        flow.append(f"5. [NIC Hardware]: Transmitting ICMPv6 Neighbor Solicitation (Type 135) to {multicast_mac}.")
        flow.append("6. [Switch Fabric]: Forwards frame only to ports subscribed to this Multicast group via MLD snooping.")
        flow.append("7. [Subnet CPUs]: 99% of devices on the subnet IGNORE the frame. Hardware interrupts avoided.")
        flow.append(f"8. [Target Device]: NIC hardware filter matches {multicast_mac}. Wakes CPU to reply via Unicast NA (Type 136).")

        action = "MULTICAST RESOLUTION SUCCESS"
        insight = (
            "IPv6 mathematically eliminates the broadcast storm. The switch only delivers the frame to "
            "interested receivers, and unrelated hosts never waste CPU cycles inspecting ARP traffic. "
            "This makes IPv6 networks infinitely more scalable at the physical Layer 2 fabric level."
        )

        self.ndp_state = {
            "target": str(ipaddress.IPv6Address(target_ipv6)),
            "last_24": last_24_bits.upper(),
            "snma": compressed_snma,
            "mac": multicast_mac,
            "flow": flow,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.ndp_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AL: IPv6 NDP SOLICITED-NODE MULTICAST ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] TARGET DERIVATION MATHEMATICS:")
        print(f"     -> Target IPv6 Address : {state['target']}")
        print(f"     -> Isolated 24 Bits    : 0x{state['last_24']}")
        print(f"     -> Derived SNMA (L3)   : {state['snma']}")
        print(f"     -> Derived MAC (L2)    : {state['mac']}")
        print("-" * width)
        
        print(" [i] NEIGHBOR DISCOVERY PROTOCOL (NDP) SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] DATAPLANE OUTCOME:")
        time.sleep(0.3)
        print(f"     -> Action           : [ {state['action']} ]")
        print(f"     -> CPU Impact       : SURGICAL (Zero Broadcast Waste)")
        
        print("\n" + "-" * width)
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = NDPSolicitedNodeEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AL_NDP_SOLICITED_NODE_MULTICAST INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate IPv6 NDP Resolution:")
            print("    (Tip: Leave default to see how 2001:db8::1:abcd:ef12 converts to Multicast)")
            
            ipv6_in = input("    Target IPv6 Address [Default: 2001:db8::1:abcd:ef12] : ").strip() or "2001:db8::1:abcd:ef12"
            if ipv6_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            target_ip = engine.validate_ipv6(ipv6_in, "IPv6 Target")
            
            engine.execute_ndp_physics(target_ip)
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