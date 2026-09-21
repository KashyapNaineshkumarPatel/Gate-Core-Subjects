"""
Core Logic: Enterprise networks cannot rely on host OS kernels to defend against 
ARP spoofing. The defense must happen in the network hardware. Dynamic ARP Inspection 
(DAI) is a Cisco switch security feature that cryptographically locks down ARP.

DAI relies on a prerequisite feature: DHCP Snooping. 
When a host connects to the network and requests an IP via DHCP, the switch actively 
"snoops" the DHCP Server's reply. The switch builds a highly secure hardware database 
called the DHCP Snooping Binding Table (IP -> MAC -> Physical Port).

Once DAI is enabled:
1. Every access port is marked as "Untrusted" by default. (Uplinks to core routers 
   are manually configured as "Trusted").
2. When an ARP packet enters an Untrusted port, the switch ASIC traps it.
3. The switch extracts the Sender Protocol Address (IP) and Sender Hardware Address 
   (MAC) from the ARP payload.
4. It cross-references these values against the hardware DHCP Binding Table.
5. If the Sender IP and MAC perfectly match the database for that specific physical 
   port, the ARP packet is permitted. 
6. If a malicious user manually changes their IP or crafts a forged ARP Reply, 
   the values will not match the DHCP database. The switch instantly drops the 
   frame, logs a security violation, and can put the port into "err-disable".
"""

import sys
import shutil
import time
import ipaddress
import re
from typing import Any, Dict

