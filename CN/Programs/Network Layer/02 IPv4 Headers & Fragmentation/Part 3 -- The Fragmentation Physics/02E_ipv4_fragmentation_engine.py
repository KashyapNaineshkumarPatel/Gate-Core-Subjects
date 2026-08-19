import sys
import shutil
import time
from typing import Any, Dict, List, Tuple

class IPv4FragmentationEngine:
    fragmentation_state: Dict[str, Any]

    def __init__(self) -> None:
        # State Management Engine
        self.fragmentation_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 100)

    def validate_inputs(self, payload_input: str, mtu_input: str) -> Tuple[int, int]:
        # Input Bounds Validation & Descriptive Errors
        try:
            payload_size = int(payload_input)
            mtu_size = int(mtu_input)
        except ValueError as exc:
            raise ValueError("Type Error: Payload and MTU must be valid integers.") from exc

        if not 1 <= payload_size <= 65515:
            raise ValueError(
                f"Exhaustion Error: Total IP packet size is 65,535 bytes. "
                f"Minus the 20-byte header, the maximum payload is 65,515 bytes. "
                f"You requested {payload_size}."
            )

        # The RFC 791 Minimum MTU Rule
        if mtu_size < 68:
            raise ValueError(
                f"Architecture Error: RFC 791 dictates the absolute minimum IPv4 MTU is 68 bytes "
                f"(20 byte IP header + max 40 byte options + minimum 8 byte fragment). "
                f"You entered {mtu_size}, which violates physical routing standards."
            )

        # Check for Infinite Loop trap (MTU too small to hold 8 bytes of payload after 20 byte header)
        if mtu_size < 28:
            raise ValueError(
                f"Physics Error: An MTU of {mtu_size} minus a 20-byte header leaves {mtu_size - 20} bytes. "
                f"Fragments MUST be divisible by 8. This MTU cannot carry a valid fragment."
            )

        return payload_size, mtu_size

    def calculate_fragments(self, payload: int, mtu: int) -> None:
        """The Fragmentation Physics Engine: Calculates offsets, MF flags, and 8-byte boundaries."""
        ip_header_size = 20
        
        # Max payload we can fit in the MTU
        max_fragment_payload = mtu - ip_header_size
        
        # The 8-Byte Boundary Rule: Payload per fragment MUST be a multiple of 8.
        # We use floor division to strip the remainder, then multiply by 8.
        aligned_payload = (max_fragment_payload // 8) * 8
        
        remaining_bytes = payload
        current_byte_index = 0
        fragments: List[Dict[str, Any]] = []

        while remaining_bytes > 0:
            if remaining_bytes > aligned_payload:
                send_bytes = aligned_payload
                mf_flag = 1  # More Fragments coming
            else:
                send_bytes = remaining_bytes
                mf_flag = 0  # Last fragment
                
            # The Offset is the byte index divided by 8
            offset_value = current_byte_index // 8
            total_packet_size = send_bytes + ip_header_size
            
            fragments.append({
                "id": len(fragments) + 1,
                "total_len": total_packet_size,
                "payload_len": send_bytes,
                "mf": mf_flag,
                "offset": offset_value,
                "byte_range": f"{current_byte_index} -> {current_byte_index + send_bytes - 1}"
            })
            
            remaining_bytes -= send_bytes
            current_byte_index += send_bytes

        # Update State Tree
        self.fragmentation_state = {
            "original_payload": payload,
            "mtu": mtu,
            "aligned_payload": aligned_payload,
            "wasted_mtu": max_fragment_payload - aligned_payload,
            "total_fragments": len(fragments),
            "fragments": fragments
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.2) 
        width = self.get_terminal_width()
        state = self.fragmentation_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 02E: MTU & FRAGMENTATION ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] Original Payload : {state['original_payload']} bytes")
        print(f" [+] Link MTU Limit   : {state['mtu']} bytes")
        
        if state['wasted_mtu'] > 0:
            print(f" [!] 8-Byte Alignment : Max payload was {state['mtu'] - 20}, but reduced to {state['aligned_payload']} to be divisible by 8.")
            print(f" [!] Wasted MTU Space : {state['wasted_mtu']} bytes per packet remain unused due to alignment physics.")
        else:
            print(" [+] 8-Byte Alignment : Perfect match. No MTU space wasted.")
            
        print("-" * width)
        
        # Educational Silicon Physics Feedback
        print(" [i] 1% ENGINEERING INSIGHT: WHY 8 BYTES?")
        print("     The 'Fragment Offset' field in the IP header is only 13 bits long. The maximum")
        print("     value is 8,191. To map a 65,535-byte payload, it MUST count in blocks of 8 bytes.")
        print("     (8,191 * 8 = 65,528). That is why every fragment payload must be a multiple of 8.")
        print("-" * width)
        
        print(" FRAG #   | TOTAL LEN | PAYLOAD | MF FLAG | OFFSET | BYTE RANGE")
        print("-" * width)

        display_limit = min(state['total_fragments'], 15)
        for idx in range(display_limit):
            frag = state['fragments'][idx]
            print(f" {frag['id']:<7} | {frag['total_len']:<10} | {frag['payload_len']:<8} | {frag['mf']:<8} | {frag['offset']:<7} | {frag['byte_range']}")
            
        if state['total_fragments'] > display_limit:
            remaining = state['total_fragments'] - display_limit
            print(f" ... and {remaining} more fragments (Output truncated for terminal performance).")
            
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = IPv4FragmentationEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 02E_IPv4_FRAGMENTATION_ENGINE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            print("\n[?] Enter Payload and MTU (e.g., Payload: 4000, MTU: 1500)")
            payload_in = input("    Original Payload Size (Bytes): ").strip()
            
            if payload_in.lower() in ['quit', 'exit']:
                print("\n[+] Graceful shutdown initiated. Goodbye.")
                sys.exit(0)
            if not payload_in: continue
                
            mtu_in = input("    Link MTU Limit (Bytes)       : ").strip()
                
            valid_payload, valid_mtu = engine.validate_inputs(payload_in, mtu_in)
            engine.calculate_fragments(valid_payload, valid_mtu)
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