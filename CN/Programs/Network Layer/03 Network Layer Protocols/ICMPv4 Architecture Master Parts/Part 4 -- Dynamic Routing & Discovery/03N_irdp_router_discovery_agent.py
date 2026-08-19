import sys
import re
import shutil
import time
from typing import Any, Dict, List, Tuple

class IRDPRouterDiscoveryEngine:
    irdp_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.irdp_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, host_ip: str, r1_ip: str, r1_pref: str, r2_ip: str, r2_pref: str, lifetime_str: str) -> Tuple[str, str, int, str, int, int]:
        # IP Validation Pattern
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        
        nodes = [
            (host_ip, "Host IP"),
            (r1_ip, "Router 1 IP"),
            (r2_ip, "Router 2 IP")
        ]
        
        for ip, label in nodes:
            match = re.match(ip_pattern, ip)
            if not match:
                raise ValueError(f"Syntax Error: {label} format invalid (e.g., 192.168.1.1).")
            for idx, octet_str in enumerate(match.groups()):
                if int(octet_str) > 255:
                    raise ValueError(f"Architecture Error: {label} Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        # Subnet Check
        host_sub = ".".join(host_ip.split('.')[:3])
        r1_sub = ".".join(r1_ip.split('.')[:3])
        r2_sub = ".".join(r2_ip.split('.')[:3])
        if not (host_sub == r1_sub == r2_sub):
            raise ValueError("RFC 1256 Error: Host and both Routers must reside on the same broadcast subnet (/24).")

        if r1_ip == r2_ip:
            raise ValueError("Logical Error: Router 1 and Router 2 must have distinct IP addresses.")

        # Preference Level Validation (32-bit signed integer in RFC 1256)
        try:
            pref1 = int(r1_pref)
            pref2 = int(r2_pref)
            lifetime = int(lifetime_str)
        except ValueError:
            raise ValueError("Type Error: Preference levels and Lifetime must be integers.")

        if pref1 < -2147483648 or pref1 > 2147483647 or pref2 < -2147483648 or pref2 > 2147483647:
            raise ValueError("Architecture Error: Preference level is a 32-bit signed integer.")

        if lifetime < 4 or lifetime > 9000:
            raise ValueError("Bounds Error: Router Advertisement lifetime must be between 4 and 9000 seconds (RFC 1256).")

        return host_ip, r1_ip, pref1, r2_ip, pref2, lifetime

    def simulate_irdp(self, host_ip: str, r1_ip: str, pref1: int, r2_ip: str, pref2: int, lifetime: int) -> None:
        """Simulates RFC 1256 Router Solicitation (Type 10) and Router Advertisement (Type 9)."""
        
        events: List[Dict[str, str]] = []
        
        # 1. Host Boots & Emits Router Solicitation (ICMP Type 10)
        events.append({
            "phase": "1. SOLICITATION (TYPE 10)",
            "source": f"Host ({host_ip})",
            "destination": "224.0.0.2 (All-Routers Multicast) / 255.255.255.255",
            "details": "ICMP Type 10 (Router Solicitation). Host querying for available default gateways on LAN."
        })
        
        # 2. Router 1 Advertises (ICMP Type 9)
        events.append({
            "phase": "2. ADVERTISEMENT R1 (TYPE 9)",
            "source": f"Router 1 ({r1_ip})",
            "destination": "224.0.0.1 (All-Hosts Multicast)",
            "details": f"ICMP Type 9 (Router Advertisement). Entries: 1 | Addr: {r1_ip} | Pref: {pref1} | Lifetime: {lifetime}s"
        })
        
        # 3. Router 2 Advertises (ICMP Type 9)
        events.append({
            "phase": "3. ADVERTISEMENT R2 (TYPE 9)",
            "source": f"Router 2 ({r2_ip})",
            "destination": "224.0.0.1 (All-Hosts Multicast)",
            "details": f"ICMP Type 9 (Router Advertisement). Entries: 1 | Addr: {r2_ip} | Pref: {pref2} | Lifetime: {lifetime}s"
        })

        # 4. Host Gateway Selection Logic (Highest Preference Wins)
        if pref1 > pref2:
            selected_gw = r1_ip
            selected_pref = pref1
            fallback_gw = r2_ip
            fallback_pref = pref2
        elif pref2 > pref1:
            selected_gw = r2_ip
            selected_pref = pref2
            fallback_gw = r1_ip
            fallback_pref = pref1
        else:
            selected_gw = r1_ip  # Tie-breaker: first response
            selected_pref = pref1
            fallback_gw = r2_ip
            fallback_pref = pref2

        events.append({
            "phase": "4. GATEWAY CONVERGENCE",
            "source": f"Host ({host_ip})",
            "destination": "Local FIB / Routing Table",
            "details": f"Selected Default Gateway: {selected_gw} (Highest Preference: {selected_pref}). Fallback: {fallback_gw} (Pref: {fallback_pref})."
        })

        # Security & Architectural Insight
        insight = (
            f"RFC 1256 DISCOVERY MECHANICS: Before DHCP became ubiquitous, IRDP provided zero-configuration default routing. "
            f"The host dynamically selected {selected_gw} based on the highest 32-bit signed preference level. "
            f"SECURITY EXPOSURE: IRDP is completely unauthenticated. An attacker on the local network can inject an ICMP Type 9 "
            f"advertisement with Maximum Preference (2,147,483,647) to instantly hijack default gateway routing across the entire subnet."
        )

        # Update State Tree
        self.irdp_state = {
            "host_ip": host_ip,
            "r1": {"ip": r1_ip, "pref": pref1},
            "r2": {"ip": r2_ip, "pref": pref2},
            "lifetime": lifetime,
            "selected_gw": selected_gw,
            "events": events,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.irdp_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03N: IRDP ROUTER DISCOVERY AGENT (RFC 1256) ".center(width))
        print("=" * width)
        
        print(f" [+] Host Endpoint      : {state['host_ip']}")
        print(f" [+] Router 1 Candidate  : {state['r1']['ip']} (Preference Level: {state['r1']['pref']})")
        print(f" [+] Router 2 Candidate  : {state['r2']['ip']} (Preference Level: {state['r2']['pref']})")
        print(f" [+] Advertised Lifetime : {state['lifetime']} seconds")
        print("-" * width)
        
        print(" [i] CONTROL PLANE IRDP PROTOCOL EXCHANGE:")
        for ev in state['events']:
            time.sleep(0.15)
            print(f"\n     [{ev['phase']}]")
            print(f"     -> Transmit : {ev['source']} -> {ev['destination']}")
            print(f"     -> Payload  : {ev['details']}")
            
        print("-" * width)
        print(" [!] RFC 1256 PACKET SPECIFICATION BREAKDOWN:")
        print("     -> Router Solicitation : ICMP Type 10 | Code 0 | Reserved: 32-bit Zero")
        print("     -> Router Advertisement: ICMP Type 9  | Code 0 | Addr Num: 1 | Addr Entry Size: 2 words (8 bytes)")
        print(f"     -> Active Gateway Set  : {state['selected_gw']}")
        print("-" * width)
        
        print(f" [!] ARCHITECTURAL & VULNERABILITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = IRDPRouterDiscoveryEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03N_IRDP_ROUTER_DISCOVERY_AGENT INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure RFC 1256 IRDP Discovery Topology:")
            host_in   = input("    Host IP                   (e.g., 10.0.0.50)  : ").strip()
            if host_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not host_in: continue
            
            r1_ip_in  = input("    Router 1 IP               (e.g., 10.0.0.1)   : ").strip()
            r1_prf_in = input("    Router 1 Preference Level (e.g., 100)        : ").strip()
            r2_ip_in  = input("    Router 2 IP               (e.g., 10.0.0.2)   : ").strip()
            r2_prf_in = input("    Router 2 Preference Level (e.g., 500)        : ").strip()
            life_in   = input("    Advertisement Lifetime    (e.g., 1800 sec)   : ").strip()
                
            h_ip, r1, p1, r2, p2, l_time = engine.validate_inputs(host_in, r1_ip_in, r1_prf_in, r2_ip_in, r2_prf_in, life_in)
            engine.simulate_irdp(h_ip, r1, p1, r2, p2, l_time)
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