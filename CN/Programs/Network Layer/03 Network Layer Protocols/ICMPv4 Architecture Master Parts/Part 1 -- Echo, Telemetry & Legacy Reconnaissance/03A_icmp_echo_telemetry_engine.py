import sys
import re
import shutil
import time
import random
from typing import Any, Dict, List, Tuple

class ICMPEchoTelemetryEngine:
    telemetry_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.telemetry_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 100)

    def validate_inputs(self, target_ip: str, packet_count: str, payload_size: str) -> Tuple[str, int, int]:
        # Input Bounds Validation & Descriptive Errors
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ip_pattern, target_ip)
        
        if not match:
            raise ValueError(f"Syntax Error: Target IP format invalid (e.g., 8.8.8.8).")
        for idx, octet_str in enumerate(match.groups()):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")
                
        try:
            count = int(packet_count)
            size = int(payload_size)
        except ValueError:
            raise ValueError("Type Error: Packet count and Payload size must be integers.")
            
        if count < 1 or count > 100:
            raise ValueError("Logical Error: Packet count must be between 1 and 100 for telemetry analysis.")
            
        # The ICMP Payload Physics: Max IP packet is 65535.
        # Minus 20 bytes (IP Header) - 8 bytes (ICMP Header) = 65507 bytes max payload.
        if size < 0 or size > 65507:
            raise ValueError(
                f"Exhaustion Error: Maximum ICMP payload is 65,507 bytes.\n"
                f"(65,535 Total - 20 IP Header - 8 ICMP Header). You requested {size}."
            )
            
        return target_ip, count, size

    def simulate_telemetry(self, target: str, count: int, payload_size: int) -> None:
        """The Telemetry Engine: Constructs ICMP headers and measures jitter."""
        
        # ICMP Header Base Fields
        icmp_type_req = 8  # Echo Request
        icmp_type_rep = 0  # Echo Reply
        icmp_code = 0
        
        # OS assigns a 16-bit random Identifier to distinguish this ping session from others
        session_id = random.randint(1000, 65535)
        
        log: List[Dict[str, Any]] = []
        rtt_list: List[float] = []
        
        # Simulate Network Conditions
        base_latency = random.uniform(10.0, 40.0)
        
        for seq in range(1, count + 1):
            # Simulate latency with minor jitter fluctuations
            jitter = random.uniform(-5.0, 15.0)
            rtt = round(base_latency + jitter, 2)
            
            # Artificial packet loss (2% chance)
            dropped = random.random() < 0.02
            
            if dropped:
                log.append({
                    "seq": seq,
                    "status": "TIMEOUT",
                    "details": "Packet lost in transit. No Type 0 Reply received.",
                    "rtt": None
                })
            else:
                rtt_list.append(rtt)
                log.append({
                    "seq": seq,
                    "status": "REPLY",
                    "details": f"Type={icmp_type_rep} Code={icmp_code} Id={session_id} Seq={seq}",
                    "rtt": rtt
                })
                
        # Statistical Math (Jitter Calculation)
        packets_sent = count
        packets_recv = len(rtt_list)
        loss_pct = ((packets_sent - packets_recv) / packets_sent) * 100
        
        if packets_recv > 0:
            min_rtt = min(rtt_list)
            max_rtt = max(rtt_list)
            avg_rtt = sum(rtt_list) / packets_recv
            # Network Jitter is the variance between consecutive RTTs
            if packets_recv > 1:
                jitter_calc = sum([abs(rtt_list[i] - rtt_list[i-1]) for i in range(1, packets_recv)]) / (packets_recv - 1)
            else:
                jitter_calc = 0.0
        else:
            min_rtt = max_rtt = avg_rtt = jitter_calc = 0.0

        # Update State Tree
        self.telemetry_state = {
            "target": target,
            "bytes": payload_size,
            "session_id": session_id,
            "log": log,
            "stats": {
                "sent": packets_sent,
                "recv": packets_recv,
                "loss": round(loss_pct, 1),
                "min": round(min_rtt, 2),
                "max": round(max_rtt, 2),
                "avg": round(avg_rtt, 2),
                "jitter": round(jitter_calc, 2)
            }
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.2) 
        width = self.get_terminal_width()
        state = self.telemetry_state
        stats = state['stats']
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03A: ICMP ECHO TELEMETRY ENGINE ".center(width))
        print("=" * width)
        
        print(f" [*] Pinging {state['target']} with {state['bytes']} bytes of data:")
        print(f" [*] Session Identifier (16-bit): {state['session_id']}")
        print("-" * width)
        
        for entry in state['log']:
            time.sleep(0.15) # Throttle to simulate real ICMP timings
            if entry['status'] == "TIMEOUT":
                print(f"     Request timeout for icmp_seq={entry['seq']}")
            else:
                print(f"     {state['bytes']} bytes from {state['target']}: icmp_seq={entry['seq']} time={entry['rtt']} ms")
                
        print("-" * width)
        print(f" [i] ICMP TELEMETRY STATISTICS FOR {state['target']}:")
        print(f"     Packets: Sent = {stats['sent']}, Received = {stats['recv']}, Lost = {stats['loss']}%")
        print(f"     Round Trip Time (ms): min = {stats['min']}, avg = {stats['avg']}, max = {stats['max']}")
        
        # Engineering Insight
        print("\n [!] ENGINEERING DIAGNOSTIC (JITTER ANALYSIS):")
        print(f"     -> Calculated Network Jitter : {stats['jitter']} ms")
        if stats['jitter'] > 30:
            print("     -> INSIGHT: Severe jitter detected. VoIP and video streams will drop audio frames.")
        elif stats['loss'] > 0:
            print("     -> INSIGHT: Packet loss detected. TCP connections will suffer throughput collapse due to retransmissions.")
        else:
            print("     -> INSIGHT: Stable connection. Variance is low. Optimal for real-time UDP streams.")
            
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPEchoTelemetryEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03A_ICMP_ECHO_TELEMETRY_ENGINE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            print("\n[?] Enter ICMP Telemetry Parameters:")
            target_in = input("    Target IP       (e.g., 8.8.8.8) : ").strip()
            if target_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not target_in: continue
            
            count_in = input("    Packet Count    (e.g., 4)       : ").strip()
            size_in  = input("    Payload Bytes   (e.g., 64)      : ").strip()
                
            tgt, count, size = engine.validate_inputs(target_in, count_in, size_in)
            engine.simulate_telemetry(tgt, count, size)
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