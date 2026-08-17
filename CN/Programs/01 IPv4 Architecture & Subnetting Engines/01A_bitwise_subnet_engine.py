import sys
import re
import shutil
import time

class BitwiseSubnetEngine:
    def __init__(self):
        # State Management Engine
        self.network_state = {}

    def _get_terminal_width(self):
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 80)

    def validate_and_parse(self, ip_input):
        # Input Bounds Validation & Descriptive Error Handling
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})$'
        match = re.match(pattern, ip_input)
        
        if not match:
            raise ValueError("Syntax Error: Format must be exactly IP/CIDR (e.g., 192.168.1.50/26)")
            
        octets = [int(match[i]) for i in range(1, 5)]
        cidr = int(match[5])
        
        # Descriptive Octet Overflow Handling
        for idx, octet in enumerate(octets):
            if octet < 0 or octet > 255:
                raise ValueError(
                    f"System Error: An IPv4 octet is exactly 8 bits. The maximum possible value is 255 (11111111). "
                    f"You entered '{octet}' in octet {idx+1}, which requires 9 bits and causes a memory overflow."
                )
                
        # Descriptive CIDR Overflow Handling
        if cidr < 0 or cidr > 32:
            raise ValueError(
                f"System Error: IPv4 architecture is strictly limited to 32 bits. "
                f"You requested a /{cidr} mask, which exceeds the physical 32-bit hardware limit."
            )
            
        return octets, cidr

    def _to_binary_str(self, octets):
        return '.'.join([f"{octet:08b}" for octet in octets])

    def execute_bitwise_math(self, octets, cidr):
        # 1. Mask Generation
        mask_binary_str = ('1' * cidr) + ('0' * (32 - cidr))
        mask_octets = [int(mask_binary_str[i:i+8], 2) for i in range(0, 32, 8)]
        
        # 2. Network ID (Bitwise AND)
        network_octets = [octets[i] & mask_octets[i] for i in range(4)]
        
        # 3. Broadcast ID (Bitwise OR with Inverted Mask)
        inverted_mask_octets = [255 - m for m in mask_octets]
        broadcast_octets = [network_octets[i] | inverted_mask_octets[i] for i in range(4)]
        
        # 4. Host Calculations
        total_hosts = 2 ** (32 - cidr)
        usable_hosts = total_hosts - 2 if cidr < 31 else 0
        
        first_host = network_octets.copy()
        first_host[3] += 1
        last_host = broadcast_octets.copy()
        last_host[3] -= 1

        # Update State Tree
        self.network_state = {
            "target": f"{'.'.join(map(str, octets))}/{cidr}",
            "target_bin": self._to_binary_str(octets),
            "mask": '.'.join(map(str, mask_octets)),
            "mask_bin": self._to_binary_str(mask_octets),
            "network": '.'.join(map(str, network_octets)),
            "network_bin": self._to_binary_str(network_octets),
            "broadcast": '.'.join(map(str, broadcast_octets)),
            "broadcast_bin": self._to_binary_str(broadcast_octets),
            "first_host": '.'.join(map(str, first_host)),
            "last_host": '.'.join(map(str, last_host)),
            "usable_hosts": usable_hosts
        }

    def render_ui(self):
        # Asynchronous UI Throttle
        time.sleep(0.15) 
        width = self._get_terminal_width()
        state = self.network_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 01A: IPv4 BITWISE ENGINE ".center(width))
        print("=" * width)
        
        print(f" [*] Target IP      : {state['target']}")
        print(f"     Binary         : {state['target_bin']}")
        print("-" * width)
        
        print(f" [+] Subnet Mask    : {state['mask']}")
        print(f"     Binary         : {state['mask_bin']}")
        print("-" * width)
        
        print(f" [+] Network ID     : {state['network']}")
        print(f"     Binary (AND)   : {state['network_bin']}")
        print("-" * width)
        
        print(f" [+] Broadcast ID   : {state['broadcast']}")
        print(f"     Binary (OR)    : {state['broadcast_bin']}")
        print("-" * width)
        
        if state['usable_hosts'] > 0:
            print(f" [+] Usable Range   : {state['first_host']} -> {state['last_host']}")
        else:
            print(" [+] Usable Range   : NONE (Point-to-Point or Host Route)")
            
        print(f" [+] Usable Hosts   : {state['usable_hosts']:,}")
        print("=" * width + "\n")

def interactive_loop():
    engine = BitwiseSubnetEngine()
    width = engine._get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 01A_BITWISE_SUBNET_ENGINE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            user_input = input("\n[?] Enter IP/CIDR to process (e.g., 10.0.0.50/26): ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                print("\n[+] Graceful shutdown initiated. Goodbye.")
                sys.exit(0)
                
            if not user_input:
                continue
                
            octets, cidr = engine.validate_and_parse(user_input)
            engine.execute_bitwise_math(octets, cidr)
            engine.render_ui()
            
        except ValueError as ve:
            print(f"\n[X] VALIDATION INTERCEPT: {ve}")
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Safely spinning down engine...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()