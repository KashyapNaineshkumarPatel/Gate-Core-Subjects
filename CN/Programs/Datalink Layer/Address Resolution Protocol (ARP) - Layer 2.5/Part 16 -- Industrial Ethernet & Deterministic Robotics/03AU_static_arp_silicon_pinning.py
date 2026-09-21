"""
Core Logic: In IT networks, Dynamic ARP is a feature. In OT (Operational Technology) 
and SCADA environments, Dynamic ARP is an unacceptable vulnerability. 

If an attacker gains physical access to a factory floor (e.g., plugging a rogue 
device into an exposed switchport), they could launch an ARP Cache Poisoning attack 
(Module 04E) to intercept traffic between a Human Machine Interface (HMI) and a 
Programmable Logic Controller (PLC). This could allow the attacker to manipulate 
centrifuge speeds, boiler temperatures, or robotic arm vectors.

The Industrial Mitigation: Static Silicon Pinning.
1. The OS network stack on the PLC and HMI is configured to completely ignore all 
   incoming ARP Requests and Replies (`arp -s` or stack-level lock).
2. The Industrial Ethernet Switch disables dynamic MAC learning.
3. The exact IP-to-MAC-to-Physical-Port bindings are hardcoded into the switch's 
   TCAM (Ternary Content-Addressable Memory).
4. If a frame arrives with a mismatched IP/MAC pairing, or on the wrong physical port, 
   the ASIC shreds it at line rate before the CPU even registers the event.
"""

import sys
import shutil
import time
from typing import Any, Dict

class StaticARPPinningEngine:
    pinning_state: Dict[str, Any]

    def __init__(self) -> None:
        self.pinning_state = {}
        
        # Hardcoded SCADA Architecture (Pinned in Silicon)
        self.plc_ip = "192.168.100.10"
        self.plc_mac = "PL:CC:CC:00:00:10"
        self.plc_port = "FastEthernet0/1"
        
        self.hmi_ip = "192.168.100.20"
        self.hmi_mac = "HM:II:II:00:00:20"
        self.hmi_port = "FastEthernet0/2"
        
        # Threat Actor
        self.rogue_mac = "DE:AD:BE:EF:66:66"
        self.rogue_port = "FastEthernet0/3"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_silicon_validation(self, attack_type: str) -> None:
        """Simulates ASIC-level enforcement of static ARP/MAC bindings."""
        
        flow = []
        frames = []
        action = ""
        insight = ""
        
        flow.append(f"1. [OT Fabric]: Switch TCAM programmed with Static Bindings.")
        flow.append(f"   -> {self.plc_port} MUST be {self.plc_mac} MUST be {self.plc_ip}")
        flow.append(f"   -> {self.hmi_port} MUST be {self.hmi_mac} MUST be {self.hmi_ip}")
        
        if attack_type == "1":
            # Legitimate HMI to PLC Command
            flow.append(f"\n2. [Ingress {self.hmi_port}]: Frame received from HMI.")
            
            frame = {
                "stage": "Hardware TCAM Validation",
                "encap": f"Src MAC: {self.hmi_mac} | Src IP: {self.hmi_ip}",
                "status": "VALID"
            }
            frames.append(frame)
            
            flow.append("3. [ASIC Logic]: Source MAC matches pinned port. Source IP matches pinned MAC.")
            flow.append("4. [ASIC Logic]: Destination IP (PLC) statically mapped to Egress Port 1.")
            flow.append(f"5. [Dataplane]: Frame forwarded to {self.plc_port} at wire-speed.")
            
            action = "FORWARDED (Silicon Match)"
            insight = "Because the HMI has a static ARP entry for the PLC, it never generates an ARP Broadcast. It instantly transmits the unicast frame. The switch ASIC validates the strict binding in hardware and forwards it with zero processing overhead."

        elif attack_type == "2":
            # Gratuitous ARP Poisoning Attempt
            flow.append(f"\n2. [Ingress {self.rogue_port}]: Attacker connects rogue laptop to open port.")
            flow.append(f"3. [Attacker OS]: Broadcasts GARP -> '{self.plc_ip} (PLC) is now at {self.rogue_mac}'.")
            
            frame = {
                "stage": "Hardware TCAM Validation",
                "encap": f"Src MAC: {self.rogue_mac} | ARP Sender IP: {self.plc_ip} (Spoofed)",
                "status": "VIOLATION DETECTED"
            }
            frames.append(frame)
            
            flow.append("4. [ASIC Logic]: Analyzing ARP Payload. Sender IP claims to be PLC.")
            flow.append(f"5. [ASIC Logic]: TCAM enforces {self.plc_ip} MUST originate from {self.plc_port} and {self.plc_mac}.")
            flow.append("6. [Port Security]: Violation! Rogue MAC attempting to hijack pinned IP.")
            flow.append(f"7. [Dataplane]: Frame instantly shredded. Port {self.rogue_port} placed in err-disable (Shutdown).")
            
            action = "DROPPED & PORT SHUTDOWN (Spoofing Mitigated)"
            insight = "Dynamic ARP relies on trust. In ICS/SCADA, trust is a vulnerability. By locking the IP-to-MAC-to-Port relationships into the physical silicon of the switch, cache poisoning becomes mathematically impossible to execute on the wire."

        elif attack_type == "3":
            # Direct IP Spoofing (Bypassing ARP)
            flow.append(f"\n2. [Ingress {self.rogue_port}]: Attacker bypasses ARP, directly crafts IP packet.")
            flow.append(f"3. [Attacker OS]: Injects IP frame -> Src IP: {self.hmi_ip} (Spoofed HMI) | Dst IP: {self.plc_ip}.")
            
            frame = {
                "stage": "Hardware TCAM Validation",
                "encap": f"Src MAC: {self.rogue_mac} | L3 Src IP: {self.hmi_ip} (Spoofed)",
                "status": "VIOLATION DETECTED"
            }
            frames.append(frame)
            
            flow.append("4. [ASIC Logic]: Cross-referencing L2 MAC with L3 IP at ingress.")
            flow.append(f"5. [ASIC Logic]: TCAM enforces {self.hmi_ip} MUST possess {self.hmi_mac}.")
            flow.append(f"6. [ASIC Logic]: Actual Source MAC is {self.rogue_mac}. Mismatch triggered.")
            flow.append("7. [Dataplane]: Frame shredded at line rate via IP Source Guard.")
            
            action = "DROPPED (L2/L3 Binding Failure)"
            insight = "Even if the attacker tries to skip ARP and directly spoof the L3 IP address, the switch silicon enforces the L2/L3 relationship. If you don't have the physical burned-in MAC address of the HMI, you cannot speak as the HMI."

        self.pinning_state = {
            "attack_type": attack_type,
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.pinning_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AU: STATIC ARP & SILICON PINNING ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] HARDWARE TCAM (BURNED-IN BINDINGS):")
        print(f"     -> PLC Node : Port {self.plc_port[-1]} | {self.plc_mac} | {self.plc_ip}")
        print(f"     -> HMI Node : Port {self.hmi_port[-1]} | {self.hmi_mac} | {self.hmi_ip}")
        print("-" * width)
        
        print(" [i] INGRESS VALIDATION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] ASIC ENFORCEMENT STATE:")
        time.sleep(0.3)
        for frame in state['frames']:
            print(f"\n     [{frame['stage']}]")
            print(f"     Payload Header : {frame['encap']}")
            print(f"     Silicon Check  : {frame['status']}")
            time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f"     -> Fabric Action   : [ {state['action']} ]")
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = StaticARPPinningEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AU_STATIC_ARP_SILICON_PINNING INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select Industrial Security Scenario:")
            print("    1. Legitimate HMI to PLC Command (Zero ARP)")
            print("    2. Rogue Actor: Gratuitous ARP Poisoning Attempt")
            print("    3. Rogue Actor: Direct IP Spoofing (IP Source Guard Test)")
            
            choice = input("    Select scenario (1/2/3) [Default: 1] : ").strip() or "1"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice not in ["1", "2", "3"]:
                raise ValueError("Selection Error: Please choose 1, 2, or 3.")
            
            engine.execute_silicon_validation(choice)
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