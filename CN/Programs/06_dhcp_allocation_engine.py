import ipaddress
import time
import sys
import random

class DHCPEngine:
    def __init__(self, network="192.168.1.0/24", gateway="192.168.1.1", lease_seconds=30):
        self.network = ipaddress.IPv4Network(network)
        self.gateway = gateway
        self.subnet_mask = str(self.network.netmask)
        self.dns = "8.8.8.8"
        self.lease_seconds = lease_seconds
        
        # Build the IP pool (excluding Network ID, Broadcast, and Gateway)
        self.available_pool = [
            str(ip) for ip in self.network.hosts() 
            if str(ip) != self.gateway
        ]
        
        # State tracking dictionaries
        self.active_leases = {}  # MAC -> {"ip": IP, "expires": timestamp}
        self.pending_offers = {} # MAC -> IP (Held temporarily during DORA)

    def _sweep_expired_leases(self):
        """Silently reclaims IPs whose lease timers have expired."""
        current_time = time.time()
        expired_macs = []
        
        for mac, data in self.active_leases.items():
            if current_time > data["expires"]:
                expired_macs.append(mac)
                
        for mac in expired_macs:
            reclaimed_ip = self.active_leases[mac]["ip"]
            self.available_pool.append(reclaimed_ip)
            del self.active_leases[mac]
            print(f"    [!] LEASE EXPIRED: Reclaimed {reclaimed_ip} from MAC {mac}")

    def execute_dora(self, client_mac):
        """Executes the strict 4-step DORA protocol."""
        print(f"\n[>] INITIATING DORA PROCESS FOR MAC: {client_mac}")
        self._sweep_expired_leases()

        # Step 1: DISCOVER
        print(f"  1. [DISCOVER] Client {client_mac} broadcasts: 'I need an IP!'")
        
        if not self.available_pool:
            print(f"  [X] DHCP SERVER FATAL ERROR: No IP addresses available! Pool exhausted.")
            return False

        # Step 2: OFFER
        offered_ip = self.available_pool.pop(0) # Pull next available IP
        self.pending_offers[client_mac] = offered_ip
        print(f"  2. [OFFER]    Server unicasts: 'I can offer you {offered_ip}'")
        time.sleep(0.5)

        # Step 3: REQUEST
        if client_mac in self.pending_offers:
            requested_ip = self.pending_offers[client_mac]
            print(f"  3. [REQUEST]  Client broadcasts: 'I accept {requested_ip}'")
        else:
            print(f"  [X] Protocol Error: Client requested IP without an offer.")
            return False
        time.sleep(0.5)

        # Step 4: ACKNOWLEDGE
        expiration_time = time.time() + self.lease_seconds
        self.active_leases[client_mac] = {
            "ip": requested_ip,
            "expires": expiration_time
        }
        del self.pending_offers[client_mac]
        
        print(f"  4. [ACK]      Server unicasts: 'Confirmed. Lease valid for {self.lease_seconds} seconds.'")
        print(f"     [+] Configuration applied -> Mask: {self.subnet_mask} | GW: {self.gateway} | DNS: {self.dns}")
        return True

    def execute_starvation_attack(self):
        """Simulates a rogue device spoofing MACs to exhaust the DHCP pool."""
        print("\n" + "="*60)
        print(" [!] WARNING: INITIATING DHCP STARVATION ATTACK")
        print("="*60)
        
        initial_pool_size = len(self.available_pool)
        print(f"[*] Target Pool Size: {initial_pool_size} available IPs.")
        print("[*] Generating spoofed MAC addresses and spamming DISCOVER packets...")
        
        time.sleep(1)
        
        attack_count = 0
        while self.available_pool:
            # Generate a random spoofed MAC address
            spoofed_mac = "02:%02x:%02x:%02x:%02x:%02x" % (
                random.randint(0, 255), random.randint(0, 255), 
                random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
            )
            
            # Attacker only goes up to the REQUEST phase to lock the IP
            stolen_ip = self.available_pool.pop(0)
            self.active_leases[spoofed_mac] = {
                "ip": stolen_ip,
                "expires": time.time() + self.lease_seconds
            }
            attack_count += 1
            
            # Print update every 50 packets to simulate speed without clogging the terminal
            if attack_count % 50 == 0:
                print(f"    -> Spoofed {attack_count} MACs... Pool dropping...")

        print("\n[+] ATTACK COMPLETE.")
        print(f"[X] Stole {attack_count} IP addresses. The DHCP pool is now completely exhausted.")
        print("[X] Legitimate users are now locked out of the network.")

    def view_status(self):
        """Displays current pool metrics and active leases."""
        self._sweep_expired_leases()
        print("\n" + "="*60)
        print(f" DHCP SERVER STATUS ")
        print("="*60)
        print(f" Total IPs in Subnet : {len(list(self.network.hosts()))}")
        print(f" IPs Available       : {len(self.available_pool)}")
        print(f" Active Leases       : {len(self.active_leases)}")
        print("-" * 60)
        
        if self.active_leases:
            print(f" {'MAC ADDRESS':<20} | {'ALLOCATED IP':<15} | {'TIME LEFT'}")
            print("-" * 60)
            current_time = time.time()
            for mac, data in list(self.active_leases.items())[:10]: # Show max 10 to avoid terminal flood
                time_left = int(data['expires'] - current_time)
                print(f" {mac:<20} | {data['ip']:<15} | {time_left}s")
            
            if len(self.active_leases) > 10:
                print(f" ... and {len(self.active_leases) - 10} more leases hidden.")
        else:
            print(" No active leases.")
        print("="*60 + "\n")


def interactive_mode():
    engine = DHCPEngine(network="192.168.1.0/24", lease_seconds=30)
    
    while True:
        print("\n--- DHCP ALLOCATION ENGINE ---")
        print("1. Simulate Standard Client Boot (DORA Process)")
        print("2. View Server Status & Active Leases")
        print("3. Wait 15 Seconds (Simulate Time Passing)")
        print("4. Execute DHCP Starvation Attack")
        print("5. Quit")
        
        choice = input("\n[?] Select Option (1-5): ").strip()
        
        if choice == "1":
            mac_input = input("  > Enter Client MAC (or press Enter for random): ").strip()
            if not mac_input:
                mac_input = "AA:BB:CC:DD:EE:%02X" % random.randint(0, 255)
            engine.execute_dora(mac_input)
            
        elif choice == "2":
            engine.view_status()
            
        elif choice == "3":
            print("\n[*] Waiting 15 seconds...")
            time.sleep(1) # Fake sleep for UX, we just manipulate the clock in reality.
            # To actually simulate time passing without waiting 15 real seconds, 
            # we subtract 15 seconds from all expiration timestamps.
            for mac in engine.active_leases:
                engine.active_leases[mac]["expires"] -= 15
            print("[+] 15 simulated seconds have passed. Leases are closer to expiring.")
            
        elif choice == "4":
            engine.execute_starvation_attack()
            
        elif choice == "5" or choice.lower() == "q":
            print("\n[+] Exiting DHCP Engine.")
            sys.exit(0)
        else:
            print("\n[!] Invalid option.")

if __name__ == "__main__":
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print("\n\n[+] Exiting DHCP Engine.")
        sys.exit(0)