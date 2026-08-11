import ipaddress

def execute_subnet_breakdown(target_ip: str):
    # UPGRADE 3: Sanitize input to prevent whitespace crashes
    target_ip = target_ip.strip()
    print(f"\n[+] TARGET LOCKED: {target_ip}")
    print("-" * 50)
    
    try:
        # Parse the input
        interface = ipaddress.IPv4Interface(target_ip)
        network = interface.network
        ip_obj = interface.ip
        
        cidr = network.prefixlen
        mask = str(network.netmask)
        
        # Step 1: Host Bits & Total IPs
        host_bits = 32 - cidr
        total_ips = 2 ** host_bits
        
        # UPGRADE 2: Network Classification (Class & Private/Public)
        first_octet = int(str(ip_obj).split('.')[0])
        if first_octet <= 127: ip_class = "A"
        elif first_octet <= 191: ip_class = "B"
        elif first_octet <= 223: ip_class = "C"
        elif first_octet <= 239: ip_class = "D (Multicast)"
        else: ip_class = "E (Experimental)"
        
        ip_type = "Private (RFC 1918)" if ip_obj.is_private else "Loopback" if ip_obj.is_loopback else "Public"

        print("STEP 1: IP METADATA & BITS")
        print(f"  > IP Class      : Class {ip_class}")
        print(f"  > IP Type       : {ip_type}")
        print(f"  > CIDR Mask     : /{cidr}")
        print(f"  > Network Bits  : {cidr}")
        print(f"  > Host Bits     : 32 - {cidr} = {host_bits}")
        print(f"  > Subnet Mask   : {mask}")
        print(f"  > Total IPs     : 2^{host_bits} = {total_ips:,}\n") 
        
        # Step 2: Identify the Interesting Octet
        if cidr >= 24:
            interesting_octet = 4
            host_bits_in_octet = 32 - cidr
        elif cidr >= 16:
            interesting_octet = 3
            host_bits_in_octet = 24 - cidr
        elif cidr >= 8:
            interesting_octet = 2
            host_bits_in_octet = 16 - cidr
        else:
            interesting_octet = 1
            host_bits_in_octet = 8 - cidr
            
        block_size = 2 ** host_bits_in_octet
        
        print("STEP 2: BLOCK SIZE & ODOMETER MATH")
        print(f"  > Interesting Octet : Octet {interesting_octet}")
        print(f"  > Host Bits in Octet: {host_bits_in_octet}")
        print(f"  > Block Size Math   : 2^{host_bits_in_octet} = {block_size}\n")
        
        # Step 3: Map the Boundaries
        net_id = network.network_address
        broadcast_id = network.broadcast_address
        
        # UPGRADE 1: The RFC 3021 & /32 Edge Cases
        if cidr == 32:
            first_host = "N/A (Single Host Route)"
            last_host = "N/A"
            usable_ips = 1
        elif cidr == 31:
            first_host = net_id
            last_host = broadcast_id
            usable_ips = 2
            print("  > [!] NOTE: /31 triggers RFC 3021 (Point-to-Point). No dedicated Network/Broadcast IDs.")
        else:
            first_host = net_id + 1
            last_host = broadcast_id - 1
            usable_ips = total_ips - 2
        
        print("STEP 3: NETWORK BOUNDARIES")
        print(f"  > Network ID    : {str(net_id)} (Start of block)")
        print(f"  > First Host    : {str(first_host)}")
        print(f"  > Last Host     : {str(last_host)}")
        print(f"  > Broadcast ID  : {str(broadcast_id)} (Odometer rolled to max)")
        print(f"  > Usable Hosts  : {usable_ips:,}\n")
        
        print("-" * 50)
        print("[+] BREAKDOWN COMPLETE.")
        
    except ValueError as e:
        print(f"[!] INVALID TARGET FORMAT: {e}")
        print("    Use format: IP/CIDR (e.g., 10.200.55.90/22)")

# --- Execution ---
if __name__ == "__main__":
    target = input("Enter Target IP with CIDR (e.g. 192.168.1.50/26): ")
    execute_subnet_breakdown(target)