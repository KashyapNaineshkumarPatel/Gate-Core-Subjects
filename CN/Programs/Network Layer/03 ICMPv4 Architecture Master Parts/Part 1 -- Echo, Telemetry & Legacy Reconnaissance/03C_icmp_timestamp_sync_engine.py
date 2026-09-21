import sys
import re
import shutil
import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

class ICMPTimestampEngine:
    sync_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.sync_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, target_ip: str) -> str:
        # IP Validation
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ip_pattern, target_ip)
        
        if not match:
            raise ValueError("Syntax Error: Target IP format invalid (e.g., 192.168.1.100).")
            
        for idx, octet_str in enumerate(match.groups()):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")
                
        return target_ip

    def _get_ms_since_midnight(self) -> int:
        """Physical ICMP Clock Math: Milliseconds since midnight UTC."""
        now = datetime.now(timezone.utc)
        ms_since_midnight = (now.hour * 3600 + now.minute * 60 + now.second) * 1000 + (now.microsecond // 1000)
        return ms_since_midnight

    def simulate_timestamp_sync(self, target_ip: str) -> None:
        """The Legacy Clock Engine: Generates Type 13 Request and Type 14 Reply."""
        
        type_req = 13  # Timestamp Request
        type_rep = 14  # Timestamp Reply
        
        # Step 1: Originate Timestamp (Attacker/Client Time)
        originate_ts = self._get_ms_since_midnight()
        
        # Simulate Network Travel Time (e.g., 15ms)
        network_delay = 15
        
        # Step 2: Receive and Transmit Timestamps (Target Time)
        # We simulate a target clock that is drifting by +4500 ms (4.5 seconds fast)
        clock_drift = 4500
        target_processing_time = 2  # Takes 2ms to process the packet
        
        receive_ts = originate_ts + network_delay + clock_drift
        transmit_ts = receive_ts + target_processing_time
        
        # Attacker receives the reply
        final_receive_ts = originate_ts + (network_delay * 2) + target_processing_time
        
        # Math to calculate the target's exact clock offset
        # Offset = ((Receive - Originate) + (Transmit - FinalReceive)) / 2
        calculated_offset = ((receive_ts - originate_ts) + (transmit_ts - final_receive_ts)) / 2
        
        # Security Insight Generation
        insight = (
            "CRITICAL EXPOSURE: The target answered a Type 13 request, exposing its internal system clock. "
            f"An attacker now knows the target clock is offset by exactly {calculated_offset} ms. "
            "This allows them to predict pseudo-random number generators (PRNG), hijack predictable TCP sequence numbers, "
            "and bypass time-synced cryptography (like TOTP/2FA tokens) if the server relies on local time."
        )

        # Update State Tree
        self.sync_state = {
            "target": target_ip,
            "originate": originate_ts,
            "receive": receive_ts,
            "transmit": transmit_ts,
            "offset": calculated_offset,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.sync_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03C: ICMP TIMESTAMP SYNC ENGINE (TYPE 13/14) ".center(width))
        print("=" * width)
        
        print(f" [+] Target Host IP : {state['target']}")
        print("-" * width)
        
        print(" [i] ICMP TIMESTAMPS (Milliseconds since Midnight UTC):")
        time.sleep(0.2)
        print(f"     -> [TX] Originate Timestamp : {state['originate']} ms (Sent in Type 13 Request)")
        time.sleep(0.4)
        print(f"     <- [RX] Receive Timestamp   : {state['receive']} ms (Target received packet)")
        print(f"     <- [RX] Transmit Timestamp  : {state['transmit']} ms (Target replied via Type 14)")
        print("-" * width)
        
        print(f" [!] MATHEMATICAL CLOCK CALCULATION:")
        print(f"     -> Calculated Clock Offset  : {state['offset']} ms")
        print("-" * width)
        
        print(f" [!] SECURITY IDS ALERT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPTimestampEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03C_ICMP_TIMESTAMP_SYNC_ENGINE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Enter Target IP to probe its internal clock:")
            target_in = input("    Target IP (e.g., 192.168.1.50): ").strip()
            if target_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not target_in: continue
                
            target = engine.validate_inputs(target_in)
            engine.simulate_timestamp_sync(target)
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