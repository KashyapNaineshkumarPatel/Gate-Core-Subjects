import sys
import re
import shutil
import time
from typing import Any, Dict, Tuple

class ICMPParameterProblemEngine:
    debug_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.debug_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, router_ip: str, fault_type: str) -> Tuple[str, int]:
        # IP Validation
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ip_pattern, router_ip)
        if not match:
            raise ValueError("Syntax Error: Router IP format invalid (e.g., 10.0.0.1).")
        for idx, octet_str in enumerate(match.groups()):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        # Fault Selection
        valid_faults = {'1', '2', '3', '4', '5'}
        if fault_type not in valid_faults:
            raise ValueError("Syntax Error: Select fault scenario 1, 2, 3, 4, or 5.")

        return router_ip, int(fault_type)

    def simulate_parameter_problem(self, router_ip: str, fault_id: int) -> None:
        """The IP Header Debugging Engine: Identifies byte offsets and constructs ICMP Type 12."""
        
        icmp_type = 12  # Parameter Problem
        
        # Scenarios mapping exact corrupted byte offsets in standard 20-byte IPv4 Header
        # Byte 0: Version/IHL
        # Byte 1: ToS / DSCP / ECN
        # Byte 2-3: Total Length
        # Byte 4-5: Identification
        # Byte 6-7: Flags / Fragment Offset
        # Byte 8: TTL
        # Byte 9: Protocol
        # Byte 10-11: Header Checksum
        # Byte 12-15: Source IP
        # Byte 16-19: Destination IP
        
        scenarios = {
            1: {
                "name": "Invalid IP Version (e.g., IPv5 / 0x55)",
                "code": 0,
                "pointer_offset": 0,
                "corrupted_field": "Version / IHL (Byte 0)",
                "raw_hex": "55 00 00 3C AB 12 00 00 40 06 1A 2B C0 A8 01 32 08 08 08 08",
                "reason": "Hardware parsing engine read Version nibble as 5. Only IPv4 (4) and IPv6 (6) are valid."
            },
            2: {
                "name": "Illegal IHL Header Length (< 5 words)",
                "code": 0,
                "pointer_offset": 0,
                "corrupted_field": "IHL (Lower 4 bits of Byte 0)",
                "raw_hex": "43 00 00 3C AB 12 00 00 40 06 1A 2B C0 A8 01 32 08 08 08 08",
                "reason": "IHL set to 3 (3 * 4 = 12 bytes). Physical base IPv4 header cannot be smaller than 20 bytes (IHL = 5)."
            },
            3: {
                "name": "Malformed Total Length (< Header Size)",
                "code": 0,
                "pointer_offset": 2,
                "corrupted_field": "Total Length (Bytes 2-3)",
                "raw_hex": "45 00 00 0E AB 12 00 00 40 06 1A 2B C0 A8 01 32 08 08 08 08",
                "reason": "Total Length declared as 14 bytes (0x000E), but base header itself requires 20 bytes."
            },
            4: {
                "name": "Reserved Flag (Evil Bit) Set",
                "code": 0,
                "pointer_offset": 6,
                "corrupted_field": "Flags / Fragment Offset (Byte 6)",
                "raw_hex": "45 00 00 3C AB 12 80 00 40 06 1A 2B C0 A8 01 32 08 08 08 08",
                "reason": "RFC 3514 Evil Bit / Reserved Flag (0x80) set on strict firewall or router requiring compliance."
            },
            5: {
                "name": "Missing Mandatory Option / Pointer Indicator",
                "code": 1,
                "pointer_offset": 20,
                "corrupted_field": "Options Field (Byte 20)",
                "raw_hex": "46 00 00 40 AB 12 00 00 40 06 1A 2B C0 A8 01 32 08 08 08 08 83 03 ...",
                "reason": "IHL declared 24 bytes (IHL = 6), but Security/Stream option payload was truncated or missing."
            }
        }

        selected = scenarios[fault_id]
        
        # Diagnostic analysis
        insight = (
            f"SILICON PRECISION DEBUGGING: ICMP Type 12 uses Byte 4 of its own header as an exact 8-bit 'Pointer'. "
            f"Here, Pointer = {selected['pointer_offset']}, highlighting byte offset {selected['pointer_offset']} ({selected['corrupted_field']}). "
            f"The receiving sender can index directly into its failed buffer without guesswork to isolate stack corruptions."
        )

        # Update State Tree
        self.debug_state = {
            "router_ip": router_ip,
            "scenario": selected['name'],
            "type": icmp_type,
            "code": selected['code'],
            "pointer": selected['pointer_offset'],
            "corrupted_field": selected['corrupted_field'],
            "raw_hex": selected['raw_hex'],
            "reason": selected['reason'],
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.debug_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03K: ICMP PARAMETER PROBLEM DEBUGGER (TYPE 12) ".center(width))
        print("=" * width)
        
        print(f" [+] Intercepting Router : {state['router_ip']}")
        print(f" [+] Simulated Anomaly   : {state['scenario']}")
        print("-" * width)
        
        print(" [i] CORRUPTED INGRESS IPv4 HEADER (HEX STREAM):")
        print(f"     {state['raw_hex']}")
        
        # Highlight pointer visually
        byte_tokens = state['raw_hex'].split(' ')
        pointer_marker = ["  "] * len(byte_tokens)
        if state['pointer'] < len(pointer_marker):
            pointer_marker[state['pointer']] = "^^"
            print(f"     {' '.join(pointer_marker)} (Pointer points to Byte Offset {state['pointer']})")
            
        print("-" * width)
        print(" [!] ICMP AUTOPSY EMISSION: Type 12 (Parameter Problem)")
        print(f"     -> Code Field       : {state['code']} ({'Pointer indicates error' if state['code'] == 0 else 'Missing required option'})")
        print(f"     -> Pointer Field    : {state['pointer']} (Exact Byte Offset in Failed Header)")
        print(f"     -> Isolated Field   : {state['corrupted_field']}")
        print(f"     -> Hardware Reason  : {state['reason']}")
        print("-" * width)
        
        print(f" [!] ARCHITECTURAL DIAGNOSTIC:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPParameterProblemEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03K_ICMP_PARAMETER_PROBLEM_DEBUGGER INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select IPv4 Header Corruption Scenario to Inject:")
            print("    1: Invalid IP Version Nibble (Byte 0)")
            print("    2: Illegal IHL Header Length < 20 Bytes (Byte 0)")
            print("    3: Total Length Smaller than Header (Byte 2-3)")
            print("    4: Illegal Reserved Flag / Evil Bit Set (Byte 6)")
            print("    5: Missing Required Option Pointer (Code 1 / Byte 20)")
            
            fault_in = input("    Selection (1-5): ").strip()
            if fault_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not fault_in: continue
            
            router_in = input("    Router IP to report fault (e.g., 10.0.0.1): ").strip()
                
            router, fault = engine.validate_inputs(router_in, fault_in)
            engine.simulate_parameter_problem(router, fault)
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