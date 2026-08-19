import sys
import re
import shutil
import time
from typing import Any, Dict, List, Tuple

class IPv4DiagnosticEngine:
    diagnostic_state: Dict[str, Any]

    def __init__(self):
        # State Management Engine
        self.diagnostic_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 85)

    def validate_syntax(self, ip_input: str) -> Tuple[List[int], int]:
        # Input Bounds Validation
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})$'
        match = re.match(pattern, ip_input)
        
        if not match:
            raise ValueError("Syntax Error: Format must be exactly IP/CIDR (e.g., 10.0.0.1/24)")
            
        octets = [int(match.group(i)) for i in range(1, 5)]
        cidr = int(match.group(5))
        
        for idx, octet in enumerate(octets):
            if octet < 0 or octet > 255:
                raise ValueError(
                    f"System Error: Octet {idx+1} is {octet}. IPv4 limits octets to 255 (8 bits). Memory overflow prevented."
                )
        if cidr < 0 or cidr > 32:
            raise ValueError(f"System Error: /{cidr} exceeds the 32-bit physical limit of IPv4.")
            
        return octets, cidr

    def _calculate_boundaries(self, octets: List[int], cidr: int) -> Tuple[List[int], List[int]]:
        """Calculates Network and Broadcast IDs to check for host assignment violations."""
        mask_binary_str = ('1' * cidr) + ('0' * (32 - cidr))
        mask_octets = [int(mask_binary_str[i:i+8], 2) for i in range(0, 32, 8)]
        
        network_octets = [octets[i] & mask_octets[i] for i in range(4)]
        
        inverted_mask_octets = [255 - m for m in mask_octets]
        broadcast_octets = [network_octets[i] | inverted_mask_octets[i] for i in range(4)]
        
        return network_octets, broadcast_octets

    def diagnose_ip(self, octets: List[int], cidr: int) -> None:
        """The Logical Classification Core."""
        network_octets, broadcast_octets = self._calculate_boundaries(octets, cidr)
        
        # 1. Descriptive Error Handling: Host Boundary Violations
        if cidr < 31: # /31 and /32 have special point-to-point/host route exceptions
            if octets == network_octets:
                raise ValueError(
                    "Logical Deployment Fault: You entered a Network ID.\n"
                    "All host bits are set to 0. This IP represents the physical wire itself. "
                    "It cannot be assigned to a computer's Network Interface Card (NIC)."
                )
            if octets == broadcast_octets:
                raise ValueError(
                    "Logical Deployment Fault: You entered a Broadcast ID.\n"
                    "All host bits are set to 1. This IP is reserved to flood packets to every device "
                    "on the subnet. It cannot be assigned to a single NIC."
                )

        first_octet = octets[0]
        second_octet = octets[1]
        
        ip_class = "Unknown"
        designation = "Public (Internet Routable)"
        notes: List[str] = []

        # 2. Classful Identification & Hardware Limits
        if 0 <= first_octet <= 127:
            ip_class = "Class A (Legacy /8)"
            if first_octet == 0:
                designation = "Reserved (Software)"
                notes.append("0.0.0.0 represents the default route (any unconfigured network).")
            elif first_octet == 127:
                designation = "Loopback (Diagnostic)"
                notes.append("Traffic sent here never hits the physical wire. It bounces back down the TCP/IP stack.")
        elif 128 <= first_octet <= 191:
            ip_class = "Class B (Legacy /16)"
        elif 192 <= first_octet <= 223:
            ip_class = "Class C (Legacy /24)"
        elif 224 <= first_octet <= 239:
            ip_class = "Class D (Multicast)"
            designation = "Reserved (Multicast)"
            notes.append("Used for one-to-many streaming (e.g., OSPF routing updates, IPTV). Cannot be assigned to a host.")
        elif 240 <= first_octet <= 255:
            ip_class = "Class E (Experimental)"
            designation = "Reserved (Military/Research)"
            if octets == [255, 255, 255, 255]:
                notes.append("255.255.255.255 is the Global Limited Broadcast. It stops at the first router.")
            else:
                notes.append("This entire block is locked by IANA and cannot be routed on the public internet.")

        # 3. RFC 1918 Private Space Detection
        if first_octet == 10:
            designation = "Private (RFC 1918)"
            notes.append("Massive enterprise private block. Dropped by internet backbone routers. Requires NAT.")
        elif first_octet == 172 and 16 <= second_octet <= 31:
            designation = "Private (RFC 1918)"
            notes.append("Medium enterprise private block. Requires NAT for internet access.")
        elif first_octet == 192 and second_octet == 168:
            designation = "Private (RFC 1918)"
            notes.append("Small business/home private block. Requires NAT for internet access.")
        elif first_octet == 169 and second_octet == 254:
            designation = "APIPA (Link-Local)"
            notes.append("DHCP allocation failed. OS self-assigned this IP to maintain local LAN connectivity.")

        # Update State Tree
        self.diagnostic_state = {
            "target": f"{'.'.join(map(str, octets))}/{cidr}",
            "class": ip_class,
            "designation": designation,
            "notes": notes
        }

    def render_ui(self):
        # Asynchronous UI Throttle
        time.sleep(0.15) 
        width = self.get_terminal_width()
        state = self.diagnostic_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 01B: IPv4 DIAGNOSTIC SCANNER ".center(width))
        print("=" * width)
        
        print(f" [*] Target IP        : {state['target']}")
        print(f" [+] Architecture     : {state['class']}")
        print(f" [+] Routing Scope    : {state['designation']}")
        print("-" * width)
        
        print(" [i] ENGINEERING NOTES:")
        if not state['notes']:
            print("     -> Standard unicast IP address. Fully routable.")
        for note in state['notes']:
            print(f"     -> {note}")
            
        print("=" * width + "\n")

def interactive_loop():
    engine = IPv4DiagnosticEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 01B_IPv4_DIAGNOSTIC_SCANNER INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            user_input = input("\n[?] Enter IP/CIDR to diagnose (e.g., 172.16.0.5/24): ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                print("\n[+] Graceful shutdown initiated. Goodbye.")
                sys.exit(0)
                
            if not user_input:
                continue
                
            octets, cidr = engine.validate_syntax(user_input)
            engine.diagnose_ip(octets, cidr)
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