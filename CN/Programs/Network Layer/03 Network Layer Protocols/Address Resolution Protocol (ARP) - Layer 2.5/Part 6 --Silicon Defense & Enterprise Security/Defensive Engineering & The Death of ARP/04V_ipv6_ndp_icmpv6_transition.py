"""
Core Logic: IPv6 fundamentally kills ARP. 
Broadcasts (FF:FF:FF:FF:FF:FF) were the biggest design flaw in IPv4, forcing every 
CPU on a subnet to interrupt its processes to parse unnecessary ARP packets.

IPv6 eliminates broadcasts entirely, replacing ARP with the Neighbor Discovery Protocol 
(NDP), which operates on top of ICMPv6.

When an IPv6 Host wants to resolve a MAC address:
1. It does NOT broadcast. Instead, it generates a "Solicited-Node Multicast Address".
2. It takes the last 24 bits of the Target IPv6 address and appends them to a strict 
   prefix: FF02::1:FFxx:xxxx.
3. At Layer 2, this maps to a highly specific Ethernet Multicast MAC: 33:33:FF:xx:xx:xx.
4. The host sends an ICMPv6 Type 135 (Neighbor Solicitation) to this specific multicast address.
5. Only the specific target host (or hosts sharing the exact same last 24 bits) will 
   listen to this multicast group. The NIC hardware of all other machines will drop the 
   frame instantly without ever interrupting their CPU.
6. The target replies with an ICMPv6 Type 136 (Neighbor Advertisement), containing its MAC.

By shifting address resolution from Layer 2.5 (ARP) into Layer 3 (ICMPv6), IPv6 allows 
IPsec encryption to secure the resolution process (Secure Neighbor Discovery - SEND), 
conceptually eliminating MITM cache poisoning.
"""

import sys
import shutil
import time
import ipaddress
from typing import Any, Dict

class IPv6NDPEngine:
    ndp_state: Dict[str, Any]

    def __init__(self) -> None:
        self.ndp_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_ipv6(self, ip_input: str) -> str:
        try:
            addr = ipaddress.IPv6Address(ip_input.strip())
            return str(addr.exploded)
        except ValueError:
            raise ValueError("Syntax Error: Must be a valid IPv6 address (e.g., 2001:db8::1).")

    def execute_ndp_physics(self, target_ipv6: str) -> None:
        """Simulates the mathematical translation from IPv6 to SNMA and L2 Multicast."""
        
        # 1. Math: Extract last 24 bits (last 6 hex characters) of the exploded IPv6
        clean_hex = target_ipv6.replace(":", "")
        last_24_bits = clean_hex[-6:]
        
        # 2. Math: Construct Solicited-Node Multicast Address (SNMA)
        # Prefix is strictly FF02:0000:0000:0000:0000:0001:FFxx:xxxx
        snma_ipv6 = f"FF02::1:FF{last_24_bits[:2]}:{last_24_bits[2:6]}"
        
        # 3. Math: Construct Layer 2 Multicast MAC
        # Prefix is strictly 33:33:FF:xx:xx:xx
        l2_multicast_mac = f"33:33:FF:{last_24_bits[:2]}:{last_24_bits[2:4]}:{last_24_bits[4:]}".upper()

        ndp_flow = []
        ndp_flow.append(f"1. [App Engine]: Wants to reach {target_ipv6}.")
        ndp_flow.append("2. [Network Stack]: IPv6 has no ARP. Triggering ICMPv6 NDP sequence.")
        ndp_flow.append(f"3. [Kernel]: Deriving Solicited-Node Multicast Address (SNMA)... -> {snma_ipv6.upper()}")
        ndp_flow.append(f"4. [Kernel]: Mapping SNMA to L2 Multicast MAC... -> {l2_multicast_mac}")
        ndp_flow.append(f"5. [Wire]: Transmitting ICMPv6 Type 135 (Neighbor Solicitation) to {l2_multicast_mac}.")
        ndp_flow.append("6. [Fabric]: Switches forward multicast frame. 99% of hosts drop it at the hardware NIC level.")
        ndp_flow.append("7. [Target Host]: NIC accepts frame. Replies with ICMPv6 Type 136 (Neighbor Advertisement).")

        insight = (
            "This is the death of ARP. By mathematically deriving a multicast group from the "
            "destination IP, IPv6 eliminates network-wide CPU interrupts. Furthermore, because "
            "NDP is just ICMPv6, it can be encrypted and authenticated natively using IPsec, "
            "closing the stateless vulnerabilities that plagued IPv4 for 40 years."
        )

        self.ndp_state = {
            "target": target_ipv6,
            "snma": snma_ipv6.upper(),
            "l2_mac": l2_multicast_mac,
            "flow": ndp_flow,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.ndp_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04V: IPV6 NDP (THE DEATH OF ARP) ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] HARDWARE MULTICAST DERIVATION:")
        print(f"     -> Exploded Target IPv6 : {state['target']}")
        print(f"     -> L3 SNMA (Multicast)  : {state['snma']}")
        print(f"     -> L2 MAC (Multicast)   : {state['l2_mac']}")
        print("-" * width)
        
        print(" [i] ICMPV6 NEIGHBOR DISCOVERY SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.3)
            print(f"     {step}")
        print("-" * width)
        
        print(f" [!] ARCHITECTURAL SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = IPv6NDPEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04V_IPV6_NDP_ICMPV6_TRANSITION INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Input Target IPv6 Address for Resolution:")
            
            ip_in = input("    Target IPv6 [Default: 2001:db8:acad:1::A] : ").strip() or "2001:db8:acad:1::A"
            if ip_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            target_ipv6 = engine.validate_ipv6(ip_in)
            
            engine.execute_ndp_physics(target_ipv6)
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