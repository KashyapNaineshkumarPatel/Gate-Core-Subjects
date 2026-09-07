"""
Core Logic: In a standard Ethernet frame carrying an ARP packet, there are actually 
two distinct sets of MAC addresses. 
1. The Layer 2 Ethernet Header (Source MAC, Destination MAC) used for physical switching.
2. The Layer 2.5 ARP Payload (Sender Hardware Address [SHA], Target Hardware Address).

Attackers running poorly written spoofing scripts (or basic tools like early versions 
of arpspoof) often forge the inner ARP Payload (SHA) to poison a victim's cache. 
However, they forget (or their raw socket implementation fails) to forge the outer 
Layer 2 Ethernet Header Source MAC, which defaults to their real physical NIC MAC.

Enterprise switches running Dynamic ARP Inspection (DAI) can enable an advanced strict 
payload validation feature: "ip arp inspection validate src-mac".

If this is enabled, the switch ASIC extracts the outer Ethernet Header MAC and compares 
it directly against the inner ARP Payload SHA. If they are not mathematically identical, 
the switch assumes it is a sloppy spoofing anomaly and instantly drops the packet in 
hardware, regardless of whether the IP matches the DHCP Snooping database.
"""

import sys
import shutil
import time
import re
from typing import Any, Dict

class ARPMismatchDropEngine:
    mismatch_state: Dict[str, Any]

    def __init__(self) -> None:
        self.mismatch_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def validate_mac(self, mac_input: str, name: str) -> str:
        cleaned = re.sub(r'[:\-\.\s]', '', mac_input).upper()
        if len(cleaned) != 12 or not all(c in '0123456789ABCDEF' for c in cleaned):
            raise ValueError(f"Syntax Error: Invalid MAC format for {name}. Expected 12 hex chars.")
        return ":".join([cleaned[i:i+2] for i in range(0, 12, 2)])

    def execute_mismatch_validation(self, eth_src: str, arp_sha: str) -> None:
        """Simulates DAI strict MAC payload validation in the switch ASIC."""
        
        flow = []
        flow.append("1. [Switch Ingress]: ARP Frame received on access port.")
        flow.append(f"2. [ASIC Decoder]: Parsing Layer 2 Ethernet Header Source MAC -> [ {eth_src} ]")
        flow.append(f"3. [ASIC Decoder]: Parsing Layer 2.5 ARP Payload Sender MAC (SHA) -> [ {arp_sha} ]")
        
        if eth_src == arp_sha:
            flow.append("4. [DAI Validation]: Ethernet L2 MAC perfectly matches ARP Payload SHA.")
            flow.append("5. [Switch Hardware]: Structural integrity check passed. Proceeding to IP validation.")
            action = "PERMITTED (MAC Match)"
            color = "SECURE - STRUCTURALLY SOUND"
            insight = "The packet is structurally valid. However, a highly sophisticated attacker who writes a custom raw socket script to spoof BOTH the Ethernet Header and the ARP Payload can bypass this specific check. This is why DHCP Snooping IP verification remains mandatory."
        else:
            flow.append("4. [DAI Validation]: MISMATCH DETECTED between L2 Outer Header and ARP Inner Payload.")
            flow.append("5. [Switch Hardware]: Frame flagged as anomalous/malicious.")
            flow.append("6. [Dataplane]: ASIC silently drops the frame before CPU interrupt.")
            action = "DROPPED (MAC Mismatch Violation)"
            color = "CRITICAL - PORT SECURITY TRIGGERED"
            insight = "This strict validation catches 'script kiddies' using basic tools like Ettercap or arpspoof without properly configuring their underlying Linux networking stack to forge the outer L2 frame. It is a zero-cost hardware check that prevents low-effort attacks."

        self.mismatch_state = {
            "eth_src": eth_src,
            "arp_sha": arp_sha,
            "flow": flow,
            "action": action,
            "color": color,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.mismatch_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04W: ARP MAC MISMATCH DROPPING ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] FRAME ENCAPSULATION DECODED:")
        print(f"     -> Outer Ethernet Src MAC : {state['eth_src']}")
        print(f"     -> Inner ARP Payload SHA  : {state['arp_sha']}")
        print("-" * width)
        
        print(" [i] HARDWARE ASIC VALIDATION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] SECURITY ENFORCEMENT OUTCOME:")
        time.sleep(0.3)
        print(f"     -> ASIC Action      : [ {state['action']} ]")
        print(f"     -> Fabric State     : {state['color']}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = ARPMismatchDropEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04W_ARP_MAC_MISMATCH_DROP INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Attacker Crafting ARP Packet:")
            print("    (Tip: Enter the same MAC for both to pass, or different MACs to trigger a Sloppy Spoof drop)")
            
            eth_in = input("    Outer Ethernet Src MAC  [Default: 11:22:33:44:55:66] : ").strip() or "11:22:33:44:55:66"
            if eth_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            arp_in = input("    Inner ARP Payload (SHA) [Default: DE:AD:BE:EF:00:11] : ").strip() or "DE:AD:BE:EF:00:11"
            
            eth_src = engine.validate_mac(eth_in, "Ethernet MAC")
            arp_sha = engine.validate_mac(arp_in, "ARP SHA")
            
            engine.execute_mismatch_validation(eth_src, arp_sha)
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