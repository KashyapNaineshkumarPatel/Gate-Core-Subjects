"""
Core Logic: Gratuitous ARP (GARP) is essential for High Availability (HA) failovers in 
enterprise datacenters. When a router fails over, it blasts a broadcast GARP to force 
all clients to update their ARP tables immediately.

However, in the world of embedded IoT (battery-powered sensors running on coin cells), 
broadcast traffic is the enemy of battery life. 

When a standard OS (Linux/Windows) receives a GARP, it triggers a hardware interrupt, 
wakes the CPU, parses the Layer 2.5 payload, executes a database lookup, and updates 
its ARP cache. 

In a minimalist stack like lwIP (Lightweight IP) configured for ultra-low power, 
processing unrequested ARP traffic is a waste of CPU cycles. To mitigate this, 
engineers configure the stack with `ETHARP_TRUST_COMPILED_MAC` or strictly disable 
unsolicited ARP updates. When the IoT device's radio receives the broadcast, the 
minimalist network stack immediately drops the frame without updating its memory or 
resetting its sleep timers, prioritizing battery preservation over HA network convergence.
"""

import sys
import shutil
import time
from typing import Any, Dict

class GratuitousARPFilterEngine:
    filter_state: Dict[str, Any]

    def __init__(self) -> None:
        self.filter_state = {}
        # Known baseline Gateway
        self.gateway_ip = "192.168.1.1"
        self.original_gw_mac = "GG:AA:TT:EE:01:01"
        self.failover_gw_mac = "FF:AA:II:LL:02:02"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def execute_firmware_filtering(self, stack_type: str) -> None:
        """Simulates how different IP stacks process unrequested GARP broadcasts."""
        
        flow = []
        
        # Initial State
        arp_cache = {self.gateway_ip: self.original_gw_mac}
        cpu_cycles = 0
        battery_drain = ""
        
        flow.append(f"1. [Steady State]: Sensor ARP Cache -> {self.gateway_ip} is at {arp_cache[self.gateway_ip]}")
        flow.append("2. [Datacenter Event]: Core Router 1 dies. Router 2 assumes Default Gateway IP.")
        flow.append(f"3. [Network Fabric]: Router 2 broadcasts GARP -> 'I am {self.gateway_ip} at MAC {self.failover_gw_mac}'.")
        flow.append("4. [IoT Radio / PHY]: Receives L2 Broadcast frame. Passes to MCU IP Stack.")

        if stack_type == "1":
            # Standard POSIX / Heavy OS Stack
            flow.append("5. [Kernel / OS]: CPU Hardware Interrupt triggered. Waking CPU from Deep Sleep.")
            cpu_cycles += 5000
            flow.append("6. [ARP Module]: Parsing unrequested GARP payload.")
            cpu_cycles += 1200
            flow.append("7. [ARP Module]: Cache matched. Executing memory overwrite.")
            arp_cache[self.gateway_ip] = self.failover_gw_mac
            cpu_cycles += 800
            
            action = "CACHE OVERWRITTEN (HA Converged)"
            battery_drain = "HIGH (7,000+ Cycles Wasted)"
            insight = "A heavy OS honors the GARP, ensuring immediate routing convergence. However, if the network has high broadcast chatter, the IoT device's CPU will constantly wake up to process ARPs, draining a 10-year coin cell battery in a matter of months."
            
        else:
            # Minimalist lwIP / uIP Stack
            flow.append("5. [lwIP Stack]: CPU lightly wakes. Passes frame to low-level ethernetif_input().")
            cpu_cycles += 200
            flow.append("6. [lwIP Stack]: Frame identified as Unrequested ARP Broadcast.")
            flow.append("7. [lwIP Stack]: STRICT FILTERING ENABLED. Frame instantly dropped.")
            cpu_cycles += 50
            flow.append("8. [MCU]: CPU immediately returns to Deep Sleep (0 memory overwrites performed).")
            
            # Cache remains unchanged
            action = "FRAME DISCARDED (Cache Stale)"
            battery_drain = "MINIMAL (250 Cycles)"
            insight = "Minimalist stacks intentionally ignore GARPs. This saves massive amounts of battery, but introduces a routing flaw: when the IoT device wakes up to send its next telemetry payload, it will send it to the dead MAC address. The transmission will fail, forcing the device to timeout and execute an active ARP Request to finally learn the new MAC."

        self.filter_state = {
            "type": "Heavyweight OS (Linux/Windows)" if stack_type == "1" else "Minimalist IoT Stack (lwIP/uIP)",
            "cache": arp_cache,
            "cpu_cycles": cpu_cycles,
            "battery_drain": battery_drain,
            "flow": flow,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.filter_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AI: GRATUITOUS ARP FIRMWARE FILTERING ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] MCU FIRMWARE ARCHITECTURE : {state['type']}")
        print("-" * width)
        
        print(" [i] FIRMWARE EXECUTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] POST-GARP FIRMWARE STATE:")
        time.sleep(0.3)
        print(f"     -> Final ARP Cache  : {self.gateway_ip} -> {state['cache'][self.gateway_ip]}")
        print(f"     -> Stack Action     : [ {state['action']} ]")
        print(f"     -> Battery Impact   : {state['battery_drain']}")
        
        print("\n" + "-" * width)
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = GratuitousARPFilterEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AI_GRATUITOUS_ARP_FILTERING INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select Network Stack Architecture:")
            print("    1. Heavyweight OS (Prioritizes HA Convergence)")
            print("    2. Minimalist lwIP IoT Stack (Prioritizes Battery/Deep Sleep)")
            
            choice = input("    Select architecture (1/2) [Default: 2] : ").strip() or "2"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice not in ["1", "2"]:
                raise ValueError("Selection Error: Please choose 1 or 2.")
            
            engine.execute_firmware_filtering(choice)
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