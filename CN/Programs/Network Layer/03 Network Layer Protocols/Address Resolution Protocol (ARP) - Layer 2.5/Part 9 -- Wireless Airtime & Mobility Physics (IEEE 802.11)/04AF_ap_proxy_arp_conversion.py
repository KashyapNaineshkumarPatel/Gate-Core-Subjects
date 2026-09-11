"""
Core Logic: To solve the 802.11 Broadcast Penalty demonstrated in Module 04AE, 
Enterprise WLAN Controllers (Cisco, Aruba) employ AP Proxy ARP and Broadcast-to-Unicast 
(B2U) Conversion.

When an Access Point (AP) is deployed in an enterprise environment, it snoops DHCP 
and 802.1X authentications to build a strict internal "Client Binding Table" 
(IP -> MAC -> Power State).

The Physics of Airtime Conservation:
1. Client A sends an ARP Broadcast: "Who has 10.1.1.50?"
2. The AP's hardware radio intercepts the broadcast and STOPS it from echoing over 
   the air at the 1 Mbps Lowest Basic Rate.
3. The AP checks its Client Binding Table.
4. SCENARIO A (Target Active): The AP converts the Broadcast frame into a Unicast 
   frame directed specifically to 10.1.1.50. It transmits this at 300 Mbps.
5. SCENARIO B (Target Sleeping): If the target is an IoT device or smartphone in 
   802.11 Power Save Mode, the AP simply acts as a Proxy. It generates the ARP 
   Reply itself using the target's MAC, allowing the target to stay asleep and 
   saving massive amounts of battery and RF airtime.
"""

import sys
import shutil
import time
import ipaddress
from typing import Any, Dict

class APProxyARPConversionEngine:
    conversion_state: Dict[str, Any]

    def __init__(self) -> None:
        self.conversion_state = {}
        
        # Enterprise AP Internal Client Binding Table
        self.client_table = {
            "10.1.1.50": {"mac": "AA:AA:AA:11:11:11", "state": "AWAKE", "mcs_rate": "300 Mbps"},
            "10.1.1.51": {"mac": "BB:BB:BB:22:22:22", "state": "POWER_SAVE", "mcs_rate": "866 Mbps"},
            "10.1.1.1":  {"mac": "CC:CC:CC:33:33:33", "state": "WIRED_GATEWAY", "mcs_rate": "N/A"}
        }
        self.ap_mac = "AP:00:11:22:33:44"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            ipaddress.IPv4Address(ip_input.strip())
            return ip_input.strip()
        except ValueError:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv4 address.")

    def execute_ap_interception(self, sender_ip: str, target_ip: str) -> None:
        """Simulates AP intercepting and manipulating L2 broadcasts."""
        
        flow = []
        frames = []
        action = ""
        insight = ""
        
        flow.append(f"1. [Sender {sender_ip}]: Generates ARP Broadcast -> 'Who has {target_ip}?'")
        flow.append("2. [Access Point]: ASIC intercepts L2 Broadcast. Suppresses 1 Mbps wireless transmission.")
        
        target = self.client_table.get(target_ip)
        
        if not target:
            flow.append(f"3. [AP Logic]: Target IP {target_ip} not found in Client Binding Table.")
            flow.append("4. [AP Logic]: Fallback mechanism. Dropping frame to protect RF airtime (Strict Mode).")
            action = "DROPPED (Unknown Target)"
            insight = "In strict enterprise deployments, if the AP does not know the IP from a valid DHCP transaction, it drops the ARP to prevent network scanning and broadcast storms."
            
        elif target["state"] == "AWAKE":
            flow.append(f"3. [AP Logic]: Target found. State: {target['state']}.")
            flow.append(f"4. [AP Logic]: Executing Broadcast-to-Unicast (B2U) Conversion.")
            flow.append(f"5. [AP Radio]: Transmitting Unicast ARP frame at {target['mcs_rate']}.")
            
            frame = {
                "stage": "B2U Converted Frame (Air Interface)",
                "l3_src": sender_ip, "l3_dst": target_ip,
                "l2_src": self.ap_mac, "l2_dst": target['mac'],
                "tx_rate": target['mcs_rate']
            }
            frames.append(frame)
            
            action = "BROADCAST-TO-UNICAST (Airtime Saved)"
            insight = "By rewriting the Destination MAC from FF:FF:FF:FF:FF:FF to the specific client's MAC, the AP can legally transmit the frame at the client's peak MCS rate (e.g., 300 Mbps) instead of the 1 Mbps basic rate."
            
        elif target["state"] == "POWER_SAVE":
            flow.append(f"3. [AP Logic]: Target found. State: {target['state']}.")
            flow.append("4. [AP Logic]: Target is asleep. Waking it up for ARP is a waste of battery.")
            flow.append(f"5. [AP Logic]: Executing Proxy ARP on behalf of {target_ip}.")
            flow.append(f"6. [AP Radio]: Transmitting ARP Reply directly to Sender {sender_ip}.")
            
            frame = {
                "stage": "Proxy ARP Reply (Air Interface)",
                "l3_src": target_ip, "l3_dst": sender_ip,
                "l2_src": target['mac'], "l2_dst": "SENDER_MAC",
                "tx_rate": "Sender's MCS Rate"
            }
            frames.append(frame)
            
            action = "PROXY ARP REPLY (Battery & Airtime Saved)"
            insight = "Smartphones sleep their Wi-Fi radios to save battery. If the AP woke them up for every ambient ARP broadcast on a crowded subnet, phones would die in hours. Proxy ARP allows the AP to lie to the network on the phone's behalf."

        else:
            flow.append(f"3. [AP Logic]: Target found. State: {target['state']}.")
            flow.append("4. [AP Logic]: Bridging frame directly to the wired Ethernet trunk.")
            action = "ETHERNET BRIDGING"
            insight = "Traffic destined for the Default Gateway is simply dumped onto the wired fabric where broadcast penalties do not exist."

        self.conversion_state = {
            "sender": sender_ip,
            "target": target_ip,
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.conversion_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AF: AP PROXY ARP & B2U CONVERSION ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] AP CLIENT BINDING TABLE (SNOOPED STATE):")
        for ip, data in self.client_table.items():
            print(f"     -> {ip:<12} | MAC: {data['mac']} | State: {data['state']:<12} | Rate: {data['mcs_rate']}")
        print("-" * width)
        
        print(" [i] 802.11 ARP INTERCEPTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        if state['frames']:
            print(" [!] CONVERTED DATAPLANE FRAMES:")
            time.sleep(0.3)
            for frame in state['frames']:
                print(f"\n     [{frame['stage']}]")
                print(f"     L2 Source MAC : {frame['l2_src']:<19} | TX Rate: {frame['tx_rate']}")
                print(f"     L2 Dest MAC   : {frame['l2_dst']}")
            print("-" * width)
            
        print(f" [!] ARCHITECTURAL ENGINEERING OUTCOME: [ {state['action']} ]")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = APProxyARPConversionEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AF_AP_PROXY_ARP_CONVERSION INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Wireless Client ARP Request:")
            print("    (Tip: Target 10.1.1.50 for B2U Unicast, or 10.1.1.51 to trigger Power Save Proxy)")
            
            sender_in = input("    Sender IP Address [Default: 10.1.1.100] : ").strip() or "10.1.1.100"
            if sender_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            target_in = input("    Target IP Address [Default: 10.1.1.51]  : ").strip() or "10.1.1.51"
            
            sender_ip = engine.validate_ip(sender_in, "Sender IP")
            target_ip = engine.validate_ip(target_in, "Target IP")
            
            engine.execute_ap_interception(sender_ip, target_ip)
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