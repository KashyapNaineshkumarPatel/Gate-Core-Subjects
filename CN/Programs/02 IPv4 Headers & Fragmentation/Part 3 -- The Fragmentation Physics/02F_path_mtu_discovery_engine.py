import sys
import shutil
import time
from typing import Any, Dict, List, Tuple

class PathMTUDiscoveryEngine:
    pmtud_state: Dict[str, Any]

    def __init__(self) -> None:
        # State Management Engine
        self.pmtud_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 95)

    def validate_inputs(self, payload_input: str, mtus_input: str, icmp_input: str) -> Tuple[int, List[int], bool]:
        # 1. Payload Validation
        try:
            payload_size = int(payload_input)
        except ValueError as exc:
            raise ValueError("Type Error: The Initial Payload size must be an integer.") from exc
            
        if payload_size < 1 or payload_size > 65515:
            raise ValueError("Exhaustion Error: Payload must be between 1 and 65,515 bytes.")

        # 2. MTU Path Validation
        raw_mtus = mtus_input.split(',')
        route_mtus: List[int] = []
        for idx, mtu_str in enumerate(raw_mtus):
            try:
                mtu_val = int(mtu_str.strip())
                if mtu_val < 68:
                    raise ValueError(f"Architecture Error: Hop {idx+1} MTU ({mtu_val}) violates RFC 791 minimum of 68.")
                route_mtus.append(mtu_val)
            except ValueError as exc:
                raise ValueError("Syntax Error: Route MTUs must be a comma-separated list of integers (e.g., 1500,1400,1200).") from exc
                
        if not route_mtus:
            raise ValueError("Logical Error: You must provide at least one router MTU for the path.")

        # 3. ICMP Block State Validation
        icmp_clean = icmp_input.strip().lower()
        yes_values = {'y', 'yes', 'true', '1'}
        no_values = {'n', 'no', 'false', '0'}
        if icmp_clean in yes_values:
            icmp_blocked = True
        elif icmp_clean in no_values:
            icmp_blocked = False
        else:
            raise ValueError("Type Error: ICMP block toggle must be 'y' or 'n'.")

        return payload_size, route_mtus, icmp_blocked

    def simulate_pmtud(self, initial_payload: int, route_mtus: List[int], icmp_blocked: bool) -> None:
        """The PMTUD State Machine: Traverses the network, intercepting drops and adjusting sizes."""
        ip_header = 20
        current_packet_size = initial_payload + ip_header
        
        traversal_log: List[Dict[str, str]] = []
        hop_idx = 0
        black_hole_triggered = False

        while hop_idx < len(route_mtus):
            link_mtu = route_mtus[hop_idx]
            
            traversal_log.append({
                "hop": f"Router {hop_idx + 1}",
                "action": "TRANSMIT",
                "details": f"Attempting to send {current_packet_size}-byte packet (DF=1) across {link_mtu}-byte link."
            })
            
            # Check if the packet fits through the link interface
            if current_packet_size <= link_mtu:
                traversal_log.append({
                    "hop": f"Router {hop_idx + 1}",
                    "action": "SUCCESS",
                    "details": "Packet fits. Forwarding to next hop."
                })
                hop_idx += 1
            else:
                # The packet is too large and the DF bit is set to 1. It MUST be dropped.
                traversal_log.append({
                    "hop": f"Router {hop_idx + 1}",
                    "action": "DROP",
                    "details": f"Packet size ({current_packet_size}) exceeds MTU ({link_mtu}). DF bit strictly prohibits fragmentation."
                })
                
                if icmp_blocked:
                    # The PMTUD Black Hole Trap
                    traversal_log.append({
                        "hop": f"Router {hop_idx + 1}",
                        "action": "BLACK HOLE",
                        "details": "ICMP Type 3 Code 4 dropped by firewall. Host never receives the error. Connection silently hangs forever."
                    })
                    black_hole_triggered = True
                    break
                else:
                    # Successful ICMP generation and PMTUD adjustment
                    traversal_log.append({
                        "hop": f"Router {hop_idx + 1}",
                        "action": "ICMP SENT",
                        "details": f"Generated ICMP Type 3 Code 4: 'Fragmentation Needed'. Reporting Next-Hop MTU: {link_mtu}."
                    })
                    
                    # Host receives ICMP, adjusts its internal MTU state, and prepares to retry
                    current_packet_size = link_mtu
                    traversal_log.append({
                        "hop": "Sender Host",
                        "action": "ADJUST",
                        "details": f"Received ICMP. Adjusting dynamically to {current_packet_size} bytes. Retrying transmission."
                    })
                    # Note: We do not increment hop_idx because the sender must retry this exact hop with the new size.

        # Engineering Insight Generation
        insight = ""
        if black_hole_triggered:
            insight = "CRITICAL FAILURE: PMTUD Black Hole detected. Firewalls blocking all ICMP break TCP MSS negotiation. Traffic is completely stalled."
        else:
            insight = f"OPTIMIZED: Final End-to-End PMTUD Packet Size settled at {current_packet_size} bytes. No fragmentation required."

        # Update State Tree
        self.pmtud_state = {
            "initial_packet": initial_payload + ip_header,
            "final_packet": "STALLED" if black_hole_triggered else current_packet_size,
            "path_mtus": route_mtus,
            "icmp_blocked": icmp_blocked,
            "log": traversal_log,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.pmtud_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 02F: PATH MTU DISCOVERY ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] Initial Packet Size : {state['initial_packet']} bytes (DF Bit = 1)")
        print(f" [+] Network Path MTUs   : {', '.join(map(str, state['path_mtus']))}")
        print(" [+] ICMP Firewall State : " + ("BLOCKED (Dangerous)" if state['icmp_blocked'] else "ALLOWED"))
        print("-" * width)
        
        print(" [i] PACKET TRAVERSAL LOG:")
        for entry in state['log']:
            # Using formatting to align columns nicely
            print(f"     [{entry['hop']:<12}] | {entry['action']:<10} | {entry['details']}")
            # Add a micro-throttle to simulate network delays
            time.sleep(0.05)
            
        print("-" * width)
        
        print(" [!] ARCHITECTURAL DIAGNOSTIC:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = PathMTUDiscoveryEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 02F_PATH_MTU_DISCOVERY_ENGINE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            print("\n[?] Enter PMTUD Parameters:")
            payload_in = input("    Initial Payload Size (e.g., 1480)       : ").strip()
            if payload_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not payload_in: continue
            
            mtus_in = input("    Route MTUs (comma-separated, e.g., 1500,1400,1500): ").strip()
            icmp_in = input("    Block ICMP at Firewall? (y/n)           : ").strip()
                
            payload, route_mtus, icmp_blocked = engine.validate_inputs(payload_in, mtus_in, icmp_in)
            engine.simulate_pmtud(payload, route_mtus, icmp_blocked)
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