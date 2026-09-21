import sys
import re
import shutil
import time
import random
from typing import Any, Dict

class ICMPAddressMaskEngine:
    mask_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.mask_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, target_ip: str) -> str:
        # Input Bounds Validation & Descriptive Errors
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ip_pattern, target_ip)
        
        if not match:
            raise ValueError("Syntax Error: Target IP format invalid (e.g., 10.0.0.1).")
            
        for idx, octet_str in enumerate(match.groups()):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")
                
        return target_ip

    def _calculate_mask_from_cidr(self, cidr: int) -> str:
        """Physical binary math to generate standard subnet mask notation."""
        mask_binary = ('1' * cidr) + ('0' * (32 - cidr))
        octets = [str(int(mask_binary[i:i+8], 2)) for i in range(0, 32, 8)]
        return '.'.join(octets)

    def _ip_to_hex(self, ip_str: str) -> str:
        """Converts dotted decimal IP to 32-bit Hex for ICMP payload simulation."""
        octets = [int(x) for x in ip_str.split('.')]
        hex_val = (octets[0] << 24) + (octets[1] << 16) + (octets[2] << 8) + octets[3]
        return f"0x{hex_val:08X}"

    def simulate_mask_request(self, target_ip: str) -> None:
        """The Subnet Discovery Engine: Generates Type 17 Request and Type 18 Reply."""
        
        type_req = 17  # Address Mask Request
        type_rep = 18  # Address Mask Reply
        
        # OS assigns a 16-bit identifier and sequence number
        identifier = random.randint(1000, 65535)
        sequence = random.randint(1, 100)
        
        # Simulate the target router's actual subnet mask (randomly chosen for demonstration)
        # We assume an enterprise environment (e.g., /24 down to /29)
        simulated_cidr = random.randint(24, 29)
        actual_mask = self._calculate_mask_from_cidr(simulated_cidr)
        hex_mask = self._ip_to_hex(actual_mask)
        
        # Network transit simulation
        rtt = round(random.uniform(2.0, 10.0), 2)
        
        # Security & Architectural Insight Generation
        insight = (
            f"CRITICAL EXPOSURE: The target answered a Type 17 request. "
            f"The network architecture is now exposed. An attacker knows the exact subnet boundary is /{simulated_cidr} ({actual_mask}). "
            f"They can immediately calculate the exact Broadcast ID to launch a Smurf DDoS attack, "
            f"or map the usable IP range to constrain a stealth reconnaissance sweep."
        )

        # Update State Tree
        self.mask_state = {
            "target": target_ip,
            "type_req": type_req,
            "type_rep": type_rep,
            "identifier": identifier,
            "sequence": sequence,
            "rtt": rtt,
            "cidr": simulated_cidr,
            "mask_decimal": actual_mask,
            "mask_hex": hex_mask,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.mask_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03D: ICMP ADDRESS MASK AGENT (TYPE 17/18) ".center(width))
        print("=" * width)
        
        print(f" [+] Target Router IP : {state['target']}")
        print("-" * width)
        
        print(" [i] CONTROL PLANE TRAVERSAL:")
        time.sleep(0.2)
        print(f"     -> [TX] Sent ICMP Type {state['type_req']} (Address Mask Request) to {state['target']}")
        print(f"             ID: {state['identifier']} | Seq: {state['sequence']} | Payload: 0x00000000")
        time.sleep(0.4)
        print(f"     <- [RX] Received ICMP Type {state['type_rep']} (Address Mask Reply) in {state['rtt']} ms")
        print("-" * width)
        
        print(f" [!] EXTRACTED ROUTING SILICON PAYLOAD:")
        print(f"     -> 32-Bit Hex Mask : {state['mask_hex']}")
        print(f"     -> Decimal Mask    : {state['mask_decimal']}")
        print(f"     -> CIDR Notation   : /{state['cidr']}")
        print("-" * width)
        
        print(f" [!] SECURITY IDS ALERT:")
        print(f"     -> {state['insight']}")
        print(f"     -> NOTE: Deprecated by RFC 6918. Modern firewalls MUST drop Type 17/18.")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPAddressMaskEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03D_ICMP_ADDRESS_MASK_AGENT INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Enter Target IP to extract its internal subnet mask:")
            target_in = input("    Target IP (e.g., 10.0.0.1): ").strip()
            if target_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not target_in: continue
                
            target = engine.validate_inputs(target_in)
            engine.simulate_mask_request(target)
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