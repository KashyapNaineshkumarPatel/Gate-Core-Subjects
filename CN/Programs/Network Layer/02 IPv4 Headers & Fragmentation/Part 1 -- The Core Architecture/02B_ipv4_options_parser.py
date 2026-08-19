import sys
import shutil
import time
from typing import Any, Dict, List, Tuple

class IPv4OptionsEngine:
    header_state: Dict[str, Any]

    def __init__(self) -> None:
        # State Management Engine
        self.header_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 90)

    def validate_options(self, option_type: str, num_ips: str) -> Tuple[str, int]:
        # Input Bounds Validation
        valid_options = {'1': 'Record Route', '2': 'Loose Source Route', '3': 'Strict Source Route'}
        if option_type not in valid_options:
            raise ValueError(f"Syntax Error: Invalid option selected ({option_type}). Must be 1, 2, or 3.")
            
        try:
            ip_count = int(num_ips)
        except ValueError as exc:
            raise ValueError("Type Error: The number of IP hops must be a valid integer.") from exc
            
        if ip_count < 0:
            raise ValueError("Logical Error: You cannot request a negative number of IPs.")
            
        # The 1% Engineering Rule: The 60-Byte Header Limit
        # IHL is 4 bits. Max value = 15. 15 * 4 bytes = 60 bytes total max header.
        # Base header = 20 bytes. Max Options space = 40 bytes.
        # Format: Type (1), Length (1), Pointer (1) = 3 bytes overhead + 4 bytes per IP.
        required_option_bytes = 3 + (ip_count * 4)
        
        if required_option_bytes > 40:
            max_allowed = (40 - 3) // 4
            raise ValueError(
                f"Exhaustion Error: IHL field is limited to 4 bits (Max 60 bytes total). "
                f"With a 20-byte base header, only 40 bytes remain for Options. "
                f"You requested {ip_count} IPs ({required_option_bytes} bytes). "
                f"The physical maximum is {max_allowed} IPs."
            )
            
        return valid_options[option_type], ip_count

    def calculate_ihl(self, option_name: str, ip_count: int) -> None:
        """The Variable Header Mechanic: Calculates padding and dynamic IHL."""
        base_header_bytes = 20
        option_overhead = 3
        ip_bytes = ip_count * 4
        
        raw_options_bytes = option_overhead + ip_bytes
        
        # 32-bit (4-byte) Alignment Physics
        # Routers expect headers to end on 32-bit boundaries. 
        # If options are not a multiple of 4, the OS injects End of Option List (0x00) or No-Op (0x01) padding.
        remainder = raw_options_bytes % 4
        padding_bytes = (4 - remainder) if remainder != 0 else 0
        
        total_options_bytes = raw_options_bytes + padding_bytes
        total_header_bytes = base_header_bytes + total_options_bytes
        
        # IHL represents the number of 32-bit words
        new_ihl = total_header_bytes // 4
        
        # Security insight generation
        security_note = ""
        if "Source Route" in option_name:
            security_note = "SEVERE RISK: Attackers use Source Routing to dictate network paths, bypassing firewalls. Most modern routers drop this."
        else:
            security_note = "WARNING: Record Route exposes internal network topology. Deprecated in favor of traceroute."

        # Update State Tree
        self.header_state = {
            "option_name": option_name,
            "ip_count": ip_count,
            "raw_bytes": raw_options_bytes,
            "padding": padding_bytes,
            "total_options": total_options_bytes,
            "total_header": total_header_bytes,
            "ihl": new_ihl,
            "security": security_note
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.2) 
        width = self.get_terminal_width()
        state = self.header_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 02B: IPv4 OPTIONS PARSER ".center(width))
        print("=" * width)
        
        print(f" [+] Option Injected  : {state['option_name']}")
        print(f" [+] Configured Hops  : {state['ip_count']} IPs")
        print("-" * width)
        
        print(" [i] HEADER ARCHITECTURE & ALIGNMENT MATH:")
        print("     -> Base IPv4 Header  : 20 bytes")
        print(f"     -> Raw Option Space  : {state['raw_bytes']} bytes")
        print(f"     -> 32-Bit Padding    : {state['padding']} bytes (No-Op / EOOL injected)")
        print(f"     -> Total Header Size : {state['total_header']} bytes")
        print("-" * width)
        
        print(f" [!] CALCULATED IHL FIELD : {state['ihl']} (Binary: {state['ihl']:04b})")
        print("-" * width)
        
        print(" [!] SECURITY IDS ALERT:")
        print(f"     -> {state['security']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = IPv4OptionsEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 02B_IPv4_OPTIONS_PARSER INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            print("\n[?] Select Variable Option to Inject:")
            print("    1: Record Route (RR)")
            print("    2: Loose Source Route (LSRR)")
            print("    3: Strict Source Route (SSRR)")
            opt_in = input("    Selection (1/2/3): ").strip()
            
            if opt_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not opt_in: continue
            
            hops_in = input("    Number of IP hops to store: ").strip()
                
            opt_name, hop_count = engine.validate_options(opt_in, hops_in)
            engine.calculate_ihl(opt_name, hop_count)
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