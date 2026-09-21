import sys
import re
import shutil
import time
from typing import Any, Dict, List, Tuple

class ICMPAdminProhibitedEngine:
    ids_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.ids_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, firewall_ip: str, target_ip: str, dport: str, acl_action: str) -> Tuple[str, str, int, str]:
        # IP Validation
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        for ip, label in [(firewall_ip, "Firewall/Gateway IP"), (target_ip, "Target Protected IP")]:
            match = re.match(ip_pattern, ip)
            if not match:
                raise ValueError(f"Syntax Error: {label} format invalid (e.g., 10.0.0.1).")
            for idx, octet_str in enumerate(match.groups()):
                if int(octet_str) > 255:
                    raise ValueError(f"Architecture Error: {label} Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        # Port Validation
        try:
            port = int(dport)
        except ValueError:
            raise ValueError("Type Error: Destination Port must be an integer.")
        if port < 1 or port > 65535:
            raise ValueError(f"Architecture Error: Port must be between 1 and 65535. Received {port}.")

        # ACL Action Validation
        valid_actions = {
            '1': 'DROP_SILENT',
            '2': 'REJECT_NET_PROHIBITED',   # Type 3, Code 9
            '3': 'REJECT_HOST_PROHIBITED',  # Type 3, Code 10
            '4': 'REJECT_ADMIN_PROHIBITED'  # Type 3, Code 13
        }
        if acl_action not in valid_actions:
            raise ValueError("Syntax Error: Select ACL action 1, 2, 3, or 4.")

        return firewall_ip, target_ip, port, valid_actions[acl_action]

    def simulate_filtering(self, fw_ip: str, tgt_ip: str, port: int, action: str) -> None:
        """Simulates firewall ACL enforcement, state inspection, and ICMP rejection telemetry."""
        
        # ICMP Codes mapping
        code_map = {
            'REJECT_NET_PROHIBITED': (9, "Communication with Destination Network is Administratively Prohibited"),
            'REJECT_HOST_PROHIBITED': (10, "Communication with Destination Host is Administratively Prohibited"),
            'REJECT_ADMIN_PROHIBITED': (13, "Communication Administratively Prohibited (RFC 1812 Filtered)")
        }

        encapsulated_hdr = {
            "src": "192.168.10.50",
            "dst": tgt_ip,
            "proto": "TCP (6)",
            "dport": port,
            "flags": "SYN"
        }

        if action == "DROP_SILENT":
            icmp_emitted = False
            code_num = None
            code_desc = "None (Silent Packet Drop / Blackhole)"
            scanner_perception = "FILTERED (Probe timed out without feedback)"
            security_note = (
                "STEALTH DEFENSE: Silent dropping minimizes attack surface intelligence. "
                "Port scanners (like Nmap) are forced to wait for retransmission timeouts, "
                "drastically slowing down external reconnaissance sweeps."
            )
        else:
            icmp_emitted = True
            code_num, code_desc = code_map[action]
            scanner_perception = f"FILTERED / REJECTED (Explicit Type 3 Code {code_num} received)"
            security_note = (
                f"ACL LEAKAGE ALERT: Emitting ICMP Type 3 Code {code_num} actively confirms the existence "
                f"of firewall/ACL enforcement at {fw_ip}. Attackers can map exact boundary rulesets "
                f"without waiting for timeouts and deduce internal network topology segmentation."
            )

        # Update State Tree
        self.ids_state = {
            "firewall_ip": fw_ip,
            "target_ip": tgt_ip,
            "dport": port,
            "action": action,
            "icmp_emitted": icmp_emitted,
            "code_num": code_num,
            "code_desc": code_desc,
            "perception": scanner_perception,
            "encapsulated": encapsulated_hdr,
            "security_note": security_note
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.ids_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03H: ICMP ADMIN PROHIBITED IDS (TYPE 3, CODES 9/10/13) ".center(width))
        print("=" * width)
        
        print(f" [+] Enforcement Firewall Gateway : {state['firewall_ip']}")
        print(f" [+] Target Protected Endpoint   : {state['target_ip']}:{state['dport']}")
        print(f" [+] Configured ACL Policy Rule  : {state['action']}")
        print("-" * width)
        
        print(" [i] CONTROL PLANE FIREWALL EVENT SEQUENCE:")
        time.sleep(0.2)
        print(f"     -> Ingress Packet: {state['encapsulated']['src']} -> {state['target_ip']}:{state['dport']} [TCP SYN]")
        time.sleep(0.2)
        print(f"     -> Policy Decision: Match Drop/Reject Rule -> Enforcing '{state['action']}'")
        
        if state['icmp_emitted']:
            time.sleep(0.2)
            print(f"     <- Egress Telemetry: Generated ICMP Type 3, Code {state['code_num']}")
            print(f"        RFC Definition : {state['code_desc']}")
            print(f"     -> Encapsulation  : Original IP Header + First 8 Bytes of TCP Payload (Dport {state['dport']})")
        else:
            time.sleep(0.2)
            print("     <- Egress Telemetry: [SILENT] Packet purged from NIC ring buffer. 0 bytes returned.")
            
        print("-" * width)
        print(f" [!] SCANNER RECONNAISSANCE SIGNATURE:")
        print(f"     -> Nmap State Classification : {state['perception']}")
        print("-" * width)
        print(f" [!] ARCHITECTURAL & IDS ANALYSIS:")
        print(f"     -> {state['security_note']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPAdminProhibitedEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03H_ICMP_ADMIN_PROHIBITED_IDS INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure Firewall / ACL Parameters:")
            fw_in   = input("    Firewall Gateway IP   (e.g., 10.0.0.1) : ").strip()
            if fw_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not fw_in: continue
            
            tgt_in  = input("    Target Protected IP   (e.g., 10.0.0.80): ").strip()
            port_in = input("    Destination TCP Port  (e.g., 22)       : ").strip()
            
            print("    Select ACL Rule Enforcement Behavior:")
            print("      1: Silent DROP (Blackhole - No ICMP)")
            print("      2: REJECT Network Prohibited (Type 3, Code 9)")
            print("      3: REJECT Host Prohibited    (Type 3, Code 10)")
            print("      4: REJECT Admin Prohibited   (Type 3, Code 13 - RFC 1812)")
            act_in  = input("    Selection (1/2/3/4)                    : ").strip()
                
            fw, tgt, port, action = engine.validate_inputs(fw_in, tgt_in, port_in, act_in)
            engine.simulate_filtering(fw, tgt, port, action)
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