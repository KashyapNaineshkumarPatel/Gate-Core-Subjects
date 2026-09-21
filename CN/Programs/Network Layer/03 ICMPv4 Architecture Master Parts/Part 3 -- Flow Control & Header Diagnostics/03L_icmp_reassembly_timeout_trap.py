import sys
import re
import shutil
import time
from typing import Any, Dict, List, Tuple

class ICMPReassemblyTimeoutEngine:
    timeout_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.timeout_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, host_ip: str, total_frags_str: str, received_frags_str: str, timer_limit_str: str) -> Tuple[str, int, List[int], int]:
        # IP Validation
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ip_pattern, host_ip)
        if not match:
            raise ValueError("Syntax Error: Host IP format invalid (e.g., 192.168.1.50).")
        for idx, octet_str in enumerate(match.groups()):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        # Total Fragments Validation
        try:
            total_frags = int(total_frags_str)
            timer_limit = int(timer_limit_str)
        except ValueError:
            raise ValueError("Type Error: Total fragments and timer limit must be integers.")

        if total_frags < 2 or total_frags > 20:
            raise ValueError("Bounds Error: Sliced packet must have between 2 and 20 total fragments.")

        if timer_limit < 5 or timer_limit > 120:
            raise ValueError("Architecture Error: RFC reassembly timeout timer is typically between 5 and 120 seconds.")

        # Received Fragments Parsing
        received: List[int] = []
        if not received_frags_str.strip():
            raise ValueError("Logical Error: At least one fragment must arrive to initiate the reassembly buffer.")

        for item in received_frags_str.split(','):
            item = item.strip()
            if not item:
                continue
            try:
                frag_num = int(item)
            except ValueError:
                raise ValueError(f"Type Error: Fragment index must be an integer. Found '{item}'.")
            if frag_num < 1 or frag_num > total_frags:
                raise ValueError(f"Bounds Error: Fragment {frag_num} exceeds configured total of {total_frags}.")
            if frag_num not in received:
                received.append(frag_num)

        return host_ip, total_frags, received, timer_limit

    def simulate_reassembly(self, host_ip: str, total_frags: int, received_frags: List[int], timer_limit: int) -> None:
        """Simulates kernel reassembly queue, timer expiration, and ICMP Type 11 Code 1 generation."""
        
        icmp_type = 11  # Time Exceeded
        icmp_code = 1   # Fragment Reassembly Time Exceeded
        
        # Slicing simulation parameters
        ip_id = "0x7E3F"
        frag_size = 1480  # Standard MTU 1500 payload
        received_frags.sort()
        
        queue_events = []
        has_fragment_zero = (1 in received_frags)
        all_arrived = (len(received_frags) == total_frags)
        
        current_time = 0.0
        for f in received_frags:
            offset = (f - 1) * (frag_size // 8)
            mf = 1 if f < total_frags else 0
            current_time += 0.2
            queue_events.append({
                "time": f"[T+{current_time:.1f}s]",
                "frag": f,
                "offset": offset,
                "mf": mf,
                "status": f"Stored in Kernel Buffer (IP ID: {ip_id}, Offset: {offset}, MF: {mf})"
            })

        # Check reassembly status
        if all_arrived:
            reassembly_success = True
            icmp_emitted = False
            details = "All fragments arrived within timer limits. Kernel reassembled original payload cleanly."
            security_note = "OPTIMAL: Reassembly buffer cleared successfully. Transport Layer processing initiated."
            encapsulated_hdr = "N/A"
        else:
            reassembly_success = False
            queue_events.append({
                "time": f"[T+{float(timer_limit):.1f}s]",
                "frag": "-",
                "offset": "-",
                "mf": "-",
                "status": f"TIMER EXPIRED ({timer_limit}s limit reached). Incomplete packet queue purged."
            })
            
            # RFC 792 / RFC 1122 Rule:
            # An ICMP Type 11 Code 1 message MUST ONLY be sent if Fragment 0 (Offset 0) was received,
            # because without Fragment 0, the host does not have the original IP header to encapsulate!
            if has_fragment_zero:
                icmp_emitted = True
                details = (
                    f"Reassembly timer expired. Host received Fragment 0 (Offset 0). "
                    f"Host dropped all buffered fragments and generated ICMP Type 11 Code 1 to sender."
                )
                encapsulated_hdr = f"Ver: 4, IHL: 5, ID: {ip_id}, Flags: 0x01 (MF=1), Offset: 0, Proto: 6 (TCP), Src: 10.0.0.99"
                security_note = (
                    "RFC 792 COMPLIANCE: Because Fragment 0 arrived, the host successfully reconstructed "
                    "the autopsy payload and emitted ICMP Type 11 Code 1. "
                    "Defense mechanism prevents kernel memory exhaustion from Rose / Fragment DoS floods."
                )
            else:
                icmp_emitted = False
                details = (
                    f"Reassembly timer expired. CRITICAL: Fragment 0 (Offset 0) was NEVER received. "
                    f"Host silently purged buffer without sending ICMP."
                )
                encapsulated_hdr = "None (Impossible without Fragment 0)"
                security_note = (
                    "SILENT BUFFER PURGE (RFC 1122 Section 3.2.2.4): Without Fragment 0, the kernel lacks "
                    "the original IP Header and L4 header snippet. It is physically prohibited from generating "
                    "an ICMP error because it cannot construct a valid encapsulated payload."
                )

        # Update State Tree
        self.timeout_state = {
            "host_ip": host_ip,
            "ip_id": ip_id,
            "total_frags": total_frags,
            "received_frags": received_frags,
            "timer_limit": timer_limit,
            "success": reassembly_success,
            "icmp_emitted": icmp_emitted,
            "events": queue_events,
            "details": details,
            "encapsulated": encapsulated_hdr,
            "security_note": security_note,
            "type": icmp_type,
            "code": icmp_code
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.timeout_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03L: ICMP REASSEMBLY TIMEOUT TRAP (TYPE 11, CODE 1) ".center(width))
        print("=" * width)
        
        print(f" [+] Reassembling Host IP : {state['host_ip']}")
        print(f" [+] Packet ID (16-bit)   : {state['ip_id']}")
        print(f" [+] Fragment Tracker     : {len(state['received_frags'])} of {state['total_frags']} Fragments Arrived")
        print(f" [+] Kernel Timeout Limit : {state['timer_limit']} seconds")
        print("-" * width)
        
        print(" [i] KERNEL REASSEMBLY QUEUE LIFECYCLE:")
        for ev in state['events']:
            time.sleep(0.1)
            print(f"     {ev['time']:<10} | Frag: {str(ev['frag']):<3} | {ev['status']}")
            
        print("-" * width)
        
        if not state['success']:
            print(" [!] REASSEMBLY FAILURE AUTOPSY:")
            print(f"     -> Outcome        : {state['details']}")
            if state['icmp_emitted']:
                print(f"     -> ICMP Generated : Type {state['type']}, Code {state['code']} (Fragment Reassembly Time Exceeded)")
                print(f"     -> Encapsulation  : {state['encapsulated']}")
            else:
                print(f"     -> ICMP Generated : [PROHIBITED] No ICMP sent (Fragment 0 Missing)")
            print("-" * width)
            
        print(f" [!] ARCHITECTURAL & RFC 1122 INSIGHT:")
        print(f"     -> {state['security_note']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPReassemblyTimeoutEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03L_ICMP_REASSEMBLY_TIMEOUT_TRAP INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure Fragment Reassembly Parameters:")
            host_in   = input("    Host IP Reassembling Packet (e.g., 192.168.1.50)   : ").strip()
            if host_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not host_in: continue
            
            total_in  = input("    Total Fragments in Original Datagram (e.g., 4)    : ").strip()
            recv_in   = input("    Arrived Fragments (comma-separated, e.g., 1,2,4)   : ").strip()
            timer_in  = input("    Reassembly Buffer Timeout in Seconds (e.g., 15)   : ").strip()
                
            host, total, recv, timer = engine.validate_inputs(host_in, total_in, recv_in, timer_in)
            engine.simulate_reassembly(host, total, recv, timer)
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