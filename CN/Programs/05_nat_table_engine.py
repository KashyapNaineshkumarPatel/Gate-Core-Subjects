import ipaddress
import sys
import random

class NATTranslationEngine:
    def __init__(self, public_ip: str = "203.0.113.1"):
        try:
            self.public_ip = str(ipaddress.IPv4Address(public_ip))
        except ValueError:
            raise ValueError(f"[!] Invalid Public IP: {public_ip}")
            
        # NAT Table stores mapping:
        # Key: (private_ip, private_port, protocol)
        # Value: public_port (allocated on self.public_ip)
        self.translation_table = {}
        
        # Track active public ports to avoid collisions
        self.used_public_ports = set()

    def process_outbound(self, src_ip: str, src_port: int, dest_ip: str, dest_port: int, protocol: str = "TCP"):
        """Simulates internal packet reaching the router's LAN interface and exiting WAN."""
        protocol = protocol.upper()
        if protocol not in ["TCP", "UDP", "ICMP"]:
            raise ValueError("[!] Unsupported protocol. Use TCP, UDP, or ICMP.")

        # Validate IPs
        src_ip_obj = ipaddress.IPv4Address(src_ip)
        dest_ip_obj = ipaddress.IPv4Address(dest_ip)

        # Validate Ports / Identifiers
        if not (1 <= src_port <= 65535) or not (1 <= dest_port <= 65535):
            raise ValueError("[!] Ports / ICMP Identifiers must be between 1 and 65535.")

        session_key = (str(src_ip_obj), src_port, protocol)

        # Check if entry already exists in NAT Table
        if session_key in self.translation_table:
            allocated_pub_port = self.translation_table[session_key]["public_port"]
        else:
            # Handle Port Collisions: Attempt to reuse src_port, or pick next available
            allocated_pub_port = src_port
            while allocated_pub_port in self.used_public_ports or allocated_pub_port > 65535:
                allocated_pub_port = random.randint(1024, 65535)

            # Record in translation table
            self.translation_table[session_key] = {
                "private_ip": str(src_ip_obj),
                "private_port": src_port,
                "public_ip": self.public_ip,
                "public_port": allocated_pub_port,
                "dest_ip": str(dest_ip_obj),
                "dest_port": dest_port,
                "protocol": protocol
            }
            self.used_public_ports.add(allocated_pub_port)

        print(f"\n[+] OUTBOUND PACKET TRANSLATED ({protocol}):")
        print(f"    ORIGINAL HEADER : {src_ip_obj}:{src_port} ---> {dest_ip_obj}:{dest_port}")
        print(f"    TRANSLATED HEADER: {self.public_ip}:{allocated_pub_port} ---> {dest_ip_obj}:{dest_port}")
        if allocated_pub_port != src_port:
            print(f"    [!] PORT COLLISION RESOLVED: Remapped private port {src_port} to WAN port {allocated_pub_port}")

    def process_inbound(self, src_ip: str, src_port: int, dest_port: int, protocol: str = "TCP"):
        """Simulates external reply hitting the router's WAN interface."""
        protocol = protocol.upper()
        
        # Look up matching translation entry
        matched_entry = None
        for key, entry in self.translation_table.items():
            if (entry["public_port"] == dest_port and 
                entry["dest_ip"] == src_ip and 
                entry["protocol"] == protocol):
                matched_entry = entry
                break

        print(f"\n[<] INBOUND PACKET RECEIVED ({protocol}):")
        print(f"    INCOMING HEADER : {src_ip}:{src_port} ---> {self.public_ip}:{dest_port}")

        if matched_entry:
            priv_ip = matched_entry["private_ip"]
            priv_port = matched_entry["private_port"]
            print(f"    MATCH FOUND IN NAT TABLE!")
            print(f"    FORWARDING TO LAN: {src_ip}:{src_port} ---> {priv_ip}:{priv_port}")
        else:
            print(f"    [!] SECURITY DROP: No active NAT entry for public port {dest_port}. Packet dropped by stateful filter.")

    def display_table(self):
        """Displays formatted NAT Translation Table."""
        print(f"\n{'='*75}")
        print(f" ACTIVE NAT / PAT TRANSLATION TABLE (WAN IP: {self.public_ip}) ".center(75, "="))
        print(f"{'='*75}")
        if not self.translation_table:
            print("  [Table is currently empty]")
            print(f"{'='*75}\n")
            return

        print(f" {'PROTO':<6} | {'INSIDE LOCAL (Private)':<22} | {'INSIDE GLOBAL (Public)':<22} | {'OUTSIDE DEST':<18}")
        print("-" * 75)
        for entry in self.translation_table.values():
            proto = entry["protocol"]
            inside_local = f"{entry['private_ip']}:{entry['private_port']}"
            inside_global = f"{entry['public_ip']}:{entry['public_port']}"
            outside_dest = f"{entry['dest_ip']}:{entry['dest_port']}"
            
            print(f" {proto:<6} | {inside_local:<22} | {inside_global:<22} | {outside_dest:<18}")
        print(f"{'='*75}\n")


def interactive_mode():
    engine = NATTranslationEngine(public_ip="203.0.113.1")
    
    while True:
        print("\n--- NAT / PAT ENGINE MENU ---")
        print("1. Simulate Outbound Request (LAN -> WAN)")
        print("2. Simulate Inbound Response (WAN -> LAN)")
        print("3. View Live NAT Table")
        print("4. Clear NAT Table")
        print("5. Quit")
        
        try:
            choice = input("\n[?] Select Option (1-5): ").strip()
            
            if choice == "1":
                src_ip = input("  > Internal Private Source IP [e.g., 192.168.1.10]: ").strip()
                src_port = int(input("  > Internal Source Port / ICMP ID [e.g., 5000]: ").strip())
                dest_ip = input("  > External Destination IP [e.g., 8.8.8.8]    : ").strip()
                dest_port = int(input("  > External Destination Port [e.g., 80]        : ").strip())
                proto = input("  > Protocol (TCP/UDP/ICMP) [Default: TCP]      : ").strip() or "TCP"
                
                engine.process_outbound(src_ip, src_port, dest_ip, dest_port, proto)

            elif choice == "2":
                src_ip = input("  > External Sender IP [e.g., 8.8.8.8]         : ").strip()
                src_port = int(input("  > External Sender Port [e.g., 80]             : ").strip())
                dest_port = int(input("  > Destination Public Port on Router           : ").strip())
                proto = input("  > Protocol (TCP/UDP/ICMP) [Default: TCP]      : ").strip() or "TCP"
                
                engine.process_inbound(src_ip, src_port, dest_port, proto)

            elif choice == "3":
                engine.display_table()

            elif choice == "4":
                engine.translation_table.clear()
                engine.used_public_ports.clear()
                print("\n[+] NAT Table flushed successfully.")

            elif choice == "5" or choice.lower() == "q":
                print("\n[+] Exiting NAT Engine.")
                sys.exit(0)

        except ValueError as e:
            if "invalid literal" in str(e):
                print("\n[!] ERROR: Port numbers must be valid integers!")
            else:
                print(f"\n{e}")
        except KeyboardInterrupt:
            print("\n\n[+] Exiting NAT Engine.")
            sys.exit(0)

if __name__ == "__main__":
    interactive_mode()