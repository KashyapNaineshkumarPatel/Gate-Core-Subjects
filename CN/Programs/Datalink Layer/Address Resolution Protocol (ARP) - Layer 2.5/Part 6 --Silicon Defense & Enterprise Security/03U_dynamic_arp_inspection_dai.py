"""
Core Logic: Relying on OS kernels to defend against ARP spoofing is structurally 
flawed. Host machines process traffic in software (Ring 3/Ring 0), which is too slow 
and vulnerable to race conditions or eBPF hooks. True defense must occur in silicon, 
at the access switch layer.

Dynamic ARP Inspection (DAI) is a hardware-level security feature. It utilizes 
Application-Specific Integrated Circuits (ASICs) to intercept and validate every 
ARP payload before it is forwarded to the fabric.

DAI depends on the 'DHCP Snooping Binding Database'. When a host gets an IP via DHCP, 
the switch snoops the transaction and securely maps [Physical Port -> IP -> MAC] 
in hardware memory. 

DAI Rules of Engagement:
1. Ports are divided into TRUSTED (Uplinks to Core/DHCP Servers) and UNTRUSTED (Access ports).
2. ARP packets on TRUSTED ports bypass inspection (forwarded at wire-speed).
3. ARP packets on UNTRUSTED ports are trapped to the switch CPU/Control Plane.
4. The Sender IP (SPA) and Sender MAC (SHA) in the ARP payload are extracted.
5. The ASIC cross-references the Payload against the DHCP Binding Database for that specific port.
6. MATCH: The packet is forwarded.
7. MISMATCH: The packet is instantly dropped. A syslog is generated, and the port 
   may be placed into 'err-disable' (Hardware Quarantine).
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
        
        # Simulated Hardware Memory: DHCP Snooping Binding Table (Built organically by the switch)
        self.dhcp_binding_table = {
            "FastEthernet0/1": {"ip": "10.0.10.50", "mac": "00:11:22:33:44:55", "vlan": 10, "lease": "86400s"},
            "FastEthernet0/2": {"ip": "10.0.10.51", "mac": "AA:BB:CC:DD:EE:FF", "vlan": 10, "lease": "86400s"},
            "GigabitEthernet0/1": {"ip": "10.0.20.100", "mac": "00:50:56:AB:CD:EF", "vlan": 20, "lease": "STATIC_ACL"}
        }
        
        # Switchport Trust Boundaries (Configured by Network Engineer)
        self.port_trust = {
            "FastEthernet0/1": "UNTRUSTED",
            "FastEthernet0/2": "UNTRUSTED",
            "GigabitEthernet0/1": "UNTRUSTED",
            "TenGigabitEthernet1/1": "TRUSTED"  # Core Uplink / Path to DHCP Server
        }

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            ipaddress.IPv4Address(ip_input.strip())
            return ip_input.strip()
        except ValueError:
            raise ValueError(f"Syntax Error: {name} must be a valid IPv4 address (e.g., 10.0.10.50).")

    def validate_mac(self, mac_input: str, name: str) -> str:
        cleaned = re.sub(r'[:\-\.\s]', '', mac_input).upper()
        if len(cleaned) != 12 or not all(c in '0123456789ABCDEF' for c in cleaned):
            raise ValueError(f"Syntax Error: Invalid MAC format for {name}. Expected 12 hex chars.")
        return ":".join([cleaned[i:i+2] for i in range(0, 12, 2)])

    def execute_dai_inspection(self, ingress_port: str, sender_ip: str, sender_mac: str) -> None:
        """Simulates the hardware ASIC DAI validation and enforcement logic."""
        
        inspection_flow = []
        action = ""
        insight = ""
        violation = False

        inspection_flow.append(f"1. [ASIC Ingress]: Frame received on physical interface {ingress_port}.")
        
        # 1. Check Port Trust State
        trust_state = self.port_trust.get(ingress_port, "UNTRUSTED")
        inspection_flow.append(f"2. [Port Security]: Interface Trust Boundary evaluated -> [ {trust_state} ].")

        if trust_state == "TRUSTED":
            inspection_flow.append("3. [DAI Engine]: Trusted port logic engaged. Bypassing payload inspection.")
            inspection_flow.append("4. [Fabric]: Frame forwarded to backplane at wire-speed.")
            action = "PERMITTED (Trusted Uplink)"
            insight = "Trunk links to core routers or hypervisors are often trusted to prevent catastrophic drops of legitimate infrastructure traffic, relying on upstream security."
        else:
            inspection_flow.append("3. [DAI Engine]: Untrusted port detected. Trapping ARP frame to Control Plane.")
            inspection_flow.append(f"4. [DAI Engine]: Deep Packet Inspection... SPA: {sender_ip}, SHA: {sender_mac}")
            
            # 2. Hardware Database Lookup
            binding = self.dhcp_binding_table.get(ingress_port)
            
            if not binding:
                inspection_flow.append(f"5. [Hardware TCAM]: Querying DHCP Snooping Database for {ingress_port}... MISS.")
                inspection_flow.append("6. [DAI Engine]: Security Violation (Silent Host / Unauthorized Static IP).")
                action = "DROPPED (No Binding Entry)"
                violation = True
                insight = "If a user unplugs their corporate laptop, plugs in a rogue device, and statically assigns an IP, DAI immediately drops the traffic because no DHCP transaction was snooped to authorize it."
            
            elif binding["ip"] == sender_ip and binding["mac"] == sender_mac:
                inspection_flow.append(f"5. [Hardware TCAM]: Querying DHCP Snooping Database... MATCH FOUND.")
                inspection_flow.append("6. [DAI Engine]: Cryptographic integrity verified against physical topology.")
                action = "PERMITTED (Binding Match)"
                insight = "This mathematically eliminates traditional ARP cache poisoning (MitM). The attacker cannot forge the IP/MAC payload without tripping the ASIC hardware verification tied to their specific physical port."
            
            else:
                inspection_flow.append(f"5. [Hardware TCAM]: Querying DHCP Snooping Database... MISMATCH DETECTED!")
                inspection_flow.append(f"   -> DB Expected : IP {binding['ip']}, MAC {binding['mac']}")
                inspection_flow.append(f"   -> Wire Payload: IP {sender_ip}, MAC {sender_mac}")
                inspection_flow.append("6. [DAI Engine]: Spoofing attack detected! Packet dropped in silicon.")
                action = "DROPPED & LOGGED (Spoofing Attempt)"
                violation = True
                insight = "In high-security enterprise environments, this specific violation triggers an 'err-disable' state, instantly shutting down the physical switch port to quarantine the attacker's machine from the fabric."

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
        print(" [>] MODULE 04U: DYNAMIC ARP INSPECTION (DAI) SILICON ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] HARDWARE DHCP SNOOPING BINDING TABLE (TCAM):")
        for port, data in self.dhcp_binding_table.items():
            print(f"     -> {port:<19} | IP: {data['ip']:<14} | MAC: {data['mac']}")
        print("-" * width)
        
        print(f" [i] ASIC INSPECTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] SECURITY ENFORCEMENT OUTCOME:")
        time.sleep(0.3)
        color = "CRITICAL - PORT QUARANTINE / SYS-LOGGED" if state['violation'] else "NOMINAL - SECURE L2 FORWARDING"
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
    print(" 04U_DYNAMIC_ARP_INSPECTION_DAI INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Ingress ARP Frame from Access Layer:")
            print("    (Tip: Use FastEthernet0/1 with 10.0.10.50 / 00:11:22:33:44:55 for a pass, or alter IP/MAC for a violation)")
            
            port_in = input("    Ingress Switch Port [Default: FastEthernet0/1] : ").strip() or "FastEthernet0/1"
            if port_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            ip_in = input("    Sender IP (Payload) [Default: 10.0.10.50]      : ").strip() or "10.0.10.50"
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