import math
import ipaddress
from typing import Dict, List

class VLSMAllocator:
    def __init__(self, major_block: str):
        """
        Initializes the VLSM engine and validates the major IP block.
        """
        try:
            # strict=False allows the engine to auto-correct host IPs to true Network IDs
            self.network = ipaddress.IPv4Network(major_block, strict=False)
            self.base_ip_int = int(self.network.network_address)
            self.max_ip_int = int(self.network.broadcast_address)
            self.total_available_ips = self.network.num_addresses
        except ValueError as e:
            raise ValueError(f"[!] Invalid CIDR Block Provided: {e}")

    def _get_next_power_of_2(self, hosts: int) -> int:
        """
        Calculates the required block size.
        Adds 2 for Network & Broadcast IDs, then finds the next power of 2.
        """
        required_ips = hosts + 2
        # If required_ips is exactly a power of 2, return it. Otherwise, round up.
        power = math.ceil(math.log2(required_ips))
        return 2 ** power

    def allocate(self, subnets: Dict[str, int]) -> List[Dict[str, str]]:
        """
        Core VLSM algorithm. Sorts requirements, verifies capacity, and allocates blocks.
        """
        # EDGE CASE 1: Validate host numbers
        for name, hosts in subnets.items():
            if hosts <= 0:
                raise ValueError(f"[!] Invalid host count for '{name}': {hosts}. Must be > 0.")

        # EDGE CASE 2: Sort subnets descending (Largest to Smallest) - The Golden Rule of VLSM
        sorted_subnets = sorted(subnets.items(), key=lambda item: item[1], reverse=True)

        # EDGE CASE 3: Predict Capacity Overflow
        total_ips_needed = sum(self._get_next_power_of_2(hosts) for _, hosts in sorted_subnets)
        if total_ips_needed > self.total_available_ips:
            raise OverflowError(
                f"[!] Block Exhausted: You need {total_ips_needed} IPs, "
                f"but {self.network} only has {self.total_available_ips} IPs."
            )

        current_ip_int = self.base_ip_int
        allocations = []

        for name, hosts in sorted_subnets:
            block_size = self._get_next_power_of_2(hosts)
            cidr_mask = 32 - int(math.log2(block_size))

            # Calculate network boundaries using raw integer odometer math
            network_id_int = current_ip_int
            broadcast_id_int = current_ip_int + block_size - 1
            
            # Convert back to readable IPv4 strings
            net_id_str = str(ipaddress.IPv4Address(network_id_int))
            broadcast_str = str(ipaddress.IPv4Address(broadcast_id_int))
            first_host = str(ipaddress.IPv4Address(network_id_int + 1))
            last_host = str(ipaddress.IPv4Address(broadcast_id_int - 1))
            subnet_mask = str(ipaddress.IPv4Network(f"0.0.0.0/{cidr_mask}").netmask)

            allocations.append({
                "Name": name,
                "Requested Hosts": hosts,
                "Allocated Block Size": block_size,
                "CIDR": f"{net_id_str}/{cidr_mask}",
                "Network ID": net_id_str,
                "Broadcast ID": broadcast_str,
                "Usable Range": f"{first_host} - {last_host}",
                "Subnet Mask": subnet_mask
            })

            # Move the odometer forward for the next subnet
            current_ip_int += block_size

        return allocations

    def print_allocations(self, allocations: List[Dict[str, str]]):
        """Formats the output into a clean, readable terminal table."""
        print(f"\n{'='*80}")
        print(f"VLSM ALLOCATION PLAN FOR: {self.network}")
        print(f"{'='*80}")
        for alloc in allocations:
            print(f"Network: {alloc['Name']} (Req: {alloc['Requested Hosts']} hosts | Allocated: {alloc['Allocated Block Size']} IPs)")
            print(f"  --> CIDR Notation : {alloc['CIDR']}")
            print(f"  --> Network ID    : {alloc['Network ID']}")
            print(f"  --> Broadcast ID  : {alloc['Broadcast ID']}")
            print(f"  --> Usable Range  : {alloc['Usable Range']}")
            print(f"  --> Subnet Mask   : {alloc['Subnet Mask']}\n")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    # GATE-Level Test Scenario
    major_block = "192.168.50.0/24"
    
    # Notice they are out of order. The engine will fix this automatically.
    requested_subnets = {
        "Admin (LAN 3)": 20,
        "Dev (LAN 2)": 50,
        "Security (LAN 1)": 120,
        "WAN Router Link": 2
    }

    try:
        # Initialize engine and run allocation
        engine = VLSMAllocator(major_block)
        results = engine.allocate(requested_subnets)
        engine.print_allocations(results)
    
    except Exception as error:
        print(error)