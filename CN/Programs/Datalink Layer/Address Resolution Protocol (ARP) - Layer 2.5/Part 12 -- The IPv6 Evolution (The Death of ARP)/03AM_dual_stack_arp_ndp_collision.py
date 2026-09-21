"""
Core Logic: When enterprises transition to IPv6, they rarely hard-cut. They run 
"Dual-Stack", meaning every host has both an IPv4 address and an IPv6 address 
simultaneously active on the same physical Network Interface Card (NIC).

The Dual-Stack Race (Happy Eyeballs - RFC 8305):
When a user application (like a web browser) queries DNS for 'app.internal.corp', 
DNS returns both an A record (IPv4) and an AAAA record (IPv6). 
The OS must now resolve the Layer 2 MAC address to establish the TCP socket.

1. The OS prefers IPv6 by default. It fires an ICMPv6 NDP Neighbor Solicitation (Multicast).
2. To prevent massive delays if the IPv6 path is blackholed, the OS starts a timer 
   (typically 250ms - 300ms). 
3. If NDP hasn't resolved the IPv6 MAC within the timer, the OS concurrently fires 
   an IPv4 ARP Request (Broadcast).
4. Whichever protocol resolves the Layer 2 MAC and establishes the TCP 3-way handshake 
   first "wins" the race, and the socket binds to that IP stack.

The Chaos: On heavily congested enterprise VLANs, IPv4 ARP broadcasts often experience 
high queue latency, while IPv6 Multicast NDP cuts right through. However, if the IPv6 
first-hop router is misconfigured (e.g., bad RA timers), NDP hangs, causing a silent 
fallback to IPv4. Engineers troubleshooting this see asymmetric routing where half the 
app's connections are v4 and half are v6, creating firewall state-table chaos.
"""

import sys
import shutil
import time
import random
from typing import Any, Dict

class DualStackCollisionEngine:
    dual_state: Dict[str, Any]

    def __init__(self) -> None:
        self.dual_state = {}
        
        # Simulated Network Topology
        self.target_hostname = "database.datacenter.local"
        self.ipv4_target = "10.50.1.200"
        self.ipv6_target = "2001:db8:acad:1::200"
        
        self.ipv4_mac = "AA:BB:CC:44:44:44"
        self.ipv6_mac = "AA:BB:CC:66:66:66" # Same physical server, same MAC
        
        self.happy_eyeballs_delay_ms = 250 # RFC 8305 standard delay

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_happy_eyeballs_race(self, v4_latency_ms: int, v6_latency_ms: int) -> None:
        """Simulates the RFC 8305 Happy Eyeballs race between ARP and NDP."""
        
        flow = []
        
        flow.append(f"1. [Application]: Initiates connection to '{self.target_hostname}'.")
        flow.append(f"2. [DNS Resolver]: Returns A Record ({self.ipv4_target}) and AAAA Record ({self.ipv6_target}).")
        
        # Step 1: IPv6 is always preferred initially
        flow.append(f"3. [OS Stack]: Preference IPv6. Initiating NDP NS (Multicast) for {self.ipv6_target}.")
        
        current_time_ms = 0
        v6_resolved = False
        v4_resolved = False
        winner = ""
        action = ""
        
        # Simulated Timeline Evaluation
        if v6_latency_ms <= self.happy_eyeballs_delay_ms:
            # IPv6 wins outright before the v4 timer even triggers
            flow.append(f"4. [NDP Engine]: ICMPv6 NA received at {v6_latency_ms}ms. MAC resolved: {self.ipv6_mac}.")
            flow.append(f"5. [TCP/IP Stack]: Socket bound to IPv6. TCP Handshake complete.")
            flow.append(f"6. [Happy Eyeballs]: IPv4 ARP fallback aborted. Connection established natively over v6.")
            winner = "IPv6 (NDP)"
            action = "NATIVE IPv6 CONNECTION"
            insight = "Ideal dual-stack behavior. The IPv6 multicast path was healthy and responded within the 250ms threshold, completely suppressing legacy IPv4 broadcast traffic."
        else:
            # IPv6 is taking too long. IPv4 is fired concurrently.
            flow.append(f"4. [Happy Eyeballs]: {self.happy_eyeballs_delay_ms}ms elapsed. IPv6 NDP unresolved.")
            flow.append(f"5. [OS Stack]: Triggering concurrent IPv4 fallback. Initiating ARP (Broadcast) for {self.ipv4_target}.")
            
            # Now we race. Does V6 finish, or does V4 finish first?
            # Note: V4 started at happy_eyeballs_delay_ms. Total V4 time = happy_eyeballs_delay_ms + v4_latency_ms
            absolute_v4_completion = self.happy_eyeballs_delay_ms + v4_latency_ms
            
            if v6_latency_ms < absolute_v4_completion:
                flow.append(f"6. [NDP Engine]: ICMPv6 NA finally received at {v6_latency_ms}ms.")
                flow.append("7. [TCP/IP Stack]: Socket bound to IPv6. IPv4 socket abandoned.")
                winner = "IPv6 (Delayed NDP)"
                action = "DELAYED IPv6 CONNECTION"
                insight = "IPv6 was slow, triggering a needless IPv4 ARP broadcast across the subnet, but ultimately V6 completed the L2 resolution first. This generates phantom ARP traffic that degrades overall subnet health."
            else:
                flow.append(f"6. [ARP Engine]: IPv4 ARP Reply received at {absolute_v4_completion}ms (V4 took {v4_latency_ms}ms).")
                flow.append(f"7. [TCP/IP Stack]: Socket bound to IPv4. IPv6 socket abandoned.")
                winner = "IPv4 (ARP Fallback)"
                action = "IPv4 FALLBACK (IPv6 Blackhole/Lag)"
                insight = "Classic Dual-Stack routing chaos. The application works, so the user doesn't complain, but the firewall is now seeing legacy IPv4 traffic because the IPv6 L2 fabric (NDP) is fundamentally broken or suffering from severe multicast drops."

        self.dual_state = {
            "v4_latency": v4_latency_ms,
            "v6_latency": v6_latency_ms,
            "flow": flow,
            "winner": winner,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.dual_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AM: DUAL-STACK ARP vs NDP RACE ENGINE (RFC 8305) ".center(width))
        print("=" * width)
        
        print(" [+] RESOLUTION TIMING PARAMETERS:")
        print(f"     -> IPv6 NDP Latency   : {state['v6_latency']} ms")
        print(f"     -> IPv4 ARP Latency   : {state['v4_latency']} ms")
        print(f"     -> Fallback Threshold : {self.happy_eyeballs_delay_ms} ms (RFC 8305)")
        print("-" * width)
        
        print(" [i] HAPPY EYEBALLS EXECUTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] SOCKET BINDING OUTCOME:")
        time.sleep(0.3)
        print(f"     -> Winning Stack    : {state['winner']}")
        print(f"     -> Dataplane State  : [ {state['action']} ]")
        
        print("\n" + "-" * width)
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = DualStackCollisionEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AM_DUAL_STACK_ARP_NDP_COLLISION INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Dual-Stack Latency (in milliseconds):")
            print("    (Tip: Try V6=50, V4=50 for native IPv6. Try V6=300, V4=20 for a V4 Fallback event.)")
            
            v6_in = input("    IPv6 NDP Multicast Latency (ms) [Default: 50]  : ").strip() or "50"
            if v6_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            v4_in = input("    IPv4 ARP Broadcast Latency (ms) [Default: 50]  : ").strip() or "50"
            
            v6_lat = int(v6_in)
            v4_lat = int(v4_in)
            
            if v6_lat < 0 or v4_lat < 0:
                raise ValueError("Latency cannot be negative.")
            
            engine.execute_happy_eyeballs_race(v4_lat, v6_lat)
            engine.render_ui()
            
        except ValueError:
            print(f"\n[X] INTERCEPT TRIGGERED:\n    Please enter valid positive integer milliseconds.")
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()