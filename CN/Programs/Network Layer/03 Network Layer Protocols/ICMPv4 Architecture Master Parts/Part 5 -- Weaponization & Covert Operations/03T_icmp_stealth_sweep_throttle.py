import sys
import re
import shutil
import time
import random
from typing import Any, Dict, List, Tuple

class ICMPStealthSweepEngine:
    sweep_state: Dict[str, Any]

    def __init__(self) -> None:
        self.sweep_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(
        self,
        target_subnet: str,
        probe_delay_ms_str: str,
        jitter_pct_str: str,
        token_bucket_capacity_str: str,
        refill_rate_pps_str: str,
        ids_threshold_pps_str: str
    ) -> Tuple[str, float, float, int, int, int]:
        # Subnet validation (e.g. 192.168.1.0/28 or /24)
        subnet_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})$'
        match = re.match(subnet_pattern, target_subnet)
        if not match:
            raise ValueError("Syntax Error: Target subnet must be in CIDR notation (e.g., 10.0.0.0/28).")
        
        octets = match.groups()[:4]
        cidr = int(match.groups()[4])
        for idx, octet_str in enumerate(octets):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")
        
        if cidr < 24 or cidr > 30:
            raise ValueError("Bounds Error: For simulation scaling, CIDR prefix must be between /24 and /30.")

        try:
            probe_delay = float(probe_delay_ms_str)
            jitter_pct = float(jitter_pct_str)
            bucket_cap = int(token_bucket_capacity_str)
            refill_rate = int(refill_rate_pps_str)
            ids_threshold = int(ids_threshold_pps_str)
        except ValueError:
            raise ValueError("Type Error: Numeric timing and rate parameters must be valid numbers.")

        if probe_delay < 0.0 or probe_delay > 10000.0:
            raise ValueError("Bounds Error: Probe delay must be between 0 and 10,000 ms.")

        if jitter_pct < 0.0 or jitter_pct > 100.0:
            raise ValueError("Bounds Error: Jitter percentage must be between 0% and 100%.")

        if bucket_cap < 1 or bucket_cap > 1000:
            raise ValueError("Bounds Error: Token bucket capacity must be between 1 and 1000.")

        if refill_rate < 1 or refill_rate > 1000:
            raise ValueError("Bounds Error: Refill rate must be between 1 and 1000 pps.")

        if ids_threshold < 1 or ids_threshold > 1000:
            raise ValueError("Bounds Error: IDS alert threshold must be between 1 and 1000 pps.")

        return target_subnet, probe_delay, jitter_pct, bucket_cap, refill_rate, ids_threshold

    def simulate_sweep(
        self,
        subnet: str,
        probe_delay_ms: float,
        jitter_pct: float,
        bucket_cap: int,
        refill_rate: int,
        ids_threshold: int
    ) -> None:
        """Simulates token-bucket leaky algorithm enforcement, stealth sweeping, and IDS alert triggers."""
        
        match = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3})\.\d{1,3}/(\d{1,2})$', subnet)
        if not match:
            return
        prefix = match.group(1)
        cidr = int(match.group(2))
        
        num_hosts = 2 ** (32 - cidr) - 2
        host_ips = [f"{prefix}.{i}" for i in range(1, min(num_hosts + 1, 15))] # Cap display at 14 for clean output

        tokens = float(bucket_cap)
        last_time = 0.0
        current_time = 0.0

        probes_log: List[Dict[str, Any]] = []
        ids_alerts: List[Dict[str, Any]] = []

        active_hosts = {f"{prefix}.{random.randint(1, len(host_ips))}": True for _ in range(max(1, len(host_ips) // 3))}

        window_probes: List[float] = []

        for target_ip in host_ips:
            # Apply jitter to delay
            jitter_range = (jitter_pct / 100.0) * probe_delay_ms
            actual_delay_ms = max(0.0, probe_delay_ms + random.uniform(-jitter_range, jitter_range))
            time_delta_sec = actual_delay_ms / 1000.0
            
            current_time += time_delta_sec

            # Token Bucket Refill Calculation: Tokens += DeltaTime * RefillRate
            tokens = min(float(bucket_cap), tokens + (current_time - last_time) * refill_rate)
            last_time = current_time

            # Rate Limiter Decision
            if tokens >= 1.0:
                tokens -= 1.0
                rate_limited = False
            else:
                rate_limited = True

            # IDS Window Inspection (Sliding 1-second window)
            window_probes.append(current_time)
            window_probes = [t for t in window_probes if current_time - t <= 1.0]
            current_pps = len(window_probes)

            ids_triggered = current_pps >= ids_threshold

            if ids_triggered:
                ids_alerts.append({
                    "time": f"+{current_time:.3f}s",
                    "rate": current_pps,
                    "target": target_ip
                })

            if rate_limited:
                status = "DROPPED (Target OS Rate-Limiter / Token Bucket Exhausted)"
                response = "No ICMP Reply (Throttled by Kernel)"
            elif target_ip in active_hosts:
                status = "PROBE DELIVERED"
                response = "ICMP Type 0, Code 0 (Echo Reply Received)"
            else:
                status = "PROBE DELIVERED"
                response = "Request Timed Out (Host Inactive / Filtered)"

            probes_log.append({
                "time_offset": f"+{current_time:.3f}s",
                "ip": target_ip,
                "delay_ms": round(actual_delay_ms, 1),
                "tokens_left": round(tokens, 2),
                "rate_pps": current_pps,
                "status": status,
                "response": response
            })

        # Architectural and Defensive Insight
        if ids_alerts:
            insight = (
                f"IDS ALERT TRIGGERED: Probe rate reached {max(a['rate'] for a in ids_alerts)} pps, exceeding "
                f"the configured threshold of {ids_threshold} pps. "
                "Network Security Monitoring (Suricata/Snort) flagged the host for horizontal ICMP sweep scanning. "
                "To evade detection, increase probe delay and apply randomized non-linear jitter (>30%)."
            )
        else:
            insight = (
                f"STEALTH RECONNAISSANCE CONVERGED: Sweep maintained an effective rate of "
                f"< {ids_threshold} pps with {jitter_pct}% jitter. "
                "All probes traversed beneath the IDS heuristic threshold without triggering rate alarms. "
                "Defensive mitigation: Implement kernel-level token-bucket rate limiting (e.g. `icmp_ratelimit`) "
                "and deploy stateful anomaly inspection based on Shannon dispersion rather than fixed rate counters."
            )

        self.sweep_state = {
            "subnet": subnet,
            "hosts_scanned": len(host_ips),
            "probe_delay": probe_delay_ms,
            "jitter": jitter_pct,
            "bucket_cap": bucket_cap,
            "refill_rate": refill_rate,
            "ids_threshold": ids_threshold,
            "probes": probes_log,
            "alerts": ids_alerts,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.2)
        width = self.get_terminal_width()
        state = self.sweep_state

        print("\n" + "=" * width)
        print(" [>] MODULE 03T: ICMP STEALTH SWEEP & RATE-LIMIT THROTTLE ".center(width))
        print("=" * width)

        print(f" [+] Target CIDR Subnet   : {state['subnet']} ({state['hosts_scanned']} hosts in sweep)")
        print(f" [+] Configured Timers    : Base Delay = {state['probe_delay']} ms | Jitter = {state['jitter']}%")
        print(f" [+] Kernel Token Bucket  : Capacity = {state['bucket_cap']} tokens | Refill = {state['refill_rate']} tokens/sec")
        print(f" [+] IDS Rule Threshold   : {state['ids_threshold']} ICMP pps (Sliding 1.0s Window)")
        print("-" * width)

        print(f" {'TIMESTAMP':<11} | {'TARGET IP':<16} | {'DELAY':<9} | {'TOKENS':<8} | {'PPS':<5} | {'OUTCOME / ICMP FEEDBACK'}")
        print("-" * width)

        for p in state['probes']:
            time.sleep(0.08)
            print(f" {p['time_offset']:<11} | {p['ip']:<16} | {str(p['delay_ms']) + 'ms':<9} | {p['tokens_left']:<8} | {p['rate_pps']:<5} | {p['response']}")

        print("-" * width)
        if state['alerts']:
            print(f" [!] IDS SIGNATURE ALERTS GENERATED: {len(state['alerts'])} instances")
            for alert in state['alerts']:
                print(f"     -> [ALERT @ {alert['time']}] ICMP Sweep detected against {alert['target']} (Current Rate: {alert['rate']} pps)")
        else:
            print(" [i] IDS SIGNATURE STATUS: ZERO ALERTS (Stealth Profile Maintained Below Threshold)")

        print("-" * width)
        print(" [!] ARCHITECTURAL & EVASION/DEFENSE ANALYSIS:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPStealthSweepEngine()
    width = engine.get_terminal_width()

    print("\n" + "=" * width)
    print(" 03T_ICMP_STEALTH_SWEEP_THROTTLE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Enter ICMP Stealth Sweep & Throttle Parameters:")
            sub_in   = input("    Target CIDR Subnet         (e.g., 10.0.0.0/28) : ").strip()
            if sub_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not sub_in: continue

            delay_in = input("    Base Probe Delay (ms)      (e.g., 250)         : ").strip()
            jit_in   = input("    Random Jitter Percentage   (e.g., 20 for 20%)  : ").strip()
            cap_in   = input("    Token Bucket Capacity      (e.g., 5)           : ").strip()
            ref_in   = input("    Bucket Refill Rate (pps)   (e.g., 2)           : ").strip()
            ids_in   = input("    IDS Alert Threshold (pps)  (e.g., 4)           : ").strip()

            sub, delay, jit, cap, ref, ids = engine.validate_inputs(
                sub_in, delay_in, jit_in, cap_in, ref_in, ids_in
            )
            engine.simulate_sweep(sub, delay, jit, cap, ref, ids)
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