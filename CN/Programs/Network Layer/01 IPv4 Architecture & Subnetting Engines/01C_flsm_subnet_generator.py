import sys
import re
import shutil
import time
import math

class FLSMEngine:
    def __init__(self):
        # State Management Engine
        self.subnet_state = {}

    def _get_terminal_width(self):
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 90)

    def validate_and_parse(self, ip_input, subnets_input):
        # 1. IP Input Validation
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})$'
        match = re.match(pattern, ip_input)
        
        if not match:
            raise ValueError("Syntax Error: Target must be exactly IP/CIDR (e.g., 192.168.1.0/24)")
            
        octets = [int(match[i]) for i in range(1, 5)]
        original_cidr = int(match[5])
        
        for idx, octet in enumerate(octets):
            if octet < 0 or octet > 255:
                raise ValueError(f"System Error: Octet {idx+1} ({octet}) exceeds the 8-bit maximum of 255.")
                
        # 2. Subnet Count Validation & Descriptive Error Handling
        try:
            req_subnets = int(subnets_input)
        except ValueError as exc:
            raise ValueError("Type Error: Requested subnets must be an integer.") from exc
            
        if req_subnets < 2:
            raise ValueError(
                "Architectural Error: Subnetting means dividing a network. You must request at least 2 subnets."
            )

        # 3. Binary Borrowing Physics (The 1% Engineering Rule)
        borrowed_bits = math.ceil(math.log2(req_subnets))
        actual_subnets = 2 ** borrowed_bits
        new_cidr = original_cidr + borrowed_bits
        
        if new_cidr > 30:
            raise ValueError(
                f"Exhaustion Error: You requested {req_subnets} subnets from a /{original_cidr}. "
                f"This requires borrowing {borrowed_bits} bits, pushing the CIDR to /{new_cidr}. "
                f"IPv4 requires at least 2 host bits (a /30) for a functional network (Network ID, Broadcast, 2 Hosts). "
                f"This block is too small for this request."
            )

        return octets, original_cidr, req_subnets, actual_subnets, borrowed_bits, new_cidr

    def _get_network_id(self, octets, cidr):
        """Forces the input IP to its strict Network ID boundary."""
        mask_binary = ('1' * cidr) + ('0' * (32 - cidr))
        mask_octets = [int(mask_binary[i:i+8], 2) for i in range(0, 32, 8)]
        return [octets[i] & mask_octets[i] for i in range(4)]

    def generate_subnets(self, octets, original_cidr, req_subnets, actual_subnets, borrowed_bits, new_cidr):
        # Ensure we start exactly at the Network Boundary
        base_network = self._get_network_id(octets, original_cidr)
        
        # Calculate Magic Number (Block Size)
        host_bits = 32 - new_cidr
        block_size = 2 ** host_bits
        usable_hosts = block_size - 2 if host_bits > 1 else 0

        # Generate the ranges mathematically
        generated_blocks = []
        current_ip_int = (base_network[0] << 24) + (base_network[1] << 16) + (base_network[2] << 8) + base_network[3]

        # To prevent terminal flood, cap the output at 16 displayed subnets
        display_limit = min(actual_subnets, 16)

        for _ in range(display_limit):
            net_id = [
                (current_ip_int >> 24) & 255,
                (current_ip_int >> 16) & 255,
                (current_ip_int >> 8) & 255,
                current_ip_int & 255
            ]
            
            bcast_int = current_ip_int + block_size - 1
            bcast_id = [
                (bcast_int >> 24) & 255,
                (bcast_int >> 16) & 255,
                (bcast_int >> 8) & 255,
                bcast_int & 255
            ]
            
            generated_blocks.append({
                "network": f"{net_id[0]}.{net_id[1]}.{net_id[2]}.{net_id[3]}/{new_cidr}",
                "usable_range": f"{net_id[0]}.{net_id[1]}.{net_id[2]}.{net_id[3]+1} - {bcast_id[0]}.{bcast_id[1]}.{bcast_id[2]}.{bcast_id[3]-1}",
                "broadcast": f"{bcast_id[0]}.{bcast_id[1]}.{bcast_id[2]}.{bcast_id[3]}"
            })
            current_ip_int += block_size

        # Update State Tree
        self.subnet_state = {
            "target": f"{'.'.join(map(str, base_network))}/{original_cidr}",
            "requested": req_subnets,
            "actual": actual_subnets,
            "borrowed": borrowed_bits,
            "new_cidr": new_cidr,
            "block_size": block_size,
            "usable_hosts": usable_hosts,
            "blocks": generated_blocks
        }

    def render_ui(self):
        # Asynchronous UI Throttle
        time.sleep(0.2) 
        width = self._get_terminal_width()
        state = self.subnet_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 01C: FLSM SUBNET GENERATOR ".center(width))
        print("=" * width)
        
        print(f" [*] Major Block Target : {state['target']}")
        print("-" * width)
        
        # Educational Binary Physics Feedback
        if state['requested'] != state['actual']:
            print(f" [!] ARCHITECTURE NOTE: You requested {state['requested']} subnets.")
            print(f"     Subnetting borrows bits in powers of 2. The engine rounded up to {state['actual']} subnets.")
        else:
            print(f" [+] Perfect Power of 2 : {state['requested']} subnets requested and allocated.")
            
        print(f" [+] Bits Borrowed      : {state['borrowed']} bits")
        print(f" [+] New Subnet Mask    : /{state['new_cidr']}")
        print(f" [+] Magic Block Size   : {state['block_size']} total IPs per subnet")
        print(f" [+] Usable Hosts/Block : {state['usable_hosts']} hosts")
        print("-" * width)
        
        print(f" {'NETWORK ID':<18} | {'USABLE IP RANGE':<33} | BROADCAST ID")
        print("-" * width)
        
        for block in state['blocks']:
            print(f" {block['network']:<18} | {block['usable_range']:<33} | {block['broadcast']}")
            
        if state['actual'] > len(state['blocks']):
            print(f" ... and {state['actual'] - len(state['blocks'])} more subnets (Output truncated for terminal performance).")
            
        print("=" * width + "\n")

def interactive_loop():
    engine = FLSMEngine()
    width = engine._get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 01C_FLSM_SUBNET_GENERATOR INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            target_input = input("\n[?] Enter Major Block IP/CIDR (e.g., 192.168.1.0/24): ").strip()
            if target_input.lower() in ['quit', 'exit']:
                print("\n[+] Graceful shutdown initiated. Goodbye.")
                sys.exit(0)
            if not target_input:
                continue
                
            subnet_input = input("[?] How many subnets do you need?: ").strip()
            if subnet_input.lower() in ['quit', 'exit']:
                sys.exit(0)
                
            octets, old_cidr, req_sub, act_sub, borrowed, new_cidr = engine.validate_and_parse(target_input, subnet_input)
            engine.generate_subnets(octets, old_cidr, req_sub, act_sub, borrowed, new_cidr)
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