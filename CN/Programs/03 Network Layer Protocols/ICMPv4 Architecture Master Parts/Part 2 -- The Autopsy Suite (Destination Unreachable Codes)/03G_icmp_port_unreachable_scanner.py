import sys
import re
import shutil
import time
from typing import Any, Dict, List, Tuple

class ICMPPortUnreachableEngine:
    scanner_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.scanner_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, target_ip: str, port_list_str: str, open_ports_str: str) -> Tuple[str, List[int], List[int]]:
        # IP Validation
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ip_pattern, target_ip)
        if not match:
            raise ValueError("Syntax Error: Target IP format invalid (e.g., 192.168.1.50).")
        for idx, octet_str in enumerate(match.groups()):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        # Port List Parsing
        def parse_ports(raw: str, label: str) -> List[int]:
            parsed: List[int] = []
            if not raw.strip():
                return parsed
            for item in raw.split(','):
                item = item.strip()
                if not item:
                    continue
                try:
                    p = int(item)
                except ValueError:
                    raise ValueError(f"Type Error: {label} values must be integers. Found '{item}'.")
                if p < 1 or p > 65535:
                    raise ValueError(f"Architecture Error: {label} port {p} exceeds 16-bit range (1-65535).")
                parsed.append(p)
            return parsed

        scan_ports = parse_ports(port_list_str, "Scan Target Port")
        open_ports = parse_ports(open_ports_str, "Open/Listening Port")

        if not scan_ports:
            raise ValueError("Logical Error: You must specify at least one UDP port to scan.")

        return target_ip, scan_ports, open_ports

    def simulate_udp_scan(self, target_ip: str, scan_ports: List[int], open_ports: List[int]) -> None:
        """The Port Unreachable Engine: Simulates Nmap UDP Scan physics and ICMP Type 3 Code 3 replies."""
        results: List[Dict[str, Any]] = []

        for port in scan_ports:
            is_open = port in open_ports
            
            # UDP Scanning Mechanics:
            # If open: Application receives UDP datagram and typically stays silent (or replies with UDP application data).
            # If closed: Host OS kernel rejects UDP packet and fires ICMP Type 3 Code 3 (Port Unreachable).
            if is_open:
                state = "OPEN | FILTERED"
                icmp_response = "None (Application consumed UDP packet or no ICMP returned)"
                encapsulated = "N/A"
            else:
                state = "CLOSED"
                icmp_response = "ICMP Type 3, Code 3 (Port Unreachable)"
                encapsulated = f"IPv4 Header (Proto 17) + UDP Header (DstPort: {port})"

            results.append({
                "port": port,
                "state": state,
                "icmp_response": icmp_response,
                "encapsulated": encapsulated
            })

        # Security & Architectural Insight Generation
        insight = (
            "UDP SCANNING MATHEMATICS (RFC 792 & RFC 1122): Unlike TCP which has deterministic SYN/ACK or RST handshakes, "
            "raw UDP is connectionless. A port is deduced as CLOSED only when the target kernel emits an ICMP Type 3 Code 3. "
            "If no ICMP is received, Nmap marks the port as 'open|filtered' because stateful firewalls silently drop packets, "
            "producing the exact same observable signature as a listening application."
        )

        # Update State Tree
        self.scanner_state = {
            "target": target_ip,
            "results": results,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.scanner_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03G: ICMP PORT UNREACHABLE SCANNER (TYPE 3, CODE 3) ".center(width))
        print("=" * width)
        
        print(f" [+] Target Node IP : {state['target']}")
        print(f" [+] Protocol Probe : UDP (Protocol 17)")
        print("-" * width)
        
        print(f" {'UDP PORT':<10} | {'INFERRED STATE':<18} | {'ICMP FEEDBACK RECEIVED':<38}")
        print("-" * width)
        
        for res in state['results']:
            time.sleep(0.1) # Simulate wire timing
            print(f" {res['port']:<10} | {res['state']:<18} | {res['icmp_response']:<38}")
            if res['state'] == "CLOSED":
                print(f"   [!] AUTOPSY PAYLOAD: Encapsulated -> {res['encapsulated']}")
            
        print("-" * width)
        print(f" [!] ARCHITECTURAL & RECONNAISSANCE INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPPortUnreachableEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03G_ICMP_PORT_UNREACHABLE_SCANNER INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Enter UDP Port Scan Parameters:")
            target_in = input("    Target Host IP                  (e.g., 10.0.0.15) : ").strip()
            if target_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not target_in: continue
            
            ports_in  = input("    Ports to Probe (comma-separated, e.g., 53,67,123,161): ").strip()
            open_in   = input("    Ports Listening (Mock Open Ports, e.g., 53,123)       : ").strip()
                
            tgt, scan_p, open_p = engine.validate_inputs(target_in, ports_in, open_in)
            engine.simulate_udp_scan(tgt, scan_p, open_p)
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