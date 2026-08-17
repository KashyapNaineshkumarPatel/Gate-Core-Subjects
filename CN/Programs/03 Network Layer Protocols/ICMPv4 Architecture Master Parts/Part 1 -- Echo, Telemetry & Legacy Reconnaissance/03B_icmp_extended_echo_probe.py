import sys
import re
import shutil
import time
import random
from typing import Any, Dict, Tuple

class ICMPExtendedEchoEngine:
    probe_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.probe_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, target_router: str, query_type: str, query_value: str) -> Tuple[str, int, str]:
        # Target IP Validation
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        if not re.match(ip_pattern, target_router):
            raise ValueError("Syntax Error: Target Router IP format invalid (e.g., 10.0.0.1).")
            
        for idx, octet_str in enumerate(target_router.split('.')):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        # Query Type Validation (RFC 8335 Object Types)
        valid_types = {'1': 'ifIndex', '2': 'ifName', '3': 'IPv4 Address'}
        if query_type not in valid_types:
            raise ValueError("Syntax Error: Query Type must be 1 (ifIndex), 2 (ifName), or 3 (IPv4).")
            
        q_type_int = int(query_type)

        # Query Value Validation based on Type
        if q_type_int == 1:  # ifIndex must be an integer
            try:
                int(query_value)
            except ValueError:
                raise ValueError("Type Error: ifIndex must be a numeric integer (e.g., 4).")
        elif q_type_int == 3:  # IPv4 must be a valid IP
            if not re.match(ip_pattern, query_value):
                raise ValueError("Syntax Error: Query value for Type 3 must be a valid IPv4 address.")
        elif q_type_int == 2:  # ifName is string, just ensure it's not empty
            if len(query_value) > 255:
                raise ValueError("Exhaustion Error: Interface names cannot exceed 255 characters.")

        return target_router, q_type_int, query_value

    def simulate_rfc8335_probe(self, router_ip: str, q_type: int, q_val: str) -> None:
        """The RFC 8335 Engine: Constructs Type 42 Request and parses Type 43 Reply."""
        
        # ICMP PROBE Parameters
        type_req = 42 # Extended Echo Request
        type_rep = 43 # Extended Echo Reply
        
        # Simulate network delay for traversing to the core router
        rtt = round(random.uniform(5.0, 15.0), 2)
        
        # Simulate Router Response State
        # In reality, this depends on the router's internal state. We mock realistic outcomes.
        l_bit = 0 # Local bit (1 if the interface is on the router itself)
        active_state = random.choice([
            "State 0: No Error (Interface UP and Active)",
            "State 1: Malformed Query",
            "State 2: No Such Interface (Does not exist)",
            "State 3: Sub-Interface Not Active",
            "State 4: Interface Administratively DOWN"
        ])
        
        # If the interface exists, L-bit is typically set to 1 by the responding router
        if "No Error" in active_state or "Administratively DOWN" in active_state:
            l_bit = 1
            
        # Security Insight Generation
        insight = ""
        if q_type == 2 and "No Error" in active_state:
            insight = "SUCCESS: Interface name resolved. WARNING: Allowing Type 42 exposes internal hardware naming conventions to attackers."
        elif "No Such Interface" in active_state:
            insight = "REJECTED: The router confirms it has no physical or logical interface matching that query."
        elif "Administratively DOWN" in active_state:
            insight = "DIAGNOSTIC: The interface exists but was shut down manually by a network administrator."
        else:
            insight = "ERROR: The query was rejected or malformed. Ensure the target router supports RFC 8335."

        # Update State Tree
        self.probe_state = {
            "router_ip": router_ip,
            "query_type": q_type,
            "query_val": q_val,
            "req_type": type_req,
            "rep_type": type_rep,
            "rtt": rtt,
            "l_bit": l_bit,
            "status": active_state,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.probe_state
        
        q_type_str = {1: "ifIndex (Numeric ID)", 2: "ifName (String)", 3: "IPv4 Address"}[state['query_type']]
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03B: ICMP EXTENDED ECHO PROBE (RFC 8335) ".center(width))
        print("=" * width)
        
        print(f" [+] Target Core Router : {state['router_ip']}")
        print(f" [+] Query Extension    : {q_type_str} -> '{state['query_val']}'")
        print("-" * width)
        
        print(" [i] CONTROL PLANE TRAVERSAL:")
        time.sleep(0.2)
        print(f"     -> [TX] Sent ICMP Type {state['req_type']} (Extended Echo Request) to {state['router_ip']}")
        time.sleep(0.4)
        print(f"     <- [RX] Received ICMP Type {state['rep_type']} (Extended Echo Reply) in {state['rtt']} ms")
        print("-" * width)
        
        print(" [i] ROUTER DIAGNOSTIC PAYLOAD (TYPE 43 RESPONSE):")
        print(f"     -> L-Bit (Local) : {state['l_bit']} {'(Interface belongs to this router)' if state['l_bit'] else '(Not local)'}")
        print(f"     -> Interface Code: {state['status']}")
        print("-" * width)
        
        print(f" [!] ARCHITECTURAL & SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPExtendedEchoEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03B_ICMP_EXTENDED_ECHO_PROBE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Enter RFC 8335 Probe Parameters:")
            router_in = input("    Target Router IP      (e.g., 10.0.0.254): ").strip()
            if router_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not router_in: continue
            
            print("    Query Object Types: 1 = ifIndex, 2 = ifName, 3 = IPv4 Address")
            q_type_in = input("    Select Query Type     (1/2/3)           : ").strip()
            q_val_in  = input("    Enter Query Value     (e.g., eth0)      : ").strip()
                
            router, q_type, q_val = engine.validate_inputs(router_in, q_type_in, q_val_in)
            engine.simulate_rfc8335_probe(router, q_type, q_val)
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