class DynamicARPInspectionEngine:
    dai_state: Dict[str, Any]

    def __init__(self) -> None:
        self.dai_state = {}
        
        # Simulated Hardware DHCP Snooping Binding Database
        self.dhcp_binding_table = {
            "FastEthernet0/1": {"ip": "10.0.0.50", "mac": "00:11:22:33:44:55", "vlan": 10},
            "FastEthernet0/2": {"ip": "10.0.0.51", "mac": "AA:BB:CC:DD:EE:FF", "vlan": 10},
            "GigabitEthernet0/1": {"ip": "10.0.0.200", "mac": "00:50:56:AB:CD:EF", "vlan": 20}
        }
        
        # Switchport Trust States
        self.port_trust = {
            "FastEthernet0/1": "UNTRUSTED",
            "FastEthernet0/2": "UNTRUSTED",
            "GigabitEthernet0/1": "UNTRUSTED",
            "GigabitEthernet1/1": "TRUSTED" # Uplink to Core Network / DHCP Server
        }

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            ipaddress.IPv4Address(ip_input.strip())
            return ip_input.strip()
        except ValueError:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv4 address format.")

    def validate_mac(self, mac_input: str, name: str) -> str:
        cleaned = re.sub(r'[:\-\.\s]', '', mac_input).upper()
        if len(cleaned) != 12 or not all(c in '0123456789ABCDEF' for c in cleaned):
            raise ValueError(f"Syntax Error: Invalid MAC format for {name}. Expected 12 hex chars.")
        return ":".join([cleaned[i:i+2] for i in range(0, 12, 2)])

    def execute_dai_inspection(self, ingress_port: str, sender_ip: str, sender_mac: str) -> None:
        """Simulates the hardware DAI validation and enforcement logic."""
        
        inspection_flow = []
        action = ""
        insight = ""
        violation = False

        inspection_flow.append(f"1. [Switch Ingress]: ARP Frame received on physical port {ingress_port}.")
        
        trust_state = self.port_trust.get(ingress_port, "UNTRUSTED")
        inspection_flow.append(f"2. [Switch Logic]: Port Trust State evaluated -> {trust_state}.")

        if trust_state == "TRUSTED":
            inspection_flow.append("3. [DAI Engine]: Trusted port bypasses deep packet inspection. Frame permitted.")
            action = "PERMITTED (Trusted Uplink)"
            insight = "Trunk links to core routers or trusted DHCP servers are exempt from DAI to prevent dropping legitimate infrastructure traffic."
        else:
            inspection_flow.append("3. [DAI Engine]: Untrusted port. Trapping frame to Control Plane for inspection.")
            inspection_flow.append(f"4. [DAI Engine]: Extracting payload -> SPA: {sender_ip}, SHA: {sender_mac}")
            
            # Cross-reference DHCP Binding Table
            binding = self.dhcp_binding_table.get(ingress_port)
            
            if not binding:
                inspection_flow.append(f"5. [DAI Engine]: Database lookup... NO DHCP binding found for {ingress_port}.")
                inspection_flow.append("6. [DAI Engine]: Security Violation (Silent Host / Static IP). Frame dropped.")
                action = "DROPPED (No Binding Table Entry)"
                violation = True
                insight = "If a user sets a static IP on a DAI-enabled port without a DHCP lease, their traffic is dropped. Admins must configure static 'ARP Access-Lists' for legacy servers."
            
            elif binding["ip"] == sender_ip and binding["mac"] == sender_mac:
                inspection_flow.append(f"5. [DAI Engine]: Database lookup... MATCH FOUND in Hardware Binding Table.")
                inspection_flow.append("6. [DAI Engine]: Payload integrity verified. Frame forwarded to physical fabric.")
                action = "PERMITTED (Binding Match)"
                insight = "This mathematically eliminates basic ARP cache poisoning. The attacker cannot forge the IP/MAC payload without tripping the ASIC hardware verification."
            
            else:
                inspection_flow.append(f"5. [DAI Engine]: Database lookup... MISMATCH DETECTED!")
                inspection_flow.append(f"   -> Expected : IP {binding['ip']}, MAC {binding['mac']}")
                inspection_flow.append(f"   -> Received : IP {sender_ip}, MAC {sender_mac}")
                inspection_flow.append("6. [DAI Engine]: Spoofing attack detected. Frame dropped. Syslog generated.")
                action = "DROPPED & LOGGED (Spoofing Attempt)"
                violation = True
                insight = "In high-security enterprise environments, DAI violations trigger an 'err-disable' state, automatically shutting down the physical switch port to quarantine the attacker."

        self.dai_state = {
            "port": ingress_port,
            "sender_ip": sender_ip,
            "sender_mac": sender_mac,
            "flow": inspection_flow,
            "action": action,
            "violation": violation,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.dai_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04U: DYNAMIC ARP INSPECTION (DAI) ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] HARDWARE DHCP SNOOPING BINDING TABLE:")
        for port, data in self.dhcp_binding_table.items():
            print(f"     -> {port:<19} | IP: {data['ip']:<14} | MAC: {data['mac']}")
        print("-" * width)
        
        print(f" [i] HARDWARE ASIC INSPECTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] SECURITY ENFORCEMENT OUTCOME:")
        time.sleep(0.3)
        color = "CRITICAL - PORT QUARANTINE" if state['violation'] else "NOMINAL - SECURE FORWARDING"
        print(f"     -> Dataplane Action : [ {state['action']} ]")
        print(f"     -> Fabric State     : {color}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = DynamicARPInspectionEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04U_CISCO_DAI_DHCP_SNOOPING INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Ingress ARP Frame:")
            print("    (Tip: Use FastEthernet0/1 with 10.0.0.50 / 00:11:22:33:44:55 for a pass, or alter IP/MAC for a drop)")
            
            port_in = input("    Ingress Switch Port [Default: FastEthernet0/1] : ").strip() or "FastEthernet0/1"
            if port_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            ip_in = input("    Sender IP (Payload) [Default: 10.0.0.50]       : ").strip() or "10.0.0.50"
            mac_in = input("    Sender MAC (Payload)[Default: AA:BB:CC:DD:11:11]: ").strip() or "AA:BB:CC:DD:11:11"
            
            sender_ip = engine.validate_ip(ip_in, "Sender IP")
            sender_mac = engine.validate_mac(mac_in, "Sender MAC")
            
            engine.execute_dai_inspection(port_in, sender_ip, sender_mac)
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