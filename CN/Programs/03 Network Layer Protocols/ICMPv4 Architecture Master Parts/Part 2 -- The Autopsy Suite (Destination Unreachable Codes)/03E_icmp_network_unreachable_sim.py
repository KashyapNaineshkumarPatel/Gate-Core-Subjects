import sys
import re
import shutil
import time
from typing import Any, Dict, Tuple

class ICMPNetworkUnreachableEngine:
    autopsy_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.autopsy_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, router_ip: str, dest_ip: str, proto: str) -> Tuple[str, str, int]:
        # Input Bounds Validation & Descriptive Errors
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        
        for ip, label in [(router_ip, "Router IP"), (dest_ip, "Destination IP")]:
            match = re.match(ip_pattern, ip)
            if not match:
                raise ValueError(f"Syntax Error: {label} format invalid (e.g., 10.0.0.1).")
            for idx, octet_str in enumerate(match.groups()):
                if int(octet_str) > 255:
                    raise ValueError(f"Architecture Error: {label} Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        try:
            protocol = int(proto)
        except ValueError:
            raise ValueError("Type Error: Protocol must be an integer (e.g., 6 for TCP, 17 for UDP).")
            
        if protocol < 0 or protocol > 255:
            raise ValueError(f"Architecture Error: Protocol is an 8-bit field (0-255). You entered {protocol}.")

        return router_ip, dest_ip, protocol

    def simulate_network_unreachable(self, router_ip: str, dest_ip: str, protocol: int) -> None:
        """The Autopsy Engine: Simulates Type 3 Code 0 and packages original header + 8 bytes."""
        
        icmp_type = 3  # Destination Unreachable
        icmp_code = 0  # Network Unreachable
        
        # Construct the simulated original failed IPv4 Header (20 bytes)
        # Version/IHL: 0x45, ToS: 0x00, Total Length: 0x003C (60 bytes)
        orig_header = {
            "version_ihl": "0x45",
            "total_len": "0x003C",
            "id": "0xABCD",
            "ttl": "64",
            "protocol": f"0x{protocol:02X}",
            "checksum": "0x1A2B",
            "src": "192.168.1.50",
            "dst": dest_ip
        }
        
        # The mandatory 8 bytes of the original payload (e.g., TCP/UDP ports)
        orig_payload_bytes = "0x005301BB (Source Port: 83, Dest Port: 443)"
        
        # Security & Architectural Insight Generation
        insight = (
            f"ROUTING SILICON AUTOPSY: Core router ({router_ip}) evaluated its routing table for destination {dest_ip}, "
            f"found no matching subnet or default gateway, and dropped the packet. "
            f"Crucially, it generated an ICMP Type 3 Code 0 packet, encapsulating the original 20-byte IP header "
            f"plus the first 8 bytes of the payload so the sending host knows exactly which socket/application failed."
        )

        # Update State Tree
        self.autopsy_state = {
            "router_ip": router_ip,
            "dest_ip": dest_ip,
            "type": icmp_type,
            "code": icmp_code,
            "header": orig_header,
            "payload_snippet": orig_payload_bytes,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.autopsy_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03E: ICMP NETWORK UNREACHABLE (TYPE 3, CODE 0) ".center(width))
        print("=" * width)
        
        print(f" [+] Originating Router : {state['router_ip']}")
        print(f" [+] Unreachable Target : {state['dest_ip']}")
        print("-" * width)
        
        print(" [i] CONTROL PLANE INTERCEPT:")
        time.sleep(0.2)
        print(f"     -> [TX] Router drops packet and generates ICMP Type {state['type']} Code {state['code']}")
        print(f"             Meaning: Network Unreachable (No route in routing table).")
        time.sleep(0.3)
        print("     -> [ENCAPSULATION] Wrapping original IP header + 8 payload bytes into ICMP data area...")
        print("-" * width)
        
        print(" [!] ENCAPSULATED FAILED PACKET (THE AUTOPSY PAYLOAD):")
        hdr = state['header']
        print(f"     -> Failed IP Header : Ver/IHL: {hdr['version_ihl']} | Total Len: {hdr['total_len']} | ID: {hdr['id']}")
        print(f"                           TTL: {hdr['ttl']} | Proto: {hdr['protocol']} | Checksum: {hdr['checksum']}")
        print(f"                           Src: {hdr['src']} -> Dst: {hdr['dst']}")
        print(f"     -> First 8 Payload  : {state['payload_snippet']}")
        print("-" * width)
        
        print(f" [!] ARCHITECTURAL DIAGNOSTIC:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPNetworkUnreachableEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03E_ICMP_NETWORK_UNREACHABLE_SIM INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Enter Network Unreachable Simulation Parameters:")
            router_in = input("    Router IP raising error (e.g., 10.0.0.1) : ").strip()
            if router_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not router_in: continue
            
            dest_in   = input("    Unreachable Destination (e.g., 172.20.5.1): ").strip()
            proto_in  = input("    Protocol of failed packet (6=TCP, 17=UDP): ").strip()
                
            router, dest, proto = engine.validate_inputs(router_in, dest_in, proto_in)
            engine.simulate_network_unreachable(router, dest, proto)
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