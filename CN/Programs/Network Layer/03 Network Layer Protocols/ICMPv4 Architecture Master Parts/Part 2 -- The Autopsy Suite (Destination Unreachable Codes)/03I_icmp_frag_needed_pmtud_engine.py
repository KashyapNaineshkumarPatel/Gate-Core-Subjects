import sys
import re
import shutil
import time
from typing import Any, Dict, Tuple

class ICMPFragNeededEngine:
    pmtud_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.pmtud_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, router_ip: str, packet_size_str: str, next_hop_mtu_str: str, df_bit_str: str) -> Tuple[str, int, int, bool]:
        # IP Validation
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ip_pattern, router_ip)
        if not match:
            raise ValueError("Syntax Error: Router IP format invalid (e.g., 10.1.1.1).")
        for idx, octet_str in enumerate(match.groups()):
            if int(octet_str) > 255:
                raise ValueError(f"Architecture Error: Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        # Packet Size Validation
        try:
            packet_size = int(packet_size_str)
            next_hop_mtu = int(next_hop_mtu_str)
        except ValueError:
            raise ValueError("Type Error: Packet size and Next-Hop MTU must be integers.")

        if packet_size < 28 or packet_size > 65535:
            raise ValueError("Bounds Error: IPv4 Packet size must be between 28 (Min Header + Data) and 65,535 bytes.")

        if next_hop_mtu < 68 or next_hop_mtu > 9216:
            raise ValueError("Architecture Error: MTU must be between 68 (RFC 791 Min) and 9,216 (Jumbo Frame Limit).")

        # DF Flag Validation
        df_clean = df_bit_str.strip().lower()
        if df_clean in ['1', 'y', 'yes', 'true', 'set']:
            df_set = True
        elif df_clean in ['0', 'n', 'no', 'false', 'unset']:
            df_set = False
        else:
            raise ValueError("Syntax Error: DF Bit must be 1 (Set) or 0 (Unset).")

        return router_ip, packet_size, next_hop_mtu, df_set

    def simulate_fragmentation_needed(self, router_ip: str, packet_size: int, next_hop_mtu: int, df_set: bool) -> None:
        """Simulates RFC 1191 PMTUD telemetry and Type 3 Code 4 generation with Next-Hop MTU payload injection."""
        
        ip_header_len = 20
        transport_header_len = 8  # TCP/UDP header snippet
        
        # State machine analysis
        if packet_size <= next_hop_mtu:
            action = "FORWARD"
            icmp_generated = False
            details = f"Packet size ({packet_size} bytes) fits within Link MTU ({next_hop_mtu} bytes). Layer 3 forwarding cleared."
            tcp_mss_calc = next_hop_mtu - 40  # 20 bytes IP + 20 bytes TCP
            security_note = "OPTIMAL: Transmission within path limits. No control-plane friction or fragmentation overhead."
            icmp_payload = {}
        else:
            if not df_set:
                action = "FRAGMENT_IN_FLIGHT"
                icmp_generated = False
                details = f"Packet size ({packet_size} bytes) exceeds Link MTU ({next_hop_mtu} bytes), but DF=0. Router fragments payload."
                tcp_mss_calc = next_hop_mtu - 40
                security_note = (
                    "SUBOPTIMAL / HIGH OVERHEAD: Intermediate router CPU is consumed slicing packets. "
                    "Reassembly at destination increases latency and exposes connection to fragment reassembly attacks."
                )
                icmp_payload = {}
            else:
                action = "DROP_AND_EMIT_ICMP"
                icmp_generated = True
                details = f"Packet size ({packet_size} bytes) exceeds MTU ({next_hop_mtu} bytes) and DF=1. Router drops packet and fires ICMP."
                tcp_mss_calc = next_hop_mtu - 40
                
                # RFC 1191 Next-Hop MTU Field (Bytes 6-7 in ICMP Header)
                icmp_payload = {
                    "type": 3,
                    "code": 4,
                    "code_desc": "Fragmentation Needed and Don't Fragment (DF) was Set",
                    "rfc1191_next_hop_mtu": next_hop_mtu,
                    "unused_bits": "0x0000",
                    "encapsulated_ip_hdr": f"Ver: 4, IHL: 5, Len: {packet_size}, ID: 0x4A12, DF: 1, MF: 0, Proto: 6 (TCP)",
                    "encapsulated_payload": "SrcPort: 54120, DstPort: 443, SeqNum: 0x8FA120DE"
                }
                security_note = (
                    f"PMTUD CONVERGENCE: Router {router_ip} advertises Next-Hop MTU = {next_hop_mtu}. "
                    f"Sending host adjusts its TCP MSS from {packet_size - 40} to {tcp_mss_calc} bytes. "
                    "If a firewall blocks this ICMP packet downstream, the connection enters a permanent Black Hole state."
                )

        # Update State Tree
        self.pmtud_state = {
            "router_ip": router_ip,
            "packet_size": packet_size,
            "next_hop_mtu": next_hop_mtu,
            "df_set": df_set,
            "action": action,
            "icmp_generated": icmp_generated,
            "icmp_payload": icmp_payload,
            "tcp_mss": tcp_mss_calc,
            "details": details,
            "security_note": security_note
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.pmtud_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03I: ICMP FRAG NEEDED & PMTUD ENGINE (TYPE 3, CODE 4) ".center(width))
        print("=" * width)
        
        print(f" [+] Intercepting Router Gateway : {state['router_ip']}")
        print(f" [+] Ingress IPv4 Packet Size   : {state['packet_size']} bytes (DF Bit = {int(state['df_set'])})")
        print(f" [+] Egress Egress Interface MTU: {state['next_hop_mtu']} bytes")
        print("-" * width)
        
        print(" [i] LAYER 3 ROUTING ACTION & LOGIC:")
        time.sleep(0.2)
        print(f"     -> Action  : {state['action']}")
        print(f"     -> Details : {state['details']}")
        print("-" * width)
        
        if state['icmp_generated']:
            p = state['icmp_payload']
            print(" [!] ICMP TYPE 3 CODE 4 TELEMETRY PACKET (RFC 1191 SPECIFICATION):")
            time.sleep(0.2)
            print(f"     -> ICMP Type / Code  : Type {p['type']}, Code {p['code']} ({p['code_desc']})")
            print(f"     -> RFC 1191 Field    : Next-Hop MTU = {p['rfc1191_next_hop_mtu']} bytes (Bits 16-31 of ICMP Header)")
            print(f"     -> Encapsulated IP   : {p['encapsulated_ip_hdr']}")
            print(f"     -> Original L4 Data  : {p['encapsulated_payload']}")
            print("-" * width)
            
        print(f" [!] PMTUD MSS CONVERGENCE:")
        print(f"     -> Inferred Max Segment Size (TCP MSS) : {state['tcp_mss']} bytes (MTU - 40 bytes IP/TCP Headers)")
        print("-" * width)
        print(f" [!] ARCHITECTURAL & SECURITY ANALYSIS:")
        print(f"     -> {state['security_note']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPFragNeededEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03I_ICMP_FRAG_NEEDED_PMTUD_ENGINE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure Path MTU Simulation Parameters:")
            r_in    = input("    Router Interface IP (e.g., 172.16.1.1) : ").strip()
            if r_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not r_in: continue
            
            size_in = input("    Ingress Packet Size (Bytes, e.g., 1500): ").strip()
            mtu_in  = input("    Next-Hop Link MTU   (Bytes, e.g., 1400): ").strip()
            df_in   = input("    Set DF (Don't Fragment) Bit? (1/0)     : ").strip()
                
            router, p_size, mtu, df = engine.validate_inputs(r_in, size_in, mtu_in, df_in)
            engine.simulate_fragmentation_needed(router, p_size, mtu, df)
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