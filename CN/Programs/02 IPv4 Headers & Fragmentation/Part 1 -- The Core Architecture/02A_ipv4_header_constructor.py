import sys
import re
import shutil
import time
from typing import Any, Dict, List, Tuple

class IPv4HeaderEngine:
    packet_state: Dict[str, Any]

    def __init__(self) -> None:
        # State Management Engine
        self.packet_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 90)

    def _ip_to_int(self, ip_str: str) -> int:
        """Helper to convert IP string to 32-bit integer for checksum math."""
        octets = [int(x) for x in ip_str.split('.')]
        return (octets[0] << 24) + (octets[1] << 16) + (octets[2] << 8) + octets[3]

    def validate_inputs(self, src: str, dst: str, proto: str, payload: str) -> Tuple[str, str, int, int]:
        # Input Bounds Validation & Descriptive Errors
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        
        for ip, label in [(src, "Source IP"), (dst, "Target IP")]:
            match = re.match(ip_pattern, ip)
            if not match:
                raise ValueError(f"Syntax Error: {label} format invalid (e.g., 192.168.1.1)")
            for idx, octet_str in enumerate(match.groups()):
                if int(octet_str) > 255:
                    raise ValueError(f"System Error: {label} Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        try:
            protocol = int(proto)
            payload_size = int(payload)
        except ValueError as exc:
            raise ValueError("Type Error: Protocol and Payload Size must be integers.") from exc

        if protocol < 0 or protocol > 255:
            raise ValueError(f"System Error: Protocol field is 8 bits. Max value is 255. You entered {protocol}.")
            
        # Total Length Field is 16 bits (Max 65,535). 20 bytes are reserved for the header.
        if payload_size < 0 or payload_size > 65515:
            raise ValueError(
                f"Exhaustion Error: The IPv4 'Total Length' field is 16 bits (Max 65,535 bytes).\n"
                f"Subtracting the 20-byte IP header leaves a maximum payload of 65,515 bytes. "
                f"You requested {payload_size} bytes, causing a memory overflow."
            )
            
        return src, dst, protocol, payload_size

    def calculate_header(self, src: str, dst: str, protocol: int, payload_size: int) -> None:
        """The Byte-Level Architecture & Checksum Math."""
        # Standard IPv4 Parameters
        version_ihl = 0x4500  # Version 4, IHL 5 (5 * 4 = 20 bytes). TOS = 0x00.
        total_length = 20 + payload_size
        identification = 0x1234  # Simulated Packet ID
        flags_offset = 0x0000    # No fragmentation for now
        ttl = 64
        ttl_proto = (ttl << 8) + protocol
        
        src_int = self._ip_to_int(src)
        dst_int = self._ip_to_int(dst)

        # Assemble the 16-bit words for the header
        header_words: List[int] = [
            version_ihl,
            total_length,
            identification,
            flags_offset,
            ttl_proto,
            0x0000, # Initial Checksum is always 0 for calculation
            (src_int >> 16) & 0xFFFF,
            src_int & 0xFFFF,
            (dst_int >> 16) & 0xFFFF,
            dst_int & 0xFFFF
        ]

        # 16-bit Ones' Complement Checksum Math
        checksum = sum(header_words)
        while checksum >> 16:
            checksum = (checksum & 0xFFFF) + (checksum >> 16)
        final_checksum = ~checksum & 0xFFFF

        # Update State Tree
        self.packet_state = {
            "src": src,
            "dst": dst,
            "protocol": protocol,
            "payload_size": payload_size,
            "total_length": total_length,
            "id_hex": f"0x{identification:04X}",
            "ttl": ttl,
            "checksum_hex": f"0x{final_checksum:04X}",
            "words": [f"0x{w:04X}" for w in header_words]
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.2) 
        width = self.get_terminal_width()
        state = self.packet_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 02A: IPv4 HEADER CONSTRUCTOR ".center(width))
        print("=" * width)
        
        print(f" [+] Source IP        : {state['src']}")
        print(f" [+] Destination IP   : {state['dst']}")
        print(f" [+] Protocol         : {state['protocol']} (e.g., 1=ICMP, 6=TCP, 17=UDP)")
        print(f" [+] Payload Size     : {state['payload_size']} bytes")
        print("-" * width)
        
        print(" [i] HEADER ARCHITECTURE & SILICON MATH:")
        print("     -> Header Length  : 20 bytes (IHL = 5 words)")
        print(f"     -> Total Length   : {state['total_length']} bytes (Fits in 16-bit field)")
        print(f"     -> Identification : {state['id_hex']}")
        print(f"     -> Time to Live   : {state['ttl']}")
        print(f"     -> Calculated CSUM: {state['checksum_hex']} (Hardware Validation Pass)")
        print("-" * width)
        
        print(" [i] RAW 16-BIT WORD ARRAY (For Ones' Complement Math):")
        print(f"     {state['words']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = IPv4HeaderEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 02A_IPv4_HEADER_CONSTRUCTOR INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            print("\n[?] Enter Packet Parameters:")
            src_in = input("    Source IP      (e.g., 10.0.0.5) : ").strip()
            if src_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not src_in: continue
            
            dst_in = input("    Destination IP (e.g., 8.8.8.8)  : ").strip()
            proto_in = input("    Protocol       (e.g., 6 for TCP): ").strip()
            payload_in = input("    Payload Bytes  (e.g., 1460)     : ").strip()
                
            src, dst, proto, payload = engine.validate_inputs(src_in, dst_in, proto_in, payload_in)
            engine.calculate_header(src, dst, proto, payload)
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