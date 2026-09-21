"""
Core Logic: When an application (like a web browser or a port scanner) attempts to send 
data to an IP address, it pushes the payload down the stack to the OS kernel. 

If the destination MAC address is unknown, the kernel enters the INCOMPLETE state and 
must halt the IP transmission to send an ARP Request. But what happens to the application's 
payload while the OS waits for the ARP Reply?

The kernel places the packets into a holding buffer called the "Unresolved Queue" (unres_qlen).
Because kernel memory (sk_buff) is precious, this queue is strictly limited. In Linux, 
the historical default for unres_qlen is just 3 packets per ARP entry. 

If a high-speed application (like Nmap or a UDP video stream) blasts 50 packets at a new IP 
in a single millisecond, the OS will queue the first 3 and instantly DROP the remaining 47 
to protect kernel memory. 

If the ARP Reply arrives, the queued packets are flushed out to the wire. If the ARP Request 
times out, the queued packets are dropped, and the kernel signals an ICMP Host Unreachable 
error back to the application.
"""

import sys
import shutil
import time
from typing import Any, Dict

class ARPQueueingPhysicsEngine:
    queue_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.queue_state = {}
        # Linux Default Unresolved Queue Length (Packets)
        self.unres_qlen = 3

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_burst(self, burst_input: str) -> int:
        try:
            val = int(burst_input)
            if val <= 0:
                raise ValueError("Bounds Error: Packet burst must be at least 1.")
            return val
        except ValueError as e:
            raise ValueError(f"Type Error: {e}")

    def validate_resolution(self, resolution_input: str) -> bool:
        choice = resolution_input.strip()
        if choice not in ["1", "2"]:
            raise ValueError("Configuration Error: Select 1 (Success) or 2 (Timeout).")
        return choice == "1"

    def execute_queue_simulation(self, packet_burst: int, arp_resolves: bool) -> None:
        """Simulates the OS kernel holding buffer (unres_qlen) physics."""
        
        # 1. Queueing Phase
        queued = min(packet_burst, self.unres_qlen)
        dropped_by_overflow = packet_burst - queued
        
        # 2. Resolution Phase
        transmitted = 0
        dropped_by_timeout = 0
        action = ""
        
        if arp_resolves:
            transmitted = queued
            action = "ARP Reply received. Kernel flushes unresolved queue. Packets transmitted to wire."
            final_status = "REACHABLE"
        else:
            dropped_by_timeout = queued
            action = "ARP Request timed out. Kernel flushes unresolved queue to bitbucket (DROP). App notified."
            final_status = "FAILED (ICMP Destination Unreachable)"

        total_dropped = dropped_by_overflow + dropped_by_timeout

        insight = (
            "This tiny 3-packet holding buffer is the exact reason why fast UDP streams, ping floods, "
            "or aggressive Nmap port scans often report 'lost' packets on a fresh LAN connection. The network "
            "didn't drop them—the sender's own OS kernel ruthlessly dropped them when the ARP queue overflowed "
            "before the MAC could resolve."
        )

        self.queue_state = {
            "burst": packet_burst,
            "qlen_limit": self.unres_qlen,
            "queued": queued,
            "overflow_drops": dropped_by_overflow,
            "resolves": arp_resolves,
            "transmitted": transmitted,
            "timeout_drops": dropped_by_timeout,
            "total_dropped": total_dropped,
            "final_status": final_status,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.queue_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04F: ARP QUEUEING PHYSICS ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] KERNEL INGRESS (APPLICATION LAYER):")
        print(f"     -> Application Burst    : {state['burst']} Packets")
        print(f"     -> OS unres_qlen Limit  : {state['qlen_limit']} Packets")
        print("-" * width)
        
        print(" [i] HOLDING BUFFER (INCOMPLETE STATE):")
        time.sleep(0.3)
        print(f"     -> Packets Queued       : {state['queued']}")
        print(f"     -> Overflow Drops       : {state['overflow_drops']} (App exceeded buffer speed)")
        print("-" * width)
        
        print(" [!] ARP RESOLUTION OUTCOME:")
        time.sleep(0.3)
        print(f"     -> Hardware State       : [{state['final_status']}]")
        print(f"     -> Action               : {state['action']}")
        time.sleep(0.2)
        print(f"     -> Packets Transmitted  : {state['transmitted']}")
        print(f"     -> Total Packets Dropped: {state['total_dropped']}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL BUFFER INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = ARPQueueingPhysicsEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04F_ARP_QUEUEING_PHYSICS INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Application Packet Burst:")
            print("    (Tip: 1 for standard web request, 100 for Nmap/UDP flood)")
            burst_in = input("    Packets pushed to Kernel [Default: 10] : ").strip() or "10"
            if burst_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            print("\n[?] Simulate Target Reachability:")
            print("    1. Target is ONLINE (ARP Reply arrives)")
            print("    2. Target is OFFLINE (ARP Timeout)")
            res_in = input("    Outcome [1/2] [Default: 1]             : ").strip() or "1"
            
            burst = engine.validate_burst(burst_in)
            resolves = engine.validate_resolution(res_in)
            
            engine.execute_queue_simulation(burst, resolves)
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