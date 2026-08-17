import sys
import re
import shutil
import time
from typing import Any, Dict, Tuple

class ICMPSmurfAmplificationEngine:
    smurf_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.smurf_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 105)

    def validate_inputs(self, victim_ip: str, broadcast_ip: str, cidr_str: str, packet_rate_str: str, payload_size_str: str) -> Tuple[str, str, int, int, int]:
        # IP Validation Pattern
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        
        for ip, label in [(victim_ip, "Victim Target IP"), (broadcast_ip, "Amplifier Broadcast IP")]:
            match = re.match(ip_pattern, ip)
            if not match:
                raise ValueError(f"Syntax Error: {label} format invalid (e.g., 192.168.1.255).")
            for idx, octet_str in enumerate(match.groups()):
                if int(octet_str) > 255:
                    raise ValueError(f"Architecture Error: {label} Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")

        if victim_ip == broadcast_ip:
            raise ValueError("Logical Error: Victim IP and Directed Broadcast IP cannot be identical.")

        # CIDR Subnet Validation
        try:
            cidr = int(cidr_str)
            rate = int(packet_rate_str)
            size = int(payload_size_str)
        except ValueError:
            raise ValueError("Type Error: CIDR prefix, packet rate, and payload size must be integers.")

        if cidr < 16 or cidr > 30:
            raise ValueError("Bounds Error: CIDR prefix must be between /16 and /30 to simulate a realistic broadcast domain.")

        if rate < 1 or rate > 1000000:
            raise ValueError("Bounds Error: Ingress packet rate must be between 1 and 1,000,000 packets/sec.")

        # ICMP Payload Limits (Physical Frame Constraints)
        if size < 0 or size > 1472:
            raise ValueError("Architecture Error: ICMP Payload size must be between 0 and 1,472 bytes (MTU 1500 - 20 IP - 8 ICMP).")

        return victim_ip, broadcast_ip, cidr, rate, size

    def simulate_smurf_attack(self, victim_ip: str, broadcast_ip: str, cidr: int, ingress_rate: int, payload_size: int) -> None:
        """Calculates mathematical amplification multiplier and volumetric bandwidth saturation."""
        
        # 1. Calculate the number of alive reflector hosts in the broadcast domain
        # Total IPs in subnet = 2^(32 - CIDR)
        # Usable hosts = Total IPs - 2 (Network ID and Directed Broadcast)
        total_ips = 2 ** (32 - cidr)
        active_reflectors = max(1, total_ips - 2)
        
        # 2. Layer 3 / Layer 2 Overhead Mathematics
        ip_header_bytes = 20
        icmp_header_bytes = 8
        ethernet_frame_overhead = 14 + 4  # 14-byte Eth header + 4-byte FCS (ignoring preamble/IPG for L3 data)
        
        total_icmp_packet_size = ip_header_bytes + icmp_header_bytes + payload_size
        wire_frame_size = total_icmp_packet_size + ethernet_frame_overhead
        
        # 3. Ingress Traffic from Attacker (Spoofed Source = Victim IP)
        attacker_pps = ingress_rate
        attacker_bandwidth_bps = attacker_pps * wire_frame_size * 8
        attacker_bandwidth_mbps = attacker_bandwidth_bps / 1_000_000
        
        # 4. Reflected Egress Traffic Converging on Victim
        # Every host in the broadcast subnet receives the Echo Request and replies with Echo Reply (Type 0)
        reflected_pps = attacker_pps * active_reflectors
        reflected_bandwidth_bps = reflected_pps * wire_frame_size * 8
        reflected_bandwidth_mbps = reflected_bandwidth_bps / 1_000_000
        reflected_bandwidth_gbps = reflected_bandwidth_mbps / 1_000
        
        # Amplification Multiplier Factor
        amplification_factor = active_reflectors

        # Security & Architectural Insight Generation
        insight = (
            f"VOLUMETRIC DDOS PHYSICS (RFC 2644 DIRECTED BROADCAST): "
            f"The attacker transmits a stream of ICMP Type 8 Echo Requests with a SPOOFED Source IP ({victim_ip}) "
            f"directly to the subnet's Directed Broadcast address ({broadcast_ip}). "
            f"The border router translates this Layer 3 broadcast into a Layer 2 frame (FF:FF:FF:FF:FF:FF). "
            f"All {active_reflectors} physical hosts in the /{cidr} subnet receive the frame and simultaneously emit "
            f"ICMP Type 0 Echo Replies directly to the victim. "
            f"Result: {attacker_bandwidth_mbps:.2f} Mbps of attacker traffic multiplies by {amplification_factor}x "
            f"into {reflected_bandwidth_mbps:.2f} Mbps ({reflected_bandwidth_gbps:.3f} Gbps), crushing the victim's link."
        )

        # Update State Tree
        self.smurf_state = {
            "victim_ip": victim_ip,
            "broadcast_ip": broadcast_ip,
            "cidr": cidr,
            "reflectors": active_reflectors,
            "packet_size": total_icmp_packet_size,
            "wire_size": wire_frame_size,
            "attacker_pps": attacker_pps,
            "attacker_mbps": attacker_bandwidth_mbps,
            "reflected_pps": reflected_pps,
            "reflected_mbps": reflected_bandwidth_mbps,
            "reflected_gbps": reflected_bandwidth_gbps,
            "multiplier": amplification_factor,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.smurf_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 03P: ICMP SMURF AMPLIFICATION PHYSICS ".center(width))
        print("=" * width)
        
        print(f" [+] Spoofed Source / Victim IP : {state['victim_ip']}")
        print(f" [+] Target Directed Broadcast : {state['broadcast_ip']} (/{state['cidr']} Subnet)")
        print(f" [+] Amplifying Host Nodes     : {state['reflectors']:,} active reflectors on LAN")
        print(f" [+] Packet Dimensions         : {state['packet_size']} bytes IP ({state['wire_size']} bytes L2 Wire)")
        print("-" * width)
        
        print(" [i] CONTROL PLANE TRAFFIC TRANSFORMATION:")
        time.sleep(0.2)
        print(f"     -> [INGRESS] Attacker Stream   : {state['attacker_pps']:,} pps | {state['attacker_mbps']:.2f} Mbps")
        time.sleep(0.3)
        print(f"     -> [REFLECT] Amplification     : {state['multiplier']}x Factor (1 Request -> {state['reflectors']} Replies)")
        time.sleep(0.2)
        print(f"     <- [EGRESS]  Converging Attack : {state['reflected_pps']:,} pps | {state['reflected_mbps']:.2f} Mbps ({state['reflected_gbps']:.3f} Gbps)")
        print("-" * width)
        
        print(" [!] MATHEMATICAL EXPLOITATION PROFILE:")
        print(f"     {'METRIC':<28} | {'ATTACKER INGRESS':<22} | {'VICTIM RECEIVED BURDEN'}")
        print("     " + "-" * 75)
        print(f"     {'Packet Generation Rate':<28} | {str(state['attacker_pps']) + ' pps':<22} | {str(state['reflected_pps']) + ' pps'}")
        print(f"     {'Bandwidth Consumption':<28} | {f'{state['attacker_mbps']:.2f} Mbps':<22} | {f'{state['reflected_mbps']:.2f} Mbps ({state['reflected_gbps']:.3f} Gbps)'}")
        print("-" * width)
        
        print(f" [!] ARCHITECTURAL DEFENSE & MITIGATION:")
        print(f"     -> {state['insight']}")
        print("     -> HARDWARE DEFENSE: Disable directed broadcasts on all routers: `no ip directed-broadcast` (RFC 2644).")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = ICMPSmurfAmplificationEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 03P_ICMP_SMURF_AMPLIFICATION_PHYSICS INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure Smurf Amplification Vector Parameters:")
            vic_in  = input("    Victim Target IP (Spoofed Source) (e.g., 192.168.10.50) : ").strip()
            if vic_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not vic_in: continue
            
            bcast_in = input("    Directed Broadcast IP            (e.g., 10.100.0.255)   : ").strip()
            cidr_in  = input("    Amplifier Subnet Prefix (CIDR)   (e.g., 24 for /24)     : ").strip()
            rate_in  = input("    Attacker Ingress Packet Rate     (e.g., 5000 pps)       : ").strip()
            size_in  = input("    ICMP Payload Size in Bytes       (e.g., 1400 bytes)     : ").strip()
                
            vic, bcast, cidr, rate, size = engine.validate_inputs(vic_in, bcast_in, cidr_in, rate_in, size_in)
            engine.simulate_smurf_attack(vic, bcast, cidr, rate, size)
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