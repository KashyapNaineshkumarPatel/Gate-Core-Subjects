"""
Core Logic: Standard ARP is a reactive request/reply protocol used to find an unknown MAC. 
But what if a host wants to update the network proactively? This is where Gratuitous ARP (GARP) 
and RFC 5227 (Address Conflict Detection - ACD) come in.

1. Address Conflict Detection (ACD): When a machine boots up, how does it know no one else 
   is already using its IP address? It sends an "ARP Probe". 
   - ARP Probe: Sender IP is strictly 0.0.0.0. Target IP is the desired IP. 
   If another machine replies, an IP conflict is detected, and the OS disables the interface.
   If there is no reply, it sends an "ARP Announcement" (GARP) claiming the IP.

2. Gratuitous ARP (HA Failover): In a High Availability (HA) cluster, two firewalls share a 
   Virtual IP (VIP). If Firewall A dies, Firewall B assumes the VIP. But the network's switches 
   and host ARP caches still map the VIP to Firewall A's MAC. 
   Firewall B instantly blasts a Gratuitous ARP (Sender IP = VIP, Target IP = VIP). 
   This unsolicited broadcast forces every switch to update its CAM table and every host 
   to overwrite its ARP cache, instantly healing the network.
"""

import sys
import shutil
import time
import socket
import re
from typing import Any, Dict

class GratuitousARPEngine:
    garp_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.garp_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            socket.inet_aton(ip_input.strip())
            return ip_input.strip()
        except socket.error:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv4 address.")

    def validate_mac(self, mac_input: str, name: str) -> str:
        cleaned = re.sub(r'[:\-\.\s]', '', mac_input).upper()
        if len(cleaned) != 12 or not all(c in '0123456789ABCDEF' for c in cleaned):
            raise ValueError(f"Syntax Error: Invalid MAC format for {name}. Expected 12 hex chars.")
        return ":".join([cleaned[i:i+2] for i in range(0, 12, 2)])

    def execute_garp_acd(self, mode: str, target_ip: str, target_mac: str, conflict_exists: bool) -> None:
        """Simulates RFC 5227 Address Conflict Detection and HA GARP logic."""
        
        transaction_log = []
        final_status = ""
        insight = ""

        if mode == "1":
            # Mode 1: ACD (Boot Sequence)
            phase = "RFC 5227 Address Conflict Detection (ACD)"
            
            # ARP Probe
            transaction_log.append({
                "step": "ARP PROBE",
                "spa": "0.0.0.0",
                "tpa": target_ip,
                "sha": target_mac,
                "action": "Host broadcasts probe to check if IP is in use. SPA is zeroed to avoid poisoning caches."
            })
            
            if conflict_exists:
                transaction_log.append({
                    "step": "CONFLICT DETECTED",
                    "spa": target_ip,
                    "tpa": "0.0.0.0",
                    "sha": "AA:BB:CC:DD:EE:FF (Rogue)",
                    "action": "Another host replied! The IP is already in use."
                })
                final_status = "INTERFACE DISABLED (IP CONFLICT)"
                insight = "By strictly using SPA 0.0.0.0 for probes, RFC 5227 guarantees that if a conflict exists, the probing host won't accidentally corrupt the network's active ARP caches before giving up."
            else:
                # ARP Announcement (GARP)
                transaction_log.append({
                    "step": "ARP ANNOUNCEMENT (GARP)",
                    "spa": target_ip,
                    "tpa": target_ip,
                    "sha": target_mac,
                    "action": "No reply to probe. Host broadcasts GARP to officially claim the IP."
                })
                final_status = "IP ACQUIRED & ANNOUNCED"
                insight = "The ARP Announcement is a Gratuitous ARP (SPA == TPA). It mathematically forces neighboring switches to update their MAC tables, ensuring immediate reachability."
                
        elif mode == "2":
            # Mode 2: High Availability Failover
            phase = "High Availability (HA) VIP Failover"
            
            transaction_log.append({
                "step": "NODE FAILURE DETECTED",
                "spa": "N/A",
                "tpa": "N/A",
                "sha": "N/A",
                "action": "Active Firewall died. Standby Firewall transitions to Active."
            })
            
            transaction_log.append({
                "step": "GRATUITOUS ARP (GARP) INJECTION",
                "spa": target_ip,
                "tpa": target_ip,
                "sha": target_mac,
                "action": "Standby firewall broadcasts GARP to steal the VIP routing."
            })
            
            final_status = "NETWORK CACHES OVERWRITTEN"
            insight = "Without GARP, hosts would continue sending packets to the dead firewall's MAC address until their STALE timers expired (minutes/hours). GARP heals the network in milliseconds."

        self.garp_state = {
            "phase": phase,
            "target_ip": target_ip,
            "target_mac": target_mac,
            "transactions": transaction_log,
            "status": final_status,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.garp_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04H: ACD & GRATUITOUS ARP FAILOVER ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] ACTIVE SCENARIO: {state['phase']}")
        print(f"     -> Target/Virtual IP : {state['target_ip']}")
        print(f"     -> Acting MAC Address: {state['target_mac']}")
        print("-" * width)
        
        print(" [i] PACKET TRANSACTION SEQUENCE:")
        for t in state['transactions']:
            time.sleep(0.4)
            print(f"     -> [ {t['step']} ]")
            if t['spa'] != 'N/A':
                print(f"        SPA: {t['spa']:<15} | TPA: {t['tpa']}")
                print(f"        SHA: {t['sha']}")
            print(f"        Log: {t['action']}")
            print("        -")
            
        print("-" * width)
        print(" [!] FINAL NETWORK STATE:")
        time.sleep(0.3)
        print(f"     -> Outcome           : [ {state['status']} ]")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = GratuitousARPEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04H_RFC5227_ACD_GRATUITOUS_FAILOVER INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select ARP Scenario:")
            print("    1. Host Boot Sequence (Address Conflict Detection)")
            print("    2. HA Cluster Failover (VIP Takeover)")
            mode_in = input("    Choice (1/2) [Default: 1] : ").strip() or "1"
            if mode_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            ip_in = input("    Target IPv4 / VIP [Default: 10.0.0.254]   : ").strip() or "10.0.0.254"
            mac_in = input("    Hardware MAC Address [Default: 11:22:33:44:55:66]: ").strip() or "11:22:33:44:55:66"
            
            conflict_exists = False
            if mode_in == "1":
                conf_in = input("    Simulate IP Conflict? (Y/N) [Default: N]  : ").strip().upper() or "N"
                conflict_exists = (conf_in == "Y")
            
            target_ip = engine.validate_ip(ip_in, "Target IP")
            target_mac = engine.validate_mac(mac_in, "MAC Address")
            
            if mode_in not in ["1", "2"]:
                raise ValueError("Selection Error: Please choose scenario 1 or 2.")
            
            engine.execute_garp_acd(mode_in, target_ip, target_mac, conflict_exists)
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