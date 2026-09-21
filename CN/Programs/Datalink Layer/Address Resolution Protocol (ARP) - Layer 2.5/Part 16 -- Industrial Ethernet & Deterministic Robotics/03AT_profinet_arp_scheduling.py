"""
Core Logic: Standard Ethernet is "Best Effort." It uses FIFO (First-In, First-Out) 
queuing. If a maintenance laptop on the factory floor unleashes a massive broadcast 
storm of ARP requests, those frames will clog the switch queues, delaying critical 
robotic control packets.

PROFINET IRT (Isochronous Real-Time) and Time-Sensitive Networking (TSN) fundamentally 
alter switch silicon to support TDMA (Time Division Multiple Access).

The Deterministic Cycle:
1. The switch divides every millisecond (1000 µs) into strict hardware time slices.
2. The Red Phase (e.g., 0 - 500 µs) is exclusively reserved for IRT Robotics traffic.
3. The Green Phase (e.g., 501 - 1000 µs) is the NRT (Non-Real-Time) open channel.
4. If an ARP request arrives at the switch during the Red Phase, the hardware ASIC 
   does not process it. It aggressively buffers the ARP frame into an NRT queue and 
   physically halts its transmission until the Green Phase opens.
5. Robotics traffic bypasses IP and ARP entirely, using raw Layer 2 EtherTypes 
   (e.g., 0x8892) mapped directly to the Red Phase for guaranteed sub-millisecond delivery.
"""

import sys
import shutil
import time
from typing import Any, Dict

class ProfinetARPSchedulingEngine:
    profinet_state: Dict[str, Any]

    def __init__(self) -> None:
        self.profinet_state = {}
        
        # Microsecond cycle definitions
        self.cycle_time_us = 1000
        self.irt_window_us = 500 # Dedicated to robotics
        self.nrt_window_us = 500 # Dedicated to TCP/IP/ARP
        
        # Payloads
        self.robot_frame = {"type": "PROFINET IRT (0x8892)", "size": "64 Bytes", "deadline": "250 µs"}
        self.arp_frame = {"type": "ARP Broadcast (0x0806)", "size": "64 Bytes", "priority": "Best Effort"}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_tsn_physics(self, switch_type: str) -> None:
        """Simulates how standard vs. PROFINET switches handle simultaneous IRT and ARP traffic."""
        
        flow = []
        frames = []
        
        flow.append("1. [Factory Floor]: Robot Controller generates precision IRT Deceleration Command.")
        flow.append("2. [Factory Floor]: Maintenance Laptop simultaneously broadcasts an ARP Request.")
        flow.append("3. [Switch Ingress]: Both frames hit the switch ASICs at t=0 µs.")
        
        if switch_type == "1":
            # Standard COTS (Commercial Off-The-Shelf) Switch
            flow.append("4. [Standard ASIC]: FIFO (First-In, First-Out) queuing architecture activated.")
            flow.append("5. [Standard ASIC]: ARP Broadcast processed slightly faster by ingress port. Placed first in Egress Queue.")
            flow.append("6. [Standard ASIC]: Robot IRT frame queued behind the ARP broadcast (Head-of-Line Blocking).")
            flow.append("7. [Dataplane]: ARP frame transmitted to all ports. Takes 120 µs of wire time.")
            flow.append("8. [Dataplane]: Robot IRT frame finally transmitted at t=125 µs.")
            
            action = "SAFETY FAULT (Jitter Introduced)"
            insight = "In standard networking, an ARP broadcast can physically block a critical motion control frame. A 125-microsecond delay violates the strict real-time deadline. The robotic arm's safety PLC detects the synchronization loss and instantly executes an Emergency Stop (E-STOP), halting the entire assembly line."
            
            frame_1 = {
                "stage": "Queue Slot 1 (Transmitted t=5 µs)",
                "payload": f"[{self.arp_frame['type']}] - Destination: FF:FF:FF:FF:FF:FF",
                "status": "Transmitted (Blocking critical traffic)"
            }
            frames.append(frame_1)
            
            frame_2 = {
                "stage": "Queue Slot 2 (Transmitted t=125 µs)",
                "payload": f"[{self.robot_frame['type']}] - Destination: 02:00:00:00:00:11",
                "status": "Delayed (Deadline Missed)"
            }
            frames.append(frame_2)

        else:
            # PROFINET IRT / TSN Switch
            flow.append("4. [TSN ASIC]: Hardware clock synchronized via IEEE 1588 Precision Time Protocol (PTP).")
            flow.append(f"5. [TSN ASIC]: Current Phase is RED (IRT Window: 0 - {self.irt_window_us} µs).")
            flow.append("6. [TSN ASIC]: ARP Broadcast identified as NRT traffic. Shunted to isolated holding buffer.")
            flow.append("7. [TSN ASIC]: Robot IRT frame bypasses standard queues (Cut-Through Switching).")
            flow.append("8. [Dataplane]: Robot IRT frame transmitted instantly at t=2 µs.")
            flow.append(f"9. [TSN ASIC]: RED phase ends at t={self.irt_window_us} µs. GREEN Phase opens.")
            flow.append(f"10. [Dataplane]: Buffered ARP Broadcast finally released onto the wire at t={self.irt_window_us + 1} µs.")
            
            action = "DETERMINISTIC SUCCESS (Zero Jitter)"
            insight = "By slicing the physical time on the wire, Industrial Ethernet ensures that standard IT traffic (ARP, Ping, Web) can never interfere with Operational Technology (OT) traffic. The ARP request is mathematically guaranteed to wait until the robots have safely communicated."
            
            frame_1 = {
                "stage": "RED Phase TX (t=2 µs)",
                "payload": f"[{self.robot_frame['type']}] - Destination: 02:00:00:00:00:11",
                "status": "Instant Transmission (Deadline Met)"
            }
            frames.append(frame_1)
            
            frame_2 = {
                "stage": "GREEN Phase TX (t=501 µs)",
                "payload": f"[{self.arp_frame['type']}] - Destination: FF:FF:FF:FF:FF:FF",
                "status": "Buffered / Delayed Transmission"
            }
            frames.append(frame_2)

        self.profinet_state = {
            "type": "Standard Best-Effort Switch" if switch_type == "1" else "PROFINET IRT / TSN Switch",
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.profinet_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AT: PROFINET TSN & ARP SCHEDULING ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] SILICON ARCHITECTURE : {state['type']}")
        print(f"     -> Hardware Cycle    : {self.cycle_time_us} µs")
        print(f"     -> Red Phase (IRT)   : {self.irt_window_us} µs (Robotics Only)")
        print(f"     -> Green Phase (NRT) : {self.nrt_window_us} µs (ARP/TCP/IP Allowed)")
        print("-" * width)
        
        print(" [i] QUEUING & DATAPLANE SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] EGRESS WIRE TRANSMISSION STATE:")
        time.sleep(0.3)
        for frame in state['frames']:
            print(f"\n     [{frame['stage']}]")
            print(f"     Payload : {frame['payload']}")
            print(f"     Status  : {frame['status']}")
            time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f"     -> Assembly Line Action : [ {state['action']} ]")
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = ProfinetARPSchedulingEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AT_PROFINET_ARP_SCHEDULING INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select Industrial Switch Architecture:")
            print("    1. Standard Commercial Switch (FIFO Queuing)")
            print("    2. PROFINET IRT / TSN Switch (Time Division Queuing)")
            
            choice = input("    Select architecture (1/2) [Default: 2] : ").strip() or "2"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice not in ["1", "2"]:
                raise ValueError("Selection Error: Please choose 1 or 2.")
            
            engine.execute_tsn_physics(choice)
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