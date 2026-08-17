import sys
import re
import shutil
import time
import random
from typing import Any, Dict, List, Tuple

class ICMPTracerouteEngine:
    trace_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.trace_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, target_ip: str, max_hops_str: str, probes_per_hop_str: str, mode_str: str) -> Tuple[str, int, int, str]:
        # IP Validation
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ip_pattern, target_ip)
        if not match:
            raise ValueError("Syntax Error: Target IP format invalid (e.g., 8.8.8.8).")
        for idx, octet_str in enumerate(match.groups()):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        # Max Hops and Probes Validation
        try:
            max_hops = int(max_hops_str)
            probes = int(probes_per_hop_str)
        except ValueError:
            raise ValueError("Type Error: Max hops and probes per hop must be integers.")

        if max_hops < 1 or max_hops > 64:
            raise ValueError("Bounds Error: Max TTL / Hops must be between 1 and 64.")

        if probes < 1 or probes > 5:
            raise ValueError("Bounds Error: Probes per hop must be between 1 and 5.")

        mode = mode_str.strip().lower()
        if mode not in ['icmp', 'udp']:
            raise ValueError("Syntax Error: Traceroute mode must be 'icmp' (Windows tracert) or 'udp' (Linux/Unix traceroute).")

        return target_ip, max_hops, probes, mode

    def simulate_traceroute(self, target_ip: str, max_hops: int, probes: int, mode: str) -> None:
        """Simulates TTL decrementation across Layer 3 hops, Type 11 Code 0 generation, and RTT collection."""
        
        # Mocking an autonomous system topology path
        actual_path_length = min(random.randint(5, 12), max_hops)
        
        # Generate simulated router IPs along the path
        simulated_hops = []
        for i in range(1, actual_path_length):
            simulated_hops.append(f"198.51.{i}.{random.randint(1, 254)}")
        simulated_hops.append(target_ip)  # Destination is the final hop

        hop_records: List[Dict[str, Any]] = []
        destination_reached = False

        for ttl in range(1, max_hops + 1):
            hop_idx = ttl - 1
            if hop_idx < len(simulated_hops):
                hop_ip = simulated_hops[hop_idx]
                is_target = (hop_ip == target_ip)
            else:
                hop_ip = "*"
                is_target = False

            # Simulate probe RTTs and packet drops
            rtt_samples: List[str] = []
            for _ in range(probes):
                # 5% chance of timeout on transit routers
                if hop_ip == "*" or (random.random() < 0.05 and not is_target):
                    rtt_samples.append("*")
                else:
                    base_delay = ttl * random.uniform(2.5, 6.0)
                    jitter = random.uniform(-1.0, 3.5)
                    latency = max(0.5, base_delay + jitter)
                    rtt_samples.append(f"{latency:.2f} ms")

            if is_target:
                destination_reached = True
                if mode == 'icmp':
                    status = "Type 0, Code 0 (Echo Reply)"
                else:
                    status = "Type 3, Code 3 (Port Unreachable - UDP High Port)"
                
                hop_records.append({
                    "ttl": ttl,
                    "ip": hop_ip,
                    "rtts": rtt_samples,
                    "status": status,
                    "action": "DESTINATION REACHED"
                })
                break
            elif hop_ip != "*":
                status = "Type 11, Code 0 (Time-to-Live Exceeded in Transit)"
                hop_records.append({
                    "ttl": ttl,
                    "ip": hop_ip,
                    "rtts": rtt_samples,
                    "status": status,
                    "action": "TTL EXPIRED -> ICMP TYPE 11 EMITTED"
                })
            else:
                hop_records.append({
                    "ttl": ttl,
                    "ip": "* * * (Request Timed Out)",
                    "rtts": rtt_samples,
                    "status": "SILENT / DROP",
                    "action": "NO ICMP RETURNED (Firewall/Rate Limit)"
                })

        # Security & Architectural Insight
        insight = (
            f"TTL TOPOLOGY INFERENCE (RFC 792 & RFC 1393): Traceroute does not use a special discovery packet. "
            f"It relies on the fundamental IPv4 TTL-decrement rule: each L3 router decrements the 8-bit TTL field by 1. "
            f"When TTL reaches 0, the router discards the frame and sends ICMP Type 11 Code 0 to the source. "
            f"By incrementally incrementing TTL from 1 to {len(hop_records)}, the initiator maps out intermediate routing silicon. "
            f"Mode used: {mode.upper()} ({'Echo Request/Reply' if mode == 'icmp' else 'High UDP Port [33434+] triggering Port Unreachable'})."
        )

        # Update State Tree
        self.trace_state = {
            "target": target_ip,
            "max_hops": max_hops,
            "probes": probes,
            "mode": mode,
            "reached": destination_reached,
            "hops": hop_records,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.trace_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03O: ICMP TIME EXCEEDED TRACEROUTE (TYPE 11, CODE 0) ".center(width))
        print("=" * width)
        
        print(f" [+] Traceroute Destination : {state['target']}")
        print(f" [+] Max TTL Boundary       : {state['max_hops']} hops | Probes per Hop: {state['probes']}")
        print(f" [+] Probing Mechanism      : {state['mode'].upper()} Protocol Dialect")
        print("-" * width)
        
        print(f" {'TTL':<4} | {'ROUTER IP / HOSTNAME':<24} | {'PROBE LATENCIES':<28} | {'ICMP FEEDBACK RECEIVED'}")
        print("-" * width)
        
        for h in state['hops']:
            time.sleep(0.12)  # Simulate hop-by-hop resolution
            rtt_str = "  ".join(h['rtts'])
            print(f" {h['ttl']:<4} | {h['ip']:<24} | {rtt_str:<28} | {h['status']}")
            
        print("-" * width)
        print(f" [!] TRACEROUTE STATUS: {'TARGET CONVERGED' if state['reached'] else 'MAX HOPS EXCEEDED'}")
        print(f" [!] ARCHITECTURAL & TOPOLOGY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPTracerouteEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03O_ICMP_TIME_EXCEEDED_TRACEROUTE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure Hop-by-Hop Topology Trace:")
            target_in = input("    Target Destination IP (e.g., 8.8.8.8)       : ").strip()
            if target_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not target_in: continue
            
            hops_in   = input("    Maximum Hops (Max TTL, e.g., 30)           : ").strip()
            prb_in    = input("    Probes per Hop (e.g., 3)                   : ").strip()
            mode_in   = input("    Protocol Mode (icmp = Windows, udp = Linux): ").strip()
                
            tgt, hops, prbs, mode = engine.validate_inputs(target_in, hops_in, prb_in, mode_in)
            engine.simulate_traceroute(tgt, hops, prbs, mode)
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