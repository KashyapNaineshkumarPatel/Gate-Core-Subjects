import sys
import re
import shutil
import time
import math
from typing import Any, Dict, Tuple

class ICMPSourceQuenchEngine:
    quench_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.quench_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, router_ip: str, ingress_rate_str: str, buffer_capacity_str: str) -> Tuple[str, int, int]:
        # IP Validation
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ip_pattern, router_ip)
        if not match:
            raise ValueError("Syntax Error: Router IP format invalid (e.g., 10.0.0.1).")
        for idx, octet_str in enumerate(match.groups()):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        # Rate and Buffer Validation
        try:
            ingress_rate = int(ingress_rate_str)
            buffer_capacity = int(buffer_capacity_str)
        except ValueError:
            raise ValueError("Type Error: Ingress rate and Buffer capacity must be integers.")

        if ingress_rate < 1 or ingress_rate > 100000:
            raise ValueError("Bounds Error: Ingress rate (packets/sec) should be between 1 and 100,000 for this simulation.")
            
        if buffer_capacity < 100 or buffer_capacity > 50000:
            raise ValueError("Bounds Error: Router buffer capacity (packets) should be between 100 and 50,000.")

        return router_ip, ingress_rate, buffer_capacity

    def simulate_source_quench(self, router_ip: str, ingress_rate: int, buffer_capacity: int) -> None:
        """The Legacy Congestion Engine: Simulates router queue saturation and ICMP Type 4 emission."""
        
        # ICMP Source Quench Parameters
        icmp_type = 4
        icmp_code = 0
        
        # Simulation Logic: Router processes packets at a fixed egress rate
        egress_rate = int(buffer_capacity * 0.8) # Router can clear 80% of its buffer per second
        
        # Calculate buffer state after 1 second of burst traffic
        net_flow = ingress_rate - egress_rate
        
        events = []
        is_quenched = False
        packets_dropped = 0
        quench_emitted = 0
        
        events.append(f"[T=0.0s] Ingress Rate: {ingress_rate} pps | Egress Rate: {egress_rate} pps")
        
        if net_flow <= 0:
            events.append("[T=1.0s] Buffer Status: Stable. Ingress traffic is being routed successfully.")
            insight = "OPTIMAL: Router queue is handling traffic loads within hardware limitations. No ICMP required."
            action = "FORWARD_ALL"
        else:
            # Buffer is filling up
            buffer_utilization = min(net_flow, buffer_capacity)
            util_pct = (buffer_utilization / buffer_capacity) * 100
            events.append(f"[T=1.0s] Buffer Status: Utilization at {util_pct:.1f}% ({buffer_utilization}/{buffer_capacity} packets).")
            
            # RFC 792 dictates Source Quench is sent when a router is *approaching* or *has reached* capacity.
            # We trigger Quench at >90% capacity or if dropping occurs.
            if net_flow > buffer_capacity:
                is_quenched = True
                packets_dropped = net_flow - buffer_capacity
                # In legacy implementations, a router might send 1 Source Quench for every N dropped packets
                quench_emitted = math.ceil(packets_dropped / 10) 
                
                events.append(f"[T=1.1s] HARDWARE EXHAUSTION: Buffer overflowed. {packets_dropped} packets dropped (Tail Drop).")
                events.append(f"[T=1.2s] CONTROL PLANE REACTION: Emitted {quench_emitted} ICMP Type 4 (Source Quench) packets to originators.")
                
                action = "DROP_AND_QUENCH"
                insight = (
                    "LEGACY DESIGN FLAW: Generating thousands of ICMP Source Quench packets during severe congestion "
                    "forces the router's CPU to work harder exactly when it is overwhelmed. "
                    "This creates a feedback loop that crashes the router. "
                    "RFC 6633 formally deprecated Source Quench. Modern networks rely on TCP window sliding and ECN (Explicit Congestion Notification)."
                )
            elif util_pct > 90:
                is_quenched = True
                quench_emitted = 5 # Preventative quench
                events.append(f"[T=1.1s] EARLY WARNING: Buffer >90%. Emitting preventative ICMP Type 4 (Source Quench).")
                action = "FORWARD_AND_QUENCH"
                insight = "WARNING THRESHOLD: Router warns hosts to back off transmission rates before dropping packets."
            else:
                events.append("[T=1.1s] Queue absorbing burst. Traffic forwarded with increased queuing delay.")
                action = "QUEUE_AND_FORWARD"
                insight = "BURST ABSORBED: Traffic spike absorbed by hardware buffer. TCP will naturally handle the increased RTT."

        # Encapsulated Original IP Header (Simulated for Autopsy)
        encapsulated_hdr = "Ver/IHL: 0x45, Total Len: 1500, Proto: 6 (TCP), Src: 10.50.1.5 -> Dst: Target" if is_quenched else "N/A"

        # Update State Tree
        self.quench_state = {
            "router_ip": router_ip,
            "ingress": ingress_rate,
            "egress": egress_rate,
            "capacity": buffer_capacity,
            "action": action,
            "is_quenched": is_quenched,
            "dropped": packets_dropped,
            "quench_count": quench_emitted,
            "events": events,
            "encapsulated": encapsulated_hdr,
            "insight": insight,
            "type": icmp_type,
            "code": icmp_code
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.quench_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03J: ICMP SOURCE QUENCH THROTTLE (TYPE 4) ".center(width))
        print("=" * width)
        
        print(f" [+] Congested Router IP : {state['router_ip']}")
        print(f" [+] Hardware Limits     : {state['capacity']} packet buffer | {state['egress']} pps egress capacity")
        print("-" * width)
        
        print(" [i] ROUTER QUEUE / BUFFER TRAVERSAL LOG:")
        for event in state['events']:
            time.sleep(0.15)
            print(f"     -> {event}")
            
        print("-" * width)
        
        if state['is_quenched']:
            print(f" [!] ICMP AUTOPSY EMISSION: Type {state['type']} | Code {state['code']} (Source Quench)")
            print(f"     -> ICMP Packets Sent : {state['quench_count']} packets")
            print(f"     -> Packet Loss (Drop): {state['dropped']} packets")
            print(f"     -> Encapsulation     : {state['encapsulated']} + First 8 Bytes")
            print("-" * width)
            
        print(f" [!] ARCHITECTURAL & DEPRECATION INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPSourceQuenchEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03J_ICMP_SOURCE_QUENCH_THROTTLE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure Router Congestion Parameters:")
            router_in = input("    Core Router IP        (e.g., 10.0.0.254): ").strip()
            if router_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not router_in: continue
            
            in_rate_in  = input("    Ingress Traffic Burst (Packets/Sec)     : ").strip()
            buffer_in   = input("    Router NIC Buffer Size (Packets)        : ").strip()
                
            router, in_rate, buffer = engine.validate_inputs(router_in, in_rate_in, buffer_in)
            engine.simulate_source_quench(router, in_rate, buffer)
            engine.render_ui()
            
        except ValueError as ve:
            print(f"\n[X] INTERCEPT TRIGGERED:\n    {ve}")
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Safely spinning down engine...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()