"""
Core Logic: Modern Software-Defined Vehicles (SDVs) like Tesla, Rivian, and modern 
BMWs no longer use pure legacy CAN bus for everything. They use Automotive Ethernet 
(100BASE-T1 / 1000BASE-T1) connecting Zonal Gateways.

The Automotive Security Threat:
The Infotainment head unit (running Android Automotive or custom Linux) is connected 
to Spotify, Bluetooth, and the cellular LTE/5G network. It is the vehicle's largest 
attack surface. If an attacker compromises the Infotainment system, their first move 
is to map the network using ARP broadcasts to find critical ECUs (Engine, Brakes, Steering).

The Architectural Defense (Strict Zonal VLAN Isolation):
1. The Infotainment unit is hardware-pinned to VLAN 100 (Untrusted / Telematics).
2. The Braking ECU and ADAS (Advanced Driver Assistance) are pinned to VLAN 200 (Critical OT).
3. The Zonal Ethernet Switch ASIC strictly enforces IEEE 802.1Q VLAN boundaries.
4. An ARP Broadcast (FF:FF:FF:FF:FF:FF) sent by a compromised Infotainment unit is 
   mathematically constrained to VLAN 100. The ASIC will NOT flood it to VLAN 200 ports.
5. If the attacker tries to forge an 802.1Q VLAN 200 tag on their frame (VLAN Hopping), 
   the switch's ingress filter drops the frame at line rate because the Infotainment 
   port is strictly configured as an untagged access port.
"""

import sys
import shutil
import time
from typing import Any, Dict

class AutomotiveVlanIsolationEngine:
    auto_state: Dict[str, Any]

    def __init__(self) -> None:
        self.auto_state = {}
        
        # Vehicle Zonal Architecture
        self.infotainment = {"ip": "10.0.100.5", "mac": "IN:FO:00:11:22:33", "vlan": 100, "port": "Eth1/1"}
        self.lte_gateway  = {"ip": "10.0.100.1", "mac": "LT:EE:00:11:22:33", "vlan": 100, "port": "Eth1/2"}
        
        self.brake_ecu    = {"ip": "10.0.200.5", "mac": "BR:AK:E0:00:11:22", "vlan": 200, "port": "Eth2/1"}
        self.steering_ecu = {"ip": "10.0.200.6", "mac": "ST:EE:R0:00:11:22", "vlan": 200, "port": "Eth2/2"}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_automotive_physics(self, scenario: str) -> None:
        """Simulates Zonal Gateway ASIC enforcing VLAN boundaries against lateral movement."""
        
        flow = []
        frames = []
        action = ""
        insight = ""
        
        if scenario == "1":
            # Legitimate Infotainment Traffic (Spotify to LTE Gateway)
            flow.append(f"1. [Infotainment {self.infotainment['port']}]: Generates ARP Request for LTE Gateway {self.lte_gateway['ip']}.")
            flow.append(f"2. [Zonal Switch]: Receives untagged frame. Ingress port native VLAN is {self.infotainment['vlan']}.")
            flow.append(f"3. [Zonal Switch]: Flooding ARP Broadcast ONLY to ports mapped to VLAN {self.infotainment['vlan']}.")
            flow.append(f"4. [LTE Gateway {self.lte_gateway['port']}]: Receives Broadcast. Synthesizes Reply.")
            flow.append(f"5. [Brake ECU {self.brake_ecu['port']}]: Hears nothing. Hardware isolated.")
            
            action = "L2 RESOLUTION SUCCESS (Isolated Domain)"
            insight = "Standard operation. The Infotainment unit can freely resolve the LTE gateway to stream music, but the broadcast radiation is physically contained within the non-critical VLAN 100."
            
            frame = {
                "stage": "Switch ASIC Flooding Domain",
                "encap": f"L2 Dst: FF:FF:FF:FF:FF:FF | 802.1Q Tag: {self.infotainment['vlan']} (Internal)",
                "status": f"Flooded to {self.lte_gateway['port']} ONLY."
            }
            frames.append(frame)

        elif scenario == "2":
            # Compromised Infotainment scanning for Brakes
            flow.append(f"1. [Infotainment {self.infotainment['port']}]: COMPROMISED. Malware scans subnet.")
            flow.append(f"2. [Infotainment OS]: Generates ARP Request -> 'Who has {self.brake_ecu['ip']}?'")
            flow.append(f"3. [Zonal Switch]: Ingress port {self.infotainment['port']} applies VLAN {self.infotainment['vlan']} context.")
            flow.append(f"4. [Zonal Switch ASIC]: Floods ARP to VLAN {self.infotainment['vlan']} ports.")
            flow.append(f"5. [Zonal Switch ASIC]: Does NOT forward broadcast to VLAN {self.brake_ecu['vlan']} (Brake ECU).")
            flow.append(f"6. [Infotainment OS]: ARP Timeout. Target Unreachable.")
            
            action = "ATTACK MITIGATED (VLAN L2 Boundary)"
            insight = "Because an ARP broadcast is a Layer 2 mechanism, it cannot cross a router or a VLAN boundary. The attacker's subnet scan is mathematically blind to the existence of the braking and steering ECUs."
            
            frame = {
                "stage": "Malicious Subnet Scan",
                "encap": f"ARP Target: {self.brake_ecu['ip']} | Internal Tag: {self.infotainment['vlan']}",
                "status": "Dropped at VLAN boundary. ECUs safe."
            }
            frames.append(frame)

        elif scenario == "3":
            # Advanced Attack: VLAN Hopping (802.1Q Injection)
            flow.append(f"1. [Infotainment {self.infotainment['port']}]: COMPROMISED. Malware attempts VLAN Hopping.")
            flow.append(f"2. [Infotainment OS]: Crafts malicious raw ethernet frame with explicit 802.1Q Tag = {self.brake_ecu['vlan']}.")
            flow.append(f"3. [Zonal Switch]: Ingress port {self.infotainment['port']} receives tagged frame.")
            flow.append(f"4. [Zonal Switch ASIC]: Port is configured as strict UNTAGGED ACCESS for VLAN {self.infotainment['vlan']}.")
            flow.append(f"5. [Zonal Switch ASIC]: Ingress Filtering triggers. Unexpected tag detected.")
            flow.append(f"6. [Zonal Switch ASIC]: Frame shredded at line rate. Port security violation logged.")
            
            action = "ATTACK SHREDDED (Ingress Filtering)"
            insight = "A sophisticated attacker might try to forge the VLAN tag using raw sockets. However, automotive Ethernet switches are configured with strict ingress filtering. If an access port receives a tagged frame, the silicon destroys it instantly, preventing 802.1Q injection."
            
            frame = {
                "stage": "802.1Q Injection Attempt",
                "encap": f"Forged Tag: {self.brake_ecu['vlan']} | Actual Port Native VLAN: {self.infotainment['vlan']}",
                "status": "HARDWARE DROP (Line Rate)"
            }
            frames.append(frame)

        self.auto_state = {
            "scenario": scenario,
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.auto_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AX: AUTOMOTIVE ZONAL VLAN ISOLATION ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] VEHICLE ZONAL ARCHITECTURE:")
        print(f"     -> Infotainment Domain : VLAN {self.infotainment['vlan']} (Untrusted)")
        print(f"     -> Critical ECU Domain : VLAN {self.brake_ecu['vlan']} (Drive-by-Wire)")
        print("-" * width)
        
        print(" [i] DATAPLANE ENFORCEMENT SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] SWITCH ASIC PROCESSING:")
        time.sleep(0.3)
        for frame in state['frames']:
            print(f"\n     [{frame['stage']}]")
            print(f"     Header Structure : {frame['encap']}")
            print(f"     Security Outcome : {frame['status']}")
            time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f"     -> Zonal Gateway Action : [ {state['action']} ]")
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = AutomotiveVlanIsolationEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AX_AUTOMOTIVE_VLAN_ARP_ISOLATION INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select Vehicle Network Scenario:")
            print("    1. Legitimate Infotainment Traffic (VLAN 100 -> LTE Gateway)")
            print("    2. Malware ARP Subnet Scan (Attempting to find Brake ECU)")
            print("    3. Raw Socket VLAN Hopping (802.1Q Injection Attempt)")
            
            choice = input("    Select scenario (1/2/3) [Default: 2] : ").strip() or "2"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice not in ["1", "2", "3"]:
                raise ValueError("Selection Error: Please choose 1, 2, or 3.")
            
            engine.execute_automotive_physics(choice)
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