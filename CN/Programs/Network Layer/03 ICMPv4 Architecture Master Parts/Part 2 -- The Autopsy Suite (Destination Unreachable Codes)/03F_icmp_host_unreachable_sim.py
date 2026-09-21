import sys
import re
import shutil
import time
from typing import Any, Dict, Tuple

class ICMPHostUnreachableEngine:
    autopsy_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.autopsy_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, last_hop_router: str, target_ip: str, arp_retries: str) -> Tuple[str, str, int]:
        # Input Bounds Validation & Descriptive Errors
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        
        for ip, label in [(last_hop_router, "Last-Hop Router IP"), (target_ip, "Target Host IP")]:
            match = re.match(ip_pattern, ip)
            if not match:
                raise ValueError(f"Syntax Error: {label} format invalid (e.g., 192.168.1.1).")
            for idx, octet_str in enumerate(match.groups()):
                if int(octet_str) > 255:
                    raise ValueError(f"Architecture Error: {label} Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        if last_hop_router == target_ip:
            raise ValueError("Logical Error: The last-hop router cannot be the destination host itself.")

        try:
            retries = int(arp_retries)
        except ValueError:
            raise ValueError("Type Error: ARP retries count must be an integer.")
            
        if retries < 1 or retries > 10:
            raise ValueError("Bounds Error: ARP retries must be between 1 and 10 attempts.")

        return last_hop_router, target_ip, retries

    def simulate_host_unreachable(self, router_ip: str, target_ip: str, retries: int) -> None:
        """The Layer 2/3 Boundary Autopsy: Simulates ARP resolution failure resulting in Type 3 Code 1."""
        
        icmp_type = 3  # Destination Unreachable
        icmp_code = 1  # Host Unreachable
        
        # Layer 2 ARP resolution failure timeline
        arp_events = []
        for attempt in range(1, retries + 1):
            arp_events.append({
                "attempt": attempt,
                "action": f"Router {router_ip} broadcasts ARP Request: 'Who has {target_ip}? Tell {router_ip}'",
                "result": "TIMED OUT (No Layer 2 ARP Reply received)"
            })

        # Encapsulated Original IP Header (20 bytes)
        orig_header = {
            "version_ihl": "0x45",
            "total_len": "0x0054",  # 84 bytes
            "id": "0xFE10",
            "ttl": "58",
            "protocol": "0x01 (ICMP)",
            "checksum": "0x89AC",
            "src": "10.10.10.25",
            "dst": target_ip
        }
        
        # First 8 bytes of original payload
        orig_payload_bytes = "0x0800A1B2 (Type 8 Echo Request, Identifier & Sequence)"

        # Security & Architectural Insight Generation
        insight = (
            f"LAYER 2/LAYER 3 BOUNDARY BREAKDOWN: Unlike 'Network Unreachable' (Type 3 Code 0) which fails at intermediate routing tables, "
            f"'Host Unreachable' (Type 3 Code 1) proves the packet reached the destination subnet's default gateway ({router_ip}), "
            f"but the physical host ({target_ip}) did not respond to {retries} ARP broadcast attempts. "
            f"This indicates the device is powered down, disconnected from Layer 2 switch fabric, or has strict ARP filtering."
        )

        # Update State Tree
        self.autopsy_state = {
            "router_ip": router_ip,
            "target_ip": target_ip,
            "retries": retries,
            "arp_log": arp_events,
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
        print(" [>] MODULE 03F: ICMP HOST UNREACHABLE (TYPE 3, CODE 1) ".center(width))
        print("=" * width)
        
        print(f" [+] Last-Hop Gateway Router : {state['router_ip']}")
        print(f" [+] Target Unresponsive IP  : {state['target_ip']}")
        print("-" * width)
        
        print(" [i] LAYER 2 ARP RESOLUTION FAILURE SEQUENCE:")
        for event in state['arp_log']:
            time.sleep(0.1)
            print(f"     -> Attempt {event['attempt']}: {event['action']}")
            print(f"        Result   : {event['result']}")
            
        print("-" * width)
        print(f" [!] ICMP AUTOPSY EMISSION: Type {state['type']} | Code {state['code']} (Host Unreachable)")
        print("     -> [ENCAPSULATION] Packing original IP header + first 8 payload bytes into ICMP body...")
        print("-" * width)
        
        print(" [!] RECOVERED ORIGINAL PACKET ARTIFACTS:")
        hdr = state['header']
        print(f"     -> Failed IP Header : Ver/IHL: {hdr['version_ihl']} | Total Len: {hdr['total_len']} | ID: {hdr['id']}")
        print(f"                           TTL: {hdr['ttl']} | Proto: {hdr['protocol']} | Checksum: {hdr['checksum']}")
        print(f"                           Src: {hdr['src']} -> Dst: {hdr['dst']}")
        print(f"     -> First 8 Payload  : {state['payload_snippet']}")
        print("-" * width)
        
        print(f" [!] ARCHITECTURAL & DIAGNOSTIC INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPHostUnreachableEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03F_ICMP_HOST_UNREACHABLE_SIM INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Enter Host Unreachable Simulation Parameters:")
            router_in = input("    Last-Hop Router Gateway (e.g., 192.168.1.1) : ").strip()
            if router_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not router_in: continue
            
            target_in = input("    Target Host IP          (e.g., 192.168.1.99): ").strip()
            retry_in  = input("    ARP Retries Attempted   (e.g., 3)           : ").strip()
                
            router, target, retries = engine.validate_inputs(router_in, target_in, retry_in)
            engine.simulate_host_unreachable(router, target, retries)
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