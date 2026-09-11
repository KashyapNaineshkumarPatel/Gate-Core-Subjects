"""
Core Logic: In wired Ethernet, a switch isolates collision domains, meaning an ARP 
broadcast on a 1 Gbps port consumes negligible bandwidth and does not impact other 
active ports.

Wi-Fi (IEEE 802.11) is entirely different. It is a shared, half-duplex medium 
utilizing CSMA/CA (Carrier Sense Multiple Access with Collision Avoidance). 

The Broadcast Penalty:
When an Access Point (AP) transmits a Unicast frame, it negotiates the fastest 
possible speed with that specific client (e.g., 300 Mbps via 802.11ac/ax).
However, when a host sends an ARP Broadcast, the AP must ensure every single 
client in the physical cell can hear it—even the client furthest away behind a wall. 
To guarantee delivery, 802.11 mandates that all Broadcasts and Multicasts must be 
transmitted at the Lowest Mandatory Basic Rate configured on the AP (typically 
legacy 1 Mbps or 6 Mbps).

Because Wi-Fi is half-duplex, while the AP is transmitting ARPs at 1 Mbps, the 
entire channel is locked. No other device can speak. In a dense environment (like 
a university lecture hall or a stadium), standard background ARP chatter from 
hundreds of devices gets flooded at 1 Mbps, rapidly consuming 100% of the available 
airtime and causing a complete network collapse, even if the "bandwidth" is technically free.
"""

import sys
import shutil
import time
from typing import Any, Dict

class WiFiARPStormEngine:
    wifi_state: Dict[str, Any]

    def __init__(self) -> None:
        self.wifi_state = {}
        # 802.11 + L2 + ARP Payload roughly = 100 Bytes = 800 bits
        self.frame_bits = 800 
        # CSMA/CA Overhead (DIFS + Preamble + Contention Window) roughly 0.5ms per frame
        self.csmaca_overhead_ms = 0.5  

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def validate_int(self, val_input: str, name: str) -> int:
        try:
            val = int(val_input.strip())
            if val <= 0:
                raise ValueError()
            return val
        except ValueError:
            raise ValueError(f"Bounds Error: {name} must be a positive integer.")

    def execute_airtime_physics(self, arp_pps: int, basic_rate_mbps: int, unicast_rate_mbps: int) -> None:
        """Simulates the 802.11 airtime consumption of Unicast vs Broadcast frames."""
        
        flow = []
        
        flow.append(f"1. [WLAN Controller]: Configured Lowest Mandatory Basic Rate: {basic_rate_mbps} Mbps.")
        flow.append(f"2. [WLAN Controller]: Configured Peak Unicast MCS Rate: {unicast_rate_mbps} Mbps.")
        flow.append(f"3. [Wireless Cell]: {arp_pps} ARP Broadcasts generated per second across the BSSID.")
        
        # Calculate Unicast Airtime (Hypothetical: if ARP was unicast)
        unicast_tx_time_ms = (self.frame_bits / (unicast_rate_mbps * 1000000)) * 1000
        unicast_total_ms = (unicast_tx_time_ms + self.csmaca_overhead_ms) * arp_pps
        
        # Calculate Broadcast Airtime (The Reality)
        broadcast_tx_time_ms = (self.frame_bits / (basic_rate_mbps * 1000000)) * 1000
        broadcast_total_ms = (broadcast_tx_time_ms + self.csmaca_overhead_ms) * arp_pps
        
        flow.append("4. [Airtime Physics]: Calculating CSMA/CA + TX time for Unicast vs Broadcast.")
        flow.append(f"   -> Unicast Frame TX Time   : {unicast_tx_time_ms:.4f} ms")
        flow.append(f"   -> Broadcast Frame TX Time : {broadcast_tx_time_ms:.4f} ms")
        
        # Evaluate 1-Second Airtime Budget
        if broadcast_total_ms >= 1000:
            action = "CELL COLLAPSE (Airtime Exhausted)"
            color = "CRITICAL FAILURE - 100% CHANNEL UTILIZATION"
            flow.append("5. [Access Point]: Channel locked by slow-speed broadcast transmission.")
            flow.append("6. [Clients]: CSMA/CA carrier sense fails. All clients defer transmission. Network frozen.")
            insight = "When broadcast airtime exceeds 1000ms per second, the cell is mathematically dead. This is why enterprise engineers completely disable 1 Mbps, 2 Mbps, and 5.5 Mbps 802.11b rates, pushing the Basic Rate to 12 Mbps or 24 Mbps."
        else:
            action = "CELL SURVIVED (Airtime Available)"
            color = "NOMINAL / DEGRADED"
            flow.append("5. [Access Point]: Broadcasts consumed portion of the 1-second budget.")
            flow.append("6. [Clients]: Remaining airtime available for high-speed Unicast data.")
            insight = "By tuning the Lowest Mandatory Rate upward, the physical transmission time of the ARP frames shrinks, freeing up the half-duplex channel for actual data."

        self.wifi_state = {
            "arp_pps": arp_pps,
            "basic_rate": basic_rate_mbps,
            "unicast_rate": unicast_rate_mbps,
            "unicast_total": unicast_total_ms,
            "broadcast_total": broadcast_total_ms,
            "flow": flow,
            "action": action,
            "color": color,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.wifi_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AE: 802.11 ARP BROADCAST STORM ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] RF CHANNEL PARAMETERS (1-SECOND BUDGET):")
        print(f"     -> Load                : {state['arp_pps']} Packets Per Second")
        print(f"     -> Broadcast TX Rate   : {state['basic_rate']} Mbps")
        print(f"     -> Unicast TX Rate     : {state['unicast_rate']} Mbps")
        print("-" * width)
        
        print(" [i] 802.11 MAC LAYER EXECUTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] AIRTIME UTILIZATION METRICS (Total ms used per second):")
        time.sleep(0.3)
        
        print(f"     -> If sent as Unicast  : {state['unicast_total']:.1f} ms / 1000 ms")
        print(f"     -> Actual Broadcasts   : {state['broadcast_total']:.1f} ms / 1000 ms")
        
        print(f"\n     -> Dataplane Outcome   : [ {state['action']} ]")
        print(f"     -> RF Fabric State     : {state['color']}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = WiFiARPStormEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AE_WIFI_ARP_BROADCAST_STORM INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Wi-Fi Airtime Load:")
            print("    (Tip: Leave defaults to see how 500 ARPs/sec at 1 Mbps destroys a network)")
            
            pps_in = input("    ARP Broadcasts Per Second [Default: 500] : ").strip() or "500"
            if pps_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            br_in = input("    Lowest Basic Rate (Mbps)  [Default: 1]   : ").strip() or "1"
            ur_in = input("    High-Speed Unicast (Mbps) [Default: 300] : ").strip() or "300"
            
            pps = engine.validate_int(pps_in, "PPS")
            basic_rate = engine.validate_int(br_in, "Basic Rate")
            unicast_rate = engine.validate_int(ur_in, "Unicast Rate")
            
            engine.execute_airtime_physics(pps, basic_rate, unicast_rate)
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