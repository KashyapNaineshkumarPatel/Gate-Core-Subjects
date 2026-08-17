import sys
import re
import math
import shutil
import time
from typing import Any, Dict, List, Tuple

class ICMPPayloadAnalyzerEngine:
    analyzer_state: Dict[str, Any]

    def __init__(self) -> None:
        self.analyzer_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, src_ip: str, dst_ip: str, payload_hex: str) -> Tuple[str, str, bytes]:
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        for ip, label in [(src_ip, "Source IP"), (dst_ip, "Destination IP")]:
            match = re.match(ip_pattern, ip)
            if not match:
                raise ValueError(f"Syntax Error: {label} format invalid (e.g., 192.168.1.10).")
            for idx, octet_str in enumerate(match.groups()):
                if int(octet_str) > 255:
                    raise ValueError(f"Architecture Error: {label} Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        cleaned_hex = re.sub(r'[^0-9A-Fa-f]', '', payload_hex)
        if len(cleaned_hex) % 2 != 0:
            raise ValueError("Syntax Error: Hex string must contain an even number of characters.")
        
        try:
            payload_bytes = bytes.fromhex(cleaned_hex)
        except ValueError:
            raise ValueError("Type Error: Failed to parse input as valid hexadecimal bytes.")

        if len(payload_bytes) > 1472:
            raise ValueError("Architecture Error: ICMP Payload exceeds MTU 1500 limit (1472 bytes max).")

        return src_ip, dst_ip, payload_bytes

    def _calculate_shannon_entropy(self, data: bytes) -> float:
        """Calculates Shannon entropy: H(X) = -sum(p(x) * log2(p(x)))."""
        if not data:
            return 0.0
        entropy = 0.0
        length = len(data)
        frequency: Dict[int, int] = {}
        for b in data:
            frequency[b] = frequency.get(b, 0) + 1
        for count in frequency.values():
            p_x = count / length
            entropy -= p_x * math.log2(p_x)
        return entropy

    def analyze_icmp_packet(self, src_ip: str, dst_ip: str, payload: bytes) -> None:
        """Evaluates ICMP data section against standard OS baselines and statistical heuristics."""
        payload_len = len(payload)
        entropy = self._calculate_shannon_entropy(payload)
        
        # Standard OS Baselines
        win_baseline = b'abcdefghijklmnopqrstuvwabcdefghi'
        is_windows_standard = (payload == win_baseline)
        
        anomaly_flags: List[str] = []
        
        if payload_len == 0:
            anomaly_flags.append("ZERO_LENGTH_PAYLOAD: Non-standard echo without data section.")
        elif payload_len > 64 and not is_windows_standard:
            anomaly_flags.append(f"ABNORMAL_PAYLOAD_SIZE: Size {payload_len}B exceeds standard 32B/56B baselines.")

        if entropy > 5.5:
            anomaly_flags.append(f"HIGH_ENTROPY_DETECTED: Entropy {entropy:.2f}/8.0 indicates encrypted/compressed payload.")
        elif entropy < 1.0 and payload_len > 16:
            anomaly_flags.append(f"LOW_ENTROPY_ANOMALY: Entropy {entropy:.2f}/8.0 indicates repeated static padding.")

        # Inferred Classification
        if not anomaly_flags:
            classification = "BENIGN / OS_STANDARD"
            risk_score = 0
        elif len(anomaly_flags) == 1 and "ABNORMAL_PAYLOAD_SIZE" in anomaly_flags[0]:
            classification = "SUSPICIOUS / NON_STANDARD_PING"
            risk_score = 45
        else:
            classification = "ANOMALOUS / POTENTIAL_COVERT_CHANNEL"
            risk_score = min(95, 30 * len(anomaly_flags))

        # Snort / Suricata Rule Signature Equivalent
        ids_rule = (
            f'alert icmp {src_ip} any -> {dst_ip} any ('
            f'msg:"PROTOCOL-ICMP Non-standard high entropy payload"; '
            f'itype:8; dsize:>{max(32, payload_len - 1)}; threshold:type limit,track by_src,count 5,seconds 60; '
            f'classtype:bad-unknown; sid:2000001; rev:1;)'
        )

        self.analyzer_state = {
            "src": src_ip,
            "dst": dst_ip,
            "payload_len": payload_len,
            "entropy": entropy,
            "raw_hex_preview": payload[:32].hex() + ('...' if len(payload) > 32 else ''),
            "flags": anomaly_flags,
            "classification": classification,
            "risk_score": risk_score,
            "ids_rule": ids_rule
        }

    def render_ui(self) -> None:
        time.sleep(0.2)
        width = self.get_terminal_width()
        state = self.analyzer_state

        print("\n" + "=" * width)
        print(" [>] MODULE 03Q: ICMP PAYLOAD ANOMALY & COVERT CHANNEL DETECTOR ".center(width))
        print("=" * width)

        print(f" [+] Source IP         : {state['src']}")
        print(f" [+] Destination IP    : {state['dst']}")
        print(f" [+] Payload Length    : {state['payload_len']} bytes")
        print(f" [+] Shannon Entropy   : {state['entropy']:.3f} / 8.000 bits per byte")
        print(f" [+] Data Preview (Hex): {state['raw_hex_preview']}")
        print("-" * width)

        print(" [i] DEEP PACKET INSPECTION (DPI) HEURISTICS:")
        if state['flags']:
            for flag in state['flags']:
                print(f"     [!] ALERT FLAG: {flag}")
        else:
            print("     [+] Standard OS payload structure matched. No structural anomalies detected.")

        print("-" * width)
        print(f" [!] CLASSIFICATION : {state['classification']} (Risk Score: {state['risk_score']}/100)")
        print("-" * width)

        print(" [i] GENERATED NETWORK IDS DETECTION SIGNATURE:")
        print(f"     {state['ids_rule']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPPayloadAnalyzerEngine()
    width = engine.get_terminal_width()

    print("\n" + "=" * width)
    print(" 03Q_ICMP_COVERT_CHANNEL_DETECTOR INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Enter ICMP Traffic Inspection Parameters:")
            src_in = input("    Source IP             (e.g., 10.0.0.15)  : ").strip()
            if src_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not src_in: continue

            dst_in = input("    Destination IP        (e.g., 198.51.100.1): ").strip()
            print("    Sample Hex Payloads:")
            print("      Standard Windows Ping: 6162636465666768696a6b6c6d6e6f7071727374757677616263646566676869")
            print("      High-Entropy / Random: 4f3a8b92c1e4f019d837a6b2c9e810345f12a87c90e1b2d3")
            raw_hex = input("    Payload Hex Stream                         : ").strip()

            src, dst, payload = engine.validate_inputs(src_in, dst_in, raw_hex)
            engine.analyze_icmp_packet(src, dst, payload)
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