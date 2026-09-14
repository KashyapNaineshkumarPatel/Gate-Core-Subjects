"""
Core Logic: Network Address Translation (NAT) fundamentally breaks the end-to-end 
Layer 3 IP model. Because the IP headers are rewritten mid-flight, the firewall 
must completely decouple the external Layer 2 broadcast domain from the internal 
Layer 2 broadcast domain.

The NAT / Proxy ARP Dependency:
A classic enterprise misconfiguration is creating a Destination NAT (Port Forwarding) 
rule for a public IP (e.g., 203.0.113.50) to an internal server (10.1.1.50). 
The engineer creates the security policy and the NAT policy, but traffic fails.

Why? Because the ISP router sends an ARP Request on the WAN wire: "Who has 203.0.113.50?"
If the firewall is not explicitly configured to execute Proxy ARP for the NAT pool 
IP addresses, the firewall stays silent. The ISP router's ARP fails, and the 
TCP packets are dropped before they ever reach the firewall's ingress interface.

When correctly configured, NAT relies heavily on Proxy ARP on the outside, and 
standard ARP on the inside, completely regenerating the L2 Ethernet frame.
"""

import sys
import shutil
import time
from typing import Any, Dict

class ARPNATTraversalEngine:
    nat_state: Dict[str, Any]

    def __init__(self) -> None:
        self.nat_state = {}
        
        # Firewall Interfaces
        self.fw_wan_ip = "203.0.113.1"
        self.fw_wan_mac = "FW:AA:AA:AA:AA:AA"
        
        self.fw_lan_ip = "10.1.1.1"
        self.fw_lan_mac = "FW:BB:BB:BB:BB:BB"
        
        # NAT Pool & Internal Server
        self.dnat_public_vip = "203.0.113.50"
        self.internal_server_ip = "10.1.1.50"
        self.internal_server_mac = "SRV:00:11:22:33:44"
        
        # ISP Router (The Internet)
        self.isp_router_ip = "203.0.113.254"
        self.isp_router_mac = "ISP:99:99:99:99:99"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_nat_physics(self, proxy_arp_enabled: bool) -> None:
        """Simulates the dual-ARP resolution required for a DNAT inbound connection."""
        
        flow = []
        frames = []
        action = ""
        insight = ""
        
        flow.append(f"1. [Internet]: Client attempts TCP connection to Public VIP {self.dnat_public_vip}.")
        flow.append(f"2. [ISP Router]: Needs to route frame. Generates ARP Broadcast -> 'Who has {self.dnat_public_vip}?'")
        
        if not proxy_arp_enabled:
            flow.append("3. [Firewall WAN]: Receives ARP Request. Target IP does not match WAN interface IP.")
            flow.append("4. [Firewall WAN]: PROXY ARP DISABLED. Firewall drops request.")
            flow.append("5. [ISP Router]: ARP Timeout. Drops TCP SYN packet.")
            
            action = "L2 RESOLUTION FAILED (Traffic Blackholed)"
            insight = "NAT policies only manipulate Layer 3. If the firewall's WAN interface doesn't logically claim ownership of the public NAT IP at Layer 2 via Proxy ARP, the ISP upstream router cannot physically deliver the frame to the firewall. The connection dies on the ISP's hardware."
            
            frame = {
                "stage": "WAN Ingress Attempt",
                "l3": f"Src: Internet Client -> Dst: {self.dnat_public_vip}",
                "l2": f"Src: {self.isp_router_mac} -> Dst: INCOMPLETE (ARP Failed)",
                "status": "DROPPED BY ISP ROUTER"
            }
            frames.append(frame)
            
        else:
            flow.append("3. [Firewall WAN]: Receives ARP Request. Target IP matches active DNAT policy.")
            flow.append(f"4. [Firewall WAN]: PROXY ARP ENABLED. Synthesizes Reply -> '{self.dnat_public_vip} is at {self.fw_wan_mac}'.")
            flow.append("5. [ISP Router]: ARP Cache updated. Transmits L2 frame to Firewall WAN MAC.")
            
            frame_1 = {
                "stage": "WAN Ingress (Pre-NAT)",
                "l3": f"Src: Internet Client -> Dst: {self.dnat_public_vip}",
                "l2": f"Src: {self.isp_router_mac} -> Dst: {self.fw_wan_mac}",
                "status": "DELIVERED TO FIREWALL"
            }
            frames.append(frame_1)
            
            flow.append("\n   --- NAT ENGINE PROCESSING ---")
            flow.append("6. [Firewall CPU]: Strips WAN L2 Header.")
            flow.append(f"7. [NAT Engine]: Matches DNAT Rule. Rewriting Dest IP: {self.dnat_public_vip} -> {self.internal_server_ip}.")
            flow.append("8. [Route Engine]: Performs lookup for internal IP. Egress interface is LAN.")
            
            flow.append(f"\n   --- LAN EGRESS RESOLUTION ---")
            flow.append(f"9. [Firewall LAN]: Generates ARP Request -> 'Who has {self.internal_server_ip}?'")
            flow.append(f"10. [Internal Server]: Replies -> '{self.internal_server_ip} is at {self.internal_server_mac}'.")
            flow.append("11. [Firewall LAN]: Encapsulates translated L3 packet in NEW L2 LAN Header. Transmits to Server.")
            
            frame_2 = {
                "stage": "LAN Egress (Post-NAT)",
                "l3": f"Src: Internet Client -> Dst: {self.internal_server_ip}",
                "l2": f"Src: {self.fw_lan_mac} -> Dst: {self.internal_server_mac}",
                "status": "DELIVERED TO INTERNAL SERVER"
            }
            frames.append(frame_2)
            
            action = "END-TO-END DNAT TRAVERSAL SUCCESS"
            insight = "NAT acts as an absolute Layer 2 boundary. The packet experiences two completely isolated ARP lifecycles: the external Proxy ARP (tricking the ISP), and the internal standard ARP (finding the real server). The L2 frames on the WAN and LAN share zero common metadata."

        self.nat_state = {
            "proxy_arp": proxy_arp_enabled,
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.nat_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AS: ARP NAT TRAVERSAL & PROXY BOUNDARY ENGINE ".center(width))
        print("=" * width)
        
        status_text = "ENABLED" if state['proxy_arp'] else "DISABLED (Misconfiguration)"
        print(f" [+] FIREWALL NAT CONFIGURATION:")
        print(f"     -> DNAT Policy      : {self.dnat_public_vip} (Public) -> {self.internal_server_ip} (Private)")
        print(f"     -> WAN Proxy ARP    : {status_text}")
        print("-" * width)
        
        print(" [i] DATAPLANE RESOLUTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.1)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] LAYER 2 & LAYER 3 ENCAPSULATION STATES:")
        time.sleep(0.3)
        for frame in state['frames']:
            print(f"\n     [{frame['stage']}]")
            print(f"     Layer 3 : {frame['l3']}")
            print(f"     Layer 2 : {frame['l2']}")
            print(f"     Status  : {frame['status']}")
            time.sleep(0.3)
        
        print("\n" + "-" * width)
        print(f"     -> Network Action : [ {state['action']} ]")
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = ARPNATTraversalEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AS_ARP_NAT_TRAVERSAL INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Inbound DNAT Connection:")
            print("    1. Disable Proxy ARP on WAN (Classic beginner misconfiguration)")
            print("    2. Enable Proxy ARP on WAN (Correct Enterprise configuration)")
            
            choice = input("    Select configuration (1/2) [Default: 2] : ").strip() or "2"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice not in ["1", "2"]:
                raise ValueError("Selection Error: Please choose 1 or 2.")
            
            proxy_arp = (choice == "2")
            engine.execute_nat_physics(proxy_arp)
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