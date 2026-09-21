import sys
import re
import shutil
import time
from typing import Any, Dict, Tuple

class ICMPRedirectRoutingEngine:
    redirect_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.redirect_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, host_ip: str, cur_gw: str, opt_gw: str, dest_ip: str, redirect_code: str) -> Tuple[str, str, str, str, int]:
        # IP Validation Pattern
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        
        nodes = [
            (host_ip, "Host IP"),
            (cur_gw, "Current Gateway (R1)"),
            (opt_gw, "Optimal Gateway (R2)"),
            (dest_ip, "Destination IP")
        ]
        
        for ip, label in nodes:
            match = re.match(ip_pattern, ip)
            if not match:
                raise ValueError(f"Syntax Error: {label} format invalid (e.g., 192.168.1.1).")
            for idx, octet_str in enumerate(match.groups()):
                if int(octet_str) > 255:
                    raise ValueError(f"Architecture Error: {label} Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        # RFC 792 Validation: Redirect requires Host, Current GW, and Optimal GW on the SAME subnet
        host_subnet = ".".join(host_ip.split('.')[:3])
        cur_subnet = ".".join(cur_gw.split('.')[:3])
        opt_subnet = ".".join(opt_gw.split('.')[:3])
        
        if not (host_subnet == cur_subnet == opt_subnet):
            raise ValueError(
                "RFC 792/1812 Rule Violation: ICMP Redirects are ONLY valid when Host, "
                "Current Router (R1), and Optimal Router (R2) reside on the exact same Layer 2 / Layer 3 subnet (/24)."
            )

        if cur_gw == opt_gw:
            raise ValueError("Logical Error: Current Gateway and Optimal Gateway cannot be identical.")

        # Code Mapping
        valid_codes = {'0': 0, '1': 1, '2': 2, '3': 3}
        if redirect_code not in valid_codes:
            raise ValueError("Syntax Error: Code must be 0 (Net), 1 (Host), 2 (ToS/Net), or 3 (ToS/Host).")

        return host_ip, cur_gw, opt_gw, dest_ip, valid_codes[redirect_code]

    def simulate_redirect(self, host_ip: str, cur_gw: str, opt_gw: str, dest_ip: str, code: int) -> None:
        """Simulates RFC 792/1812 ICMP Type 5 generation, gateway redirection, and local routing table update."""
        
        icmp_type = 5  # Redirect
        code_descriptions = {
            0: "Redirect Datagram for the Network",
            1: "Redirect Datagram for the Host",
            2: "Redirect Datagram for the Type of Service and Network",
            3: "Redirect Datagram for the Type of Service and Host"
        }
        
        events = []
        
        # Step 1: Host transmits packet to default gateway
        events.append({
            "step": "1. INGRESS FORWARDING",
            "actor": f"Host ({host_ip})",
            "action": f"Transmits packet destined for {dest_ip} to Default Gateway R1 ({cur_gw})."
        })
        
        # Step 2: Router R1 realizes the next hop is on the SAME interface it arrived on
        events.append({
            "step": "2. ROUTE DETERMINATION",
            "actor": f"Current Gateway R1 ({cur_gw})",
            "action": f"Consults FIB. Next-hop for {dest_ip} is R2 ({opt_gw}). Egress interface matches Ingress interface."
        })
        
        # Step 3: Router R1 forwards packet to R2 and generates ICMP Redirect to Host
        events.append({
            "step": "3. PACKET FORWARD & ICMP EMISSION",
            "actor": f"Current Gateway R1 ({cur_gw})",
            "action": f"Forwards original packet to R2 ({opt_gw}) AND sends ICMP Type 5 Code {code} back to Host ({host_ip})."
        })
        
        # Step 4: Host updates its dynamic routing table
        events.append({
            "step": "4. HOST ROUTING TABLE UPDATE",
            "actor": f"Host ({host_ip})",
            "action": f"Installs dynamic host route: '{dest_ip} via {opt_gw}' (Bypassing R1 for future packets)."
        })

        # Encapsulated Original IP Header
        encapsulated_hdr = f"Ver: 4, IHL: 5, Len: 84, ID: 0x33A1, Proto: 1 (ICMP/UDP/TCP), Src: {host_ip} -> Dst: {dest_ip}"

        # Architectural & Security Insight
        insight = (
            f"DYNAMIC ROUTING OPTIMIZATION: Router {cur_gw} detected inefficient hair-pinning (two-hop traversal on same subnet). "
            f"By sending ICMP Type 5 (Gateway Address = {opt_gw}), future packets go directly from {host_ip} to {opt_gw}. "
            "SECURITY HAZARD: Modern OSs disable ICMP redirects by default (e.g., `net.ipv4.conf.all.accept_redirects=0`) "
            "because an attacker on the same LAN can forge Type 5 packets to redirect all host traffic through a rogue machine (MitM)."
        )

        # Update State Tree
        self.redirect_state = {
            "host_ip": host_ip,
            "cur_gw": cur_gw,
            "opt_gw": opt_gw,
            "dest_ip": dest_ip,
            "type": icmp_type,
            "code": code,
            "code_desc": code_descriptions[code],
            "events": events,
            "encapsulated": encapsulated_hdr,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.redirect_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03M: ICMP REDIRECT ROUTING ENGINE (TYPE 5) ".center(width))
        print("=" * width)
        
        print(f" [+] Originating Host Node : {state['host_ip']}")
        print(f" [+] Current Gateway (R1)  : {state['cur_gw']}")
        print(f" [+] Optimal Gateway (R2)  : {state['opt_gw']} (Advertised Next-Hop)")
        print(f" [+] Destination Target    : {state['dest_ip']}")
        print("-" * width)
        
        print(" [i] CONTROL PLANE REDIRECT CONVERGENCE LOG:")
        for ev in state['events']:
            time.sleep(0.15)
            print(f"\n     {ev['step']}")
            print(f"     -> Entity : {ev['actor']}")
            print(f"     -> Action : {ev['action']}")
            
        print("-" * width)
        print(" [!] ICMP TYPE 5 PACKET SPECIFICATION (RFC 792):")
        print(f"     -> Type / Code         : Type {state['type']} | Code {state['code']} ({state['code_desc']})")
        print(f"     -> Gateway IP (Bytes 4-7): {state['opt_gw']} (Address of the Better Router)")
        print(f"     -> Encapsulated Header : {state['encapsulated']}")
        print("-" * width)
        
        print(f" [!] ARCHITECTURAL & SECURITY ANALYSIS:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPRedirectRoutingEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03M_ICMP_REDIRECT_ROUTING_ENGINE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure ICMP Redirect Topology (Same /24 Subnet):")
            host_in = input("    Host IP               (e.g., 192.168.1.50) : ").strip()
            if host_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not host_in: continue
            
            cur_in  = input("    Current Gateway R1    (e.g., 192.168.1.1)  : ").strip()
            opt_in  = input("    Optimal Gateway R2    (e.g., 192.168.1.2)  : ").strip()
            dest_in = input("    Remote Destination IP (e.g., 8.8.8.8)      : ").strip()
            
            print("    Select ICMP Redirect Code:")
            print("      0: Redirect for Network")
            print("      1: Redirect for Host")
            print("      2: Redirect for Type of Service & Network")
            print("      3: Redirect for Type of Service & Host")
            code_in = input("    Selection (0/1/2/3)                        : ").strip()
                
            host, cur_gw, opt_gw, dest, code = engine.validate_inputs(host_in, cur_in, opt_in, dest_in, code_in)
            engine.simulate_redirect(host, cur_gw, opt_gw, dest, code)
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