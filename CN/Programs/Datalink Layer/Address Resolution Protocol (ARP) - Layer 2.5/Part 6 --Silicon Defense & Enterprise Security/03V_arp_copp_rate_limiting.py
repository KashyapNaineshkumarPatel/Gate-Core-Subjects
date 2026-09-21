"""
Core Logic: Enterprise switches are built with two distinct processing planes. 
The Data Plane (hardware ASICs) forwards standard payload traffic at wire-speed 
(Tbps). The Control Plane (the central switch CPU) handles routing protocols (BGP/OSPF), 
management (SSH), and specific Layer 2 protocols like ARP.

When an ARP broadcast enters a switch, the ASIC cannot forward it purely in hardware 
if the switch itself needs to learn the MAC or route the packet. The ASIC must "punt" 
a copy of the ARP frame to the switch CPU.

As demonstrated in the macof flood attack (Module 04O), if an attacker blasts 10,000 
ARP packets per second, the switch CPU is overwhelmed handling hardware interrupts. 
The CPU spikes to 100%, routing protocols drop (BGP teardown), and the network crashes.

Control Plane Policing (CoPP) solves this. It is a hardware-level Quality of Service 
(QoS) policy applied directly to the internal CPU interface. 
1. The network engineer defines a strict rate limit for ARP (e.g., 250 packets/sec).
2. The hardware ASIC tracks the arrival rate of ARP packets destined for the CPU.
3. If the rate exceeds 250 PPS, the ASIC mathematically drops the excess packets in 
   silicon BEFORE they ever trigger a CPU interrupt.
4. The switch control plane remains perfectly stable even during a massive DoS attack.
"""

import sys
import shutil
import time
from typing import Any, Dict

class CoPPRateLimitingEngine:
    copp_state: Dict[str, Any]

    def __init__(self) -> None:
        self.copp_state = {}
        # Hardware Rate Limit (Committed Information Rate - CIR) mapped to the CPU interface
        self.arp_cir_pps = 250
        # Theoretical max CPU threshold before panic
        self.cpu_panic_threshold_pps = 1500 

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def validate_int(self, val_input: str, name: str) -> int:
        try:
            val = int(val_input.strip())
            if val < 0:
                raise ValueError()
            return val
        except ValueError:
            raise ValueError(f"Bounds Error: {name} must be a positive integer.")

    def execute_copp_physics(self, inbound_pps: int) -> None:
        """Simulates hardware token-bucket rate limiting for the Control Plane CPU."""
        
        flow = []
        flow.append(f"1. [Inbound Wire]: Host injects ARP broadcasts at {inbound_pps:,} Packets Per Second (PPS).")
        flow.append(f"2. [Switch ASIC]: Identifies frames as 'Punt to CPU' (ARP Protocol Flag).")
        flow.append(f"3. [ASIC CoPP Class]: Evaluates traffic against CoPP_ARP_POLICY (Hardware Limit: {self.arp_cir_pps} PPS).")
        
        if inbound_pps <= self.arp_cir_pps:
            passed = inbound_pps
            dropped = 0
            
            # Calculate CPU Load (Linear scale up to panic threshold)
            cpu_load = min((passed / self.cpu_panic_threshold_pps) * 100, 100.0)
            
            flow.append(f"4. [Hardware Token Bucket]: Traffic conforms to CIR. 0 packets dropped.")
            flow.append("5. [Switch CPU]: Processes all ARP requests normally via software interrupts.")
            
            action = "CONFORM (Wire-Speed Pass to CPU)"
            stability = f"STABLE (CPU Load: {cpu_load:.1f}%)"
            insight = "Under normal conditions, ambient ARP traffic easily falls below the CoPP threshold. The CPU handles the interrupts seamlessly, maintaining standard network resolution."
            
        else:
            passed = self.arp_cir_pps
            dropped = inbound_pps - self.arp_cir_pps
            
            # CPU load is capped because the ASIC physically refuses to pass more than the CIR
            cpu_load = min((passed / self.cpu_panic_threshold_pps) * 100, 100.0)
            
            flow.append(f"4. [Hardware Token Bucket]: Traffic EXCEEDS CIR. Hardware policing aggressively engaged.")
            flow.append(f"5. [Switch ASIC]: Passes {passed:,} PPS to CPU. Silently drops {dropped:,} PPS in silicon.")
            flow.append("6. [Switch CPU]: Only processes conformant traffic. Completely protected from interrupt storm.")
            
            action = "EXCEED (Hardware Silicon Drop)"
            stability = f"STABLE (CPU Load: {cpu_load:.1f}%) - DoS Attack Mitigated"
            insight = "By leveraging the ASIC to execute the drops, CoPP ensures the CPU never even registers the flood. While legitimate ARP requests might experience slight latency due to tail drops, the core routing plane (BGP/OSPF/SSH) remains perfectly online."

        self.copp_state = {
            "inbound": inbound_pps,
            "passed": passed,
            "dropped": dropped,
            "flow": flow,
            "action": action,
            "stability": stability,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.copp_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04V: ARP CONTROL PLANE POLICING (CoPP) ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] ASIC CoPP HARDWARE POLICY (PUNT PATH):")
        print(f"     -> Protocol Class   : ARP (Broadcast/Unicast)")
        print(f"     -> Hardware CIR Limit: {self.arp_cir_pps} Packets Per Second")
        print("-" * width)
        
        print(" [i] SILICON POLICING SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] DATAPLANE AND CPU SURVIVABILITY:")
        time.sleep(0.3)
        print(f"     -> Hardware Action  : [ {state['action']} ]")
        print(f"     -> Packets Passed   : {state['passed']:,} PPS (Hitting CPU)")
        print(f"     -> Packets Dropped  : {state['dropped']:,} PPS (Killed in ASIC)")
        print(f"     -> Control Plane    : {state['stability']}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = CoPPRateLimitingEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04V_ARP_COPP_RATE_LIMITING INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Ingress ARP Traffic Load:")
            print("    (Tip: Try 60 for normal ambient traffic, or 25000 for a catastrophic macof flood)")
            
            pps_in = input("    Inbound ARP Packets per Sec [Default: 25000] : ").strip() or "25000"
            if pps_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            pps = engine.validate_int(pps_in, "PPS")
            engine.execute_copp_physics(pps)
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