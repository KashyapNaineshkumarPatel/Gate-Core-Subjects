import ipaddress
import sys

class RouteAggregator:
    def __init__(self):
        self.subnets = []

    def add_subnet(self, cidr_input: str):
        """Validates and adds a subnet to the aggregation pool."""
        try:
            # strict=False auto-corrects host IPs to Network IDs
            network = ipaddress.IPv4Network(cidr_input.strip(), strict=False)
            self.subnets.append(network)
            print(f"  [+] Added: {network}")
        except ValueError as e:
            print(f"  [!] ERROR: '{cidr_input}' is invalid. {e}")

    def execute_aggregation(self):
        """Attempts to fuse the subnets based on contiguity and alignment."""
        if not self.subnets:
            print("\n[!] No subnets provided. Aborting aggregation.")
            return

        print(f"\n{'-'*65}")
        print("⚙️ EXECUTING ROUTE AGGREGATION (SUPERNETTING)")
        print(f"{'-'*65}")
        print(f"Analyzing {len(self.subnets)} subnets...")

        # ipaddress.collapse_addresses automatically enforces Contiguity and Alignment rules
        try:
            collapsed = list(ipaddress.collapse_addresses(self.subnets))
            
            if len(collapsed) == 1:
                print("\n[+] AGGREGATION SUCCESSFUL (Perfect Alignment & Contiguity)")
                print(f"  > Supernet Route : {collapsed[0]}")
                print(f"  > Network ID     : {collapsed[0].network_address}")
                print(f"  > Broadcast ID   : {collapsed[0].broadcast_address}")
                print(f"  > New Subnet Mask: {collapsed[0].netmask}")
            else:
                print("\n[!] AGGREGATION FAILED TO FORM A SINGLE SUPERNET")
                print("  > Reason: The subnets are either not contiguous (there are gaps) ")
                print("            or they fail the alignment divisibility rule.")
                print("\n  > Maximum possible optimization yielded these blocks:")
                for net in collapsed:
                    print(f"    - {net}")
                    
        except Exception as e:
            print(f"[!] An unexpected mathematical error occurred: {e}")
            
        print(f"{'-'*65}\n")


def interactive_mode():
    """Handles CLI input and sanitizes user errors."""
    print("="*65)
    print(" ROUTE AGGREGATOR ENGINE ".center(65, "="))
    print("="*65)
    
    while True:
        aggregator = RouteAggregator()
        print("\n[?] Enter CIDR networks one by one (e.g., 192.168.1.0/24).")
        print("[?] Type 'done' to calculate, or 'q' to quit.")
        
        while True:
            try:
                user_input = input("  > Subnet: ").strip().lower()
                
                if user_input == 'q':
                    print("\n[+] Exiting engine.")
                    sys.exit(0)
                elif user_input == 'done':
                    break
                elif not user_input:
                    continue
                else:
                    aggregator.add_subnet(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n[+] Exiting engine.")
                sys.exit(0)
                
        # Run the engine on the collected subnets
        aggregator.execute_aggregation()


if __name__ == "__main__":
    interactive_mode()