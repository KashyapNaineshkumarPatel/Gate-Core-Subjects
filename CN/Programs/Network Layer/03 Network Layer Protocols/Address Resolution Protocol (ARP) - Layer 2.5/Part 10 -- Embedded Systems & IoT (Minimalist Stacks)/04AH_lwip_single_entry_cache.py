"""
Core Logic: Modern operating systems (Linux, Windows) allocate megabytes of RAM 
to network state, allowing them to store thousands of dynamic ARP entries. 

Embedded IoT devices (like ESP32 or STM32 microcontrollers) run Lightweight IP 
(lwIP) or uIP stacks where RAM is severely constrained (e.g., 32KB total SRAM). 
To save memory, lwIP often compiles with an ARP cache limited to just 1 or 2 entries.

The Thrashing Penalty:
If an IoT sensor needs to alternate between sending telemetry to a Local Edge Server 
(IP A) and polling an NTP Time Server via the Default Gateway (IP B), a 1-entry ARP 
cache becomes a massive bottleneck.
1. Sensor wants to reach IP A. Cache Miss. Broadcasts ARP. Learns MAC A. Sends Data.
2. Sensor wants to reach IP B. Cache Full. Evicts MAC A. Broadcasts ARP. Learns MAC B. Sends Data.
3. Sensor wants to reach IP A again. Cache Full. Evicts MAC B. Broadcasts ARP.

This creates "ARP Thrashing"—where the IoT device wastes precious battery life, 
CPU cycles, and RF airtime continuously re-resolving the exact same two devices 
because it literally lacks the RAM to remember both simultaneously.
"""

import sys
import shutil
import time
from typing import Any, Dict

class LwIPARPEngine:
    lwip_state: Dict[str, Any]

    def __init__(self) -> None:
        self.lwip_state = {}
        # Hardware Constraint: 1 Entry Maximum
        self.arp_cache_size = 1
        self.arp_cache: Dict[str, str] = {}
        
        # Topology
        self.sensor_ip = "192.168.1.100"
        self.edge_server = {"ip": "192.168.1.10", "mac": "EE:DD:GG:EE:10:10"}
        self.gateway = {"ip": "192.168.1.1", "mac": "GG:AA:TT:EE:01:01"}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def execute_iot_thrashing(self, iterations: int) -> None:
        """Simulates ARP thrashing in a memory-constrained embedded IP stack."""
        
        flow = []
        arp_broadcasts = 0
        payload_transmissions = 0
        
        # Traffic Pattern: Alternate between Edge Server and Gateway
        targets = [self.edge_server, self.gateway]
        
        for i in range(iterations):
            target = targets[i % 2]
            target_ip = target["ip"]
            target_mac = target["mac"]
            
            flow.append(f"\n   [Cycle {i+1}] Sensor application requests transmission to {target_ip}")
            
            if target_ip in self.arp_cache:
                flow.append(f"   -> [lwIP]: Cache HIT for {target_ip}. Direct transmission.")
                payload_transmissions += 1
            else:
                flow.append(f"   -> [lwIP]: Cache MISS. Target not in SRAM.")
                
                if len(self.arp_cache) >= self.arp_cache_size:
                    evicted_ip = list(self.arp_cache.keys())[0]
                    del self.arp_cache[evicted_ip]
                    flow.append(f"   -> [lwIP]: Cache FULL. Evicting {evicted_ip} to free memory.")
                
                flow.append(f"   -> [Radio/PHY]: Transmitting ARP Broadcast for {target_ip}.")
                arp_broadcasts += 1
                
                flow.append(f"   -> [lwIP]: ARP Reply received. Caching {target_ip} -> {target_mac}.")
                self.arp_cache[target_ip] = target_mac
                
                flow.append("   -> [Radio/PHY]: Transmitting IP Payload.")
                payload_transmissions += 1

        total_tx = arp_broadcasts + payload_transmissions
        efficiency = (payload_transmissions / total_tx) * 100 if total_tx > 0 else 0

        insight = (
            f"Thrashing state reached. The radio was forced to transmit {arp_broadcasts} "
            f"ARP broadcasts just to deliver {payload_transmissions} payloads. "
            "In embedded IoT engineering, if you cannot increase the ARP table size via `ARP_TABLE_SIZE` "
            "in lwipopts.h, the software architecture must be redesigned to batch all communications "
            "to a single IP destination (like an MQTT broker) to lock the cache entry."
        )

        self.lwip_state = {
            "iterations": iterations,
            "cache_size": self.arp_cache_size,
            "final_cache": self.arp_cache,
            "arp_count": arp_broadcasts,
            "payload_count": payload_transmissions,
            "efficiency": efficiency,
            "flow": flow,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.lwip_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AH: EMBEDDED LwIP ARP THRASHING ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] IoT HARDWARE CONSTRAINTS:")
        print(f"     -> Max ARP Table Size : {state['cache_size']} Entry (SRAM Limited)")
        print(f"     -> Current Cache State: {state['final_cache']}")
        print("-" * width)
        
        print(" [i] lwIP FIRMWARE EXECUTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.1)
            print(step)
        print("\n" + "-" * width)
        
        print(" [!] BATTERY & AIRTIME METRICS:")
        time.sleep(0.3)
        print(f"     -> Total Payloads Sent : {state['payload_count']}")
        print(f"     -> Wasted ARP Requests : {state['arp_count']}")
        print(f"     -> Airtime Efficiency  : {state['efficiency']:.1f}% (Ideal is > 99%)")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = LwIPARPEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AH_LWIP_SINGLE_ENTRY_CACHE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Alternating Traffic Patterns:")
            print("    (Tip: Try 6 iterations to see the cache thrash back and forth)")
            
            iter_in = input("    Number of TX iterations [Default: 6] : ").strip() or "6"
            if iter_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            iterations = int(iter_in)
            if iterations <= 0:
                raise ValueError("Must be positive integer.")
            
            engine.execute_iot_thrashing(iterations)
            engine.render_ui()
            
        except ValueError:
            print(f"\n[X] INTERCEPT TRIGGERED:\n    Please enter a valid positive integer.")
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()