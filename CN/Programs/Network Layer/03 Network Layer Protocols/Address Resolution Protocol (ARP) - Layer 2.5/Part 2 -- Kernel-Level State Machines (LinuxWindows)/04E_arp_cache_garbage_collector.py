"""
Core Logic: An OS kernel cannot allow the ARP cache to grow infinitely. If an attacker 
scanned a /16 subnet, it would force the server to hold 65,535 MAC addresses in RAM, 
potentially starving the kernel of memory and crashing the system.

To prevent memory exhaustion, the Linux kernel uses a strict Garbage Collection (GC) 
algorithm governed by three thresholds:
- gc_thresh1 (Default 128): The absolute minimum. If the cache size is below this, 
  the Garbage Collector does absolutely nothing.
- gc_thresh2 (Default 512): The soft limit. If the cache exceeds this, the GC starts 
  a 5-second timer. If the cache stays above 512 for 5 seconds, it aggressively purges 
  STALE entries.
- gc_thresh3 (Default 1024): The hard maximum limit. If the cache hits this number, 
  the GC runs instantaneously. If it cannot free up space, the kernel throws the infamous 
  "Neighbour table overflow!" error, and all new IP connections are completely dropped 
  (Denial of Service).
"""

import sys
import shutil
import time
import random
from typing import Any, Dict

class ARPGarbageCollectorEngine:
    gc_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.gc_state = {}
        # Linux Default Thresholds
        self.thresh1 = 128
        self.thresh2 = 512
        self.thresh3 = 1024

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_input(self, count_input: str) -> int:
        try:
            val = int(count_input)
            if val < 0:
                raise ValueError("Bounds Error: ARP entry count cannot be negative.")
            return val
        except ValueError as e:
            raise ValueError(f"Type Error: {e}")

    def execute_garbage_collection(self, current_entries: int) -> None:
        """Simulates the Linux kernel ARP Garbage Collection thresholds."""
        
        status = ""
        action = ""
        dropped = 0
        new_count = current_entries
        panic = False

        if current_entries <= self.thresh1:
            status = "IDLE (Below gc_thresh1)"
            action = "GC Sleeping. Memory footprint is minimal. No entries evicted."
            
        elif self.thresh1 < current_entries <= self.thresh2:
            status = "PASSIVE (Below gc_thresh2)"
            action = "GC is awake but passive. Evicting only naturally expired STALE entries."
            # Simulate natural STALE expiration
            dropped = random.randint(1, max(2, int(current_entries * 0.05)))
            new_count -= dropped
            
        elif self.thresh2 < current_entries <= self.thresh3:
            status = "AGGRESSIVE (Exceeded gc_thresh2 soft limit)"
            action = "GC 5-second grace period triggered. Aggressively purging all STALE/DELAY entries."
            # Simulate aggressive purge bringing it back down near thresh2
            dropped = current_entries - self.thresh2 + random.randint(10, 50)
            new_count = max(self.thresh2 - random.randint(10, 50), current_entries - dropped)
            
        elif current_entries > self.thresh3:
            status = "CRITICAL (Exceeded gc_thresh3 hard limit)"
            # Simulate kernel failing to find enough flushable entries (e.g. an active scan attack)
            stale_entries = random.randint(100, 300)
            dropped = stale_entries
            new_count -= dropped
            
            if new_count >= self.thresh3:
                panic = True
                action = "KERNEL PANIC: 'Neighbour table overflow'. Cannot free enough memory. New packets DROPPED."
            else:
                action = "EMERGENCY PURGE: GC ran instantaneously. Successfully evaded memory exhaustion."

        insight = (
            "These thresholds are why standard Linux distributions fail as enterprise routers out-of-the-box. "
            "If you build a Linux router for a subnet with 2,000 devices, the ARP table will hit gc_thresh3 "
            "(1024) and the network will mysteriously collapse. Network engineers must manually tune "
            "sysctl net.ipv4.neigh.default.gc_thresh3 to stabilize large subnets."
        )

        self.gc_state = {
            "initial_count": current_entries,
            "final_count": new_count,
            "dropped": dropped,
            "status": status,
            "panic": panic,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.gc_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04E: ARP CACHE GARBAGE COLLECTOR ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] KERNEL ARP MEMORY ALLOCATION:")
        print(f"     -> Initial ARP Entries : {state['initial_count']:,}")
        print(f"     -> Threshold 1 (Min)   : {self.thresh1}")
        print(f"     -> Threshold 2 (Soft)  : {self.thresh2}")
        print(f"     -> Threshold 3 (Hard)  : {self.thresh3}")
        print("-" * width)
        
        print(" [i] GARBAGE COLLECTION HEURISTICS:")
        time.sleep(0.3)
        print(f"     -> GC State            : {state['status']}")
        time.sleep(0.2)
        print(f"     -> Kernel Action       : {state['action']}")
        print(f"     -> Entries Evicted     : {state['dropped']:,}")
        print("-" * width)
        
        print(" [!] FINAL KERNEL STABILITY:")
        time.sleep(0.3)
        status_flag = "[ X ] NEIGHBOUR OVERFLOW" if state['panic'] else "[ > ] SYSTEM STABLE"
        print(f"     -> Status              : {status_flag}")
        print(f"     -> Remaining Entries   : {state['final_count']:,}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL TUNING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = ARPGarbageCollectorEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04E_ARP_CACHE_GARBAGE_COLLECTOR INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Subnet ARP Table Volume:")
            print("    (Tip: Try 100 for normal PC, 800 for busy server, 1500 for Nmap scan attack)")
            count_in = input("    Current ARP Entries in RAM [Default: 800] : ").strip() or "800"
            if count_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            entries = engine.validate_input(count_in)
            
            engine.execute_garbage_collection(entries)
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