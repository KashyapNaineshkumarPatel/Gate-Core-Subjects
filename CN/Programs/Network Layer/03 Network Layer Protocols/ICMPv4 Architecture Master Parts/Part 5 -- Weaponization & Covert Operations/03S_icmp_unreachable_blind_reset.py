import sys
import re
import shutil
import time
from typing import Any, Dict, List, Tuple

class ICMPBlindResetDefenseEngine:
    reset_state: Dict[str, Any]

    def __init__(self) -> None:
        self.reset_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(
        self,
        src_ip: str,
        dst_ip: str,
        sport_str: str,
        dport_str: str,
        claimed_seq_str: str,
        rcv_nxt_str: str,
        rcv_wnd_str: str,
        rfc5927_enabled_str: str
    ) -> Tuple[str, str, int, int, int, int, int, bool]:
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        for ip, label in [(src_ip, "Source IP"), (dst_ip, "Destination IP")]:
            match = re.match(ip_pattern, ip)
            if not match:
                raise ValueError(f"Syntax Error: {label} format invalid (e.g., 192.168.1.10).")
            for idx, octet_str in enumerate(match.groups()):
                if int(octet_str) > 255:
                    raise ValueError(f"Architecture Error: {label} Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        try:
            sport = int(sport_str)
            dport = int(dport_str)
            claimed_seq = int(claimed_seq_str)
            rcv_nxt = int(rcv_nxt_str)
            rcv_wnd = int(rcv_wnd_str)
        except ValueError:
            raise ValueError("Type Error: Ports, sequence numbers, and window sizes must be integers.")

        for p, label in [(sport, "Source Port"), (dport, "Destination Port")]:
            if p < 1 or p > 65535:
                raise ValueError(f"Bounds Error: {label} ({p}) must be within 1-65535.")

        for s, label in [(claimed_seq, "Claimed Sequence Number"), (rcv_nxt, "RCV.NXT")]:
            if s < 0 or s > 4294967295:
                raise ValueError(f"Architecture Error: {label} exceeds 32-bit boundary (0 to 4,294,967,295).")

        if rcv_wnd < 1 or rcv_wnd > 65535 * 16384:
            raise ValueError("Bounds Error: Receive window size invalid.")

        rfc5927_flag = rfc5927_enabled_str.strip().lower() in ['1', 'y', 'yes', 'true', 'enable', 'enabled']

        return src_ip, dst_ip, sport, dport, claimed_seq, rcv_nxt, rcv_wnd, rfc5927_flag

    def simulate_blind_reset(
        self,
        src_ip: str,
        dst_ip: str,
        sport: int,
        dport: int,
        claimed_seq: int,
        rcv_nxt: int,
        rcv_wnd: int,
        rfc5927_enabled: bool
    ) -> None:
        """Simulates RFC 5927 TCP state-checking against spoofed ICMP Type 3 hard errors."""
        
        # Hard Error Types that historically caused immediate socket teardown:
        # Type 3, Code 2 (Protocol Unreachable)
        # Type 3, Code 3 (Port Unreachable)
        # Type 3, Code 4 (Frag Needed - can trigger Path MTU collapse)

        eval_steps: List[Dict[str, str]] = []

        # Step 1: 4-Tuple Matching
        eval_steps.append({
            "stage": "1. 4-TUPLE LOOKUP",
            "condition": f"{src_ip}:{sport} <-> {dst_ip}:{dport}",
            "result": "MATCHED: Active ESTABLISHED TCP Transmission Control Block (TCB) located."
        })

        # Step 2: Sequence Number Window Validation (RFC 5927 Core Defense)
        # Without RFC 5927: Classic stacks checked only if 4-tuple matched, ignoring sequence number in payload!
        # With RFC 5927: Sequence number in encapsulated header MUST be within [RCV.NXT, RCV.NXT + RCV.WND).
        
        seq_in_window = (rcv_nxt <= claimed_seq < (rcv_nxt + rcv_wnd))

        if not rfc5927_enabled:
            eval_steps.append({
                "stage": "2. SEQUENCE VALIDATION (LEGACY / RFC 792)",
                "condition": "Strict TCP Sequence Check Disabled (Legacy behavior)",
                "result": "BYPASSED: Kernel accepts ICMP error blindly without checking SEQ in inner IP header."
            })
            connection_status = "CLOSED / RESET_BLINDLY"
            action = "TCB DESTROYED (ECONNRESET returned to application)"
            insight = (
                "VULNERABILITY EXPOSED (Pre-RFC 5927): An off-path attacker only needs to guess or bruteforce "
                "the 4-tuple (IPs and Ports). The kernel blindly trusts the ICMP error and immediately terminates "
                "long-lived BGP (port 179) or active VPN tunnels without checking if the sequence number is valid."
            )
        else:
            eval_steps.append({
                "stage": "2. SEQUENCE VALIDATION (RFC 5927)",
                "condition": f"Is {claimed_seq} in range [{rcv_nxt}, {rcv_nxt + rcv_wnd})?",
                "result": "IN-WINDOW" if seq_in_window else "OUT-OF-WINDOW / REJECTED"
            })

            if seq_in_window:
                connection_status = "VERIFIED_RESET"
                action = "TCB DESTROYED (Sequence number authenticated inside window)"
                insight = (
                    "LEGITIMATE ERROR PROCESSED: The ICMP error contained a sequence number actively matching "
                    "in-flight data within the receive window. Kernel safely tears down the failed connection."
                )
            else:
                connection_status = "SURVIVED / SPOOF_DROPPED"
                action = "ICMP PACKET DISCARDED (Off-path sequence guess was invalid)"
                insight = (
                    "RFC 5927 DEFENSE MITIGATION SUCCESSFUL: Because the attacker could not guess the exact "
                    "32-bit TCP sequence space within the window, the spoofed ICMP error was silently dropped. "
                    "The TCP session remains stable and uninterrupted."
                )

        self.reset_state = {
            "src": src_ip,
            "dst": dst_ip,
            "sport": sport,
            "dport": dport,
            "claimed_seq": claimed_seq,
            "rcv_nxt": rcv_nxt,
            "rcv_wnd": rcv_wnd,
            "rfc5927": rfc5927_enabled,
            "eval_steps": eval_steps,
            "status": connection_status,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.2)
        width = self.get_terminal_width()
        state = self.reset_state

        print("\n" + "=" * width)
        print(" [>] MODULE 03S: ICMP UNREACHABLE BLIND RESET & RFC 5927 MITIGATION ".center(width))
        print("=" * width)

        print(f" [+] Target Connection : {state['src']}:{state['sport']} <-> {state['dst']}:{state['dport']} [TCP]")
        print(f" [+] Kernel TCP State  : RCV.NXT = {state['rcv_nxt']} | Window = {state['rcv_wnd']} bytes")
        print(f" [+] Encapsulated SEQ  : {state['claimed_seq']} (Claimed by incoming ICMP Type 3 payload)")
        print(f" [+] RFC 5927 Engine   : {'ENABLED (Strict SEQ Validation)' if state['rfc5927'] else 'DISABLED (Vulnerable Legacy Stack)'}")
        print("-" * width)

        print(" [i] TCP/IP STACK VERIFICATION PIPELINE:")
        for step in state['eval_steps']:
            time.sleep(0.12)
            print(f"\n     [{step['stage']}]")
            print(f"     -> Evaluated Rule : {step['condition']}")
            print(f"     -> Stack Decision : {step['result']}")

        print("-" * width)
        print(f" [!] CONNECTION OUTCOME : {state['status']}")
        print(f" [!] CONTROL ACTION     : {state['action']}")
        print("-" * width)
        print(" [!] ARCHITECTURAL & DEFENSIVE INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPBlindResetDefenseEngine()
    width = engine.get_terminal_width()

    print("\n" + "=" * width)
    print(" 03S_ICMP_UNREACHABLE_BLIND_RESET INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Enter ICMP Blind Reset Evaluation Parameters:")
            src_in = input("    Local Host IP           (e.g., 10.0.0.5)      : ").strip()
            if src_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not src_in: continue

            dst_in = input("    Remote Endpoint IP      (e.g., 198.51.100.1)  : ").strip()
            sp_in  = input("    Local Port              (e.g., 179 for BGP)   : ").strip()
            dp_in  = input("    Remote Port             (e.g., 49152)         : ").strip()
            seq_in = input("    ICMP Payload SEQ Guess  (e.g., 100000)        : ").strip()
            nxt_in = input("    Actual Kernel RCV.NXT   (e.g., 5000000)       : ").strip()
            wnd_in = input("    Actual TCP Window Size  (e.g., 65535)         : ").strip()
            rfc_in = input("    Enable RFC 5927 Defense?(1=Yes, 0=No)         : ").strip()

            src, dst, sp, dp, c_seq, nxt, wnd, rfc = engine.validate_inputs(
                src_in, dst_in, sp_in, dp_in, seq_in, nxt_in, wnd_in, rfc_in
            )
            engine.simulate_blind_reset(src, dst, sp, dp, c_seq, nxt, wnd, rfc)
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