"""
Core Logic: When a user walks down a hallway while on a VoIP call, their device 
(STA) must mathematically decide to break its connection with Access Point 1 (AP1) 
and establish a connection with Access Point 2 (AP2).

The Layer 2 Routing Problem:
From the perspective of the upstream enterprise switch, the STA's MAC address is 
mapped to the physical switchport connected to AP1.
When the STA roams to AP2, the switch does NOT inherently know this. If the STA 
remains silent (e.g., listening to an audio stream but not transmitting), the 
switch will continue forwarding downstream packets to AP1, resulting in a traffic 
blackhole and dropped packets.

The 802.11r / WLC Solution:
Fast BSS Transition (802.11r) and Enterprise WLAN Controllers (WLCs) engineer a 
solution using forced Layer 2 updates. 
The millisecond the STA successfully associates with AP2, AP2 (or the WLC on its behalf) 
instantly injects a Gratuitous ARP (GARP) or an 802.11 Null Data Frame onto the 
wired backbone using the STA's Source MAC. 
The upstream switch receives this frame on AP2's port and instantly overwrites its 
Hardware CAM table. Downstream traffic is immediately steered to AP2.
"""

import sys
import shutil
import time
from typing import Any, Dict

class FastBSSTransitionEngine:
    roam_state: Dict[str, Any]

    def __init__(self) -> None:
        self.roam_state = {}
        
        # Network Topology Definitions
        self.sta_mac = "CC:CC:CC:99:99:99"
        self.sta_ip = "10.10.20.55"
        
        self.ap1_port = "GigabitEthernet1/0/1"
        self.ap2_port = "GigabitEthernet1/0/2"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_roam_physics(self, roam_type: str) -> None:
        """Simulates the L2 switch CAM update during an 802.11 roam."""
        
        flow = []
        
        # Initial State: STA is on AP1
        switch_cam = {self.sta_mac: self.ap1_port}
        
        flow.append(f"1. [Steady State]: STA {self.sta_mac} connected to AP1. Signal: -65 dBm.")
        flow.append(f"   -> Switch CAM Table : {self.sta_mac} maps to {switch_cam[self.sta_mac]}")
        flow.append("2. [Mobility Event]: User walks down the hall. AP1 signal drops to -82 dBm. AP2 seen at -60 dBm.")
        flow.append("3. [802.11 MAC]: STA executes Reassociation Request to AP2.")
        
        if roam_type == "1":
            # Legacy Roaming (No Forced Update)
            flow.append("4. [STA Logic]: Legacy roam complete. STA enters idle listening state (no TX).")
            flow.append(f"5. [Switch Fabric]: Upstream switch is UNAWARE of the roam.")
            flow.append(f"6. [Dataplane]: Incoming VoIP packets for {self.sta_ip} arrive at the switch.")
            flow.append(f"7. [Dataplane]: Switch forwards packets to {self.ap1_port} (AP1).")
            flow.append("8. [AP1]: Drops packets. Client is no longer associated.")
            
            action = "L2 BLACKHOLE (Asymmetric Topology)"
            color = "CRITICAL FAILURE - PACKET LOSS"
            insight = "In legacy roaming, the network relies on the client's next organic transmission to update the upstream switch's MAC table. If the client is just downloading or listening, traffic blackholes until a TCP ACK or Keepalive is finally sent."
            
        else:
            # 802.11r / WLC Managed Roam
            flow.append("4. [802.11r Logic]: Fast BSS Transition complete. 4-Way Handshake bypassed via PTK caching.")
            flow.append("5. [AP2 / WLC]: Detects successful association. Generates forced L2 Update.")
            flow.append(f"6. [AP2 Trunk]: Injects Gratuitous ARP (Src MAC: {self.sta_mac}) onto wired {self.ap2_port}.")
            
            # The Magic: CAM Table Update
            switch_cam[self.sta_mac] = self.ap2_port
            
            flow.append(f"7. [Switch Fabric]: Intercepts GARP. Detects MAC move from {self.ap1_port} to {self.ap2_port}.")
            flow.append("8. [Switch Fabric]: Hardware CAM table instantly overwritten in silicon.")
            flow.append(f"9. [Dataplane]: Incoming VoIP packets correctly steered to {self.ap2_port}. Zero packet loss.")
            
            action = "SEAMLESS ROAM (Hardware CAM Steered)"
            color = "NOMINAL - SUB-50ms TRANSITION"
            insight = "Enterprise mobility relies heavily on manipulating the wired L2 fabric. By having the infrastructure inject spoofed GARPs on behalf of the roaming client, the network heals the downstream routing path instantly, keeping latency under the strict 50ms VoIP threshold."

        self.roam_state = {
            "type": "Legacy Roam (No L2 Update)" if roam_type == "1" else "802.11r Fast BSS Transition",
            "cam_state": switch_cam,
            "flow": flow,
            "action": action,
            "color": color,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.roam_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AG: FAST BSS TRANSITION & L2 ROAMING ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] MOBILITY ARCHITECTURE : {state['type']}")
        print("-" * width)
        
        print(" [i] RF TO WIRED L2 EXECUTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] POST-ROAM WIRED TOPOLOGY STATE:")
        time.sleep(0.3)
        print(f"     -> Final Switch CAM : {self.sta_mac} -> {state['cam_state'][self.sta_mac]}")
        print(f"     -> Dataplane Status : [ {state['action']} ]")
        print(f"     -> Fabric Health    : {state['color']}")
        
        print("\n" + "-" * width)
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = FastBSSTransitionEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AG_FAST_BSS_TRANSITION_ARP INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select Wi-Fi Roaming Architecture:")
            print("    1. Legacy Standard Roam (Relies on organic client TX)")
            print("    2. 802.11r / Enterprise WLC Roam (Forced GARP Injection)")
            
            choice = input("    Select architecture (1/2) [Default: 2] : ").strip() or "2"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice not in ["1", "2"]:
                raise ValueError("Selection Error: Please choose 1 or 2.")
            
            engine.execute_roam_physics(choice)
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