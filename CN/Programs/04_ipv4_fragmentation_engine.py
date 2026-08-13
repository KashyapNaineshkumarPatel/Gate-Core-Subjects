import sys

class IPv4FragmentationEngine:
    def __init__(self, total_packet_size: int, mtu: int, header_size: int = 20):
        self.total_packet_size = total_packet_size
        self.mtu = mtu
        self.header_size = header_size
        
        # EDGE CASE 1: Header Size bounds
        if self.header_size < 20 or self.header_size > 60:
            raise ValueError("[!] Invalid IPv4 Header Size. Must be between 20 and 60 bytes.")
            
        # EDGE CASE 2: IHL Scaling Rule (Header must be a multiple of 4)
        if self.header_size % 4 != 0:
            raise ValueError("[!] Invalid IPv4 Header Size. Must be a multiple of 4 (IHL scaling rule).")
            
        # EDGE CASE 3: MTU vs Header paradox
        if self.mtu <= self.header_size:
            raise ValueError(f"[!] MTU ({self.mtu}) is too small to even carry the {self.header_size}-byte IP Header!")

        # EDGE CASE 4: Packet smaller than header
        if self.total_packet_size < self.header_size:
            raise ValueError("[!] Total packet size cannot be smaller than the IP header itself.")

        self.total_data_to_send = self.total_packet_size - self.header_size

    def calculate_fragments(self):
        print(f"\n{'-'*65}")
        print(f"📡 INITIALIZING FRAGMENTATION ENGINE")
        print(f"  > Original Packet Size : {self.total_packet_size} bytes")
        print(f"  > Network MTU          : {self.mtu} bytes")
        print(f"  > IP Header Size       : {self.header_size} bytes")
        print(f"{'-'*65}")

        # Check if fragmentation is even necessary
        if self.total_packet_size <= self.mtu:
            print("[+] Packet fits within MTU. No fragmentation required.\n")
            return

        # Step 1: Calculate the Header Tax and the 8-Byte Rule
        max_data_per_fragment = self.mtu - self.header_size
        
        # The 8-Byte Divisibility Trap: Round down to the nearest multiple of 8
        usable_data_per_fragment = (max_data_per_fragment // 8) * 8
        
        if usable_data_per_fragment != max_data_per_fragment:
            print(f"[!] WARNING: Payload capacity ({max_data_per_fragment}) is not divisible by 8.")
            print(f"    Adjusting max data payload down to {usable_data_per_fragment} bytes per fragment.\n")

        fragments = []
        data_remaining = self.total_data_to_send
        current_offset = 0
        fragment_number = 1

        # Step 2: The Chop Loop
        while data_remaining > 0:
            if data_remaining > usable_data_per_fragment:
                # This is not the last fragment
                data_in_this_frag = usable_data_per_fragment
                mf_bit = 1
            else:
                # This is the final fragment
                data_in_this_frag = data_remaining
                mf_bit = 0

            total_frag_size = data_in_this_frag + self.header_size
            
            fragments.append({
                "Fragment": fragment_number,
                "Total Length": total_frag_size,
                "Data Payload": data_in_this_frag,
                "MF Bit": mf_bit,
                "Offset (Raw)": current_offset,
                "Offset (Scaled)": current_offset // 8
            })

            # Step 3: Move the odometer forward
            data_remaining -= data_in_this_frag
            current_offset += data_in_this_frag
            fragment_number += 1

        self._print_results(fragments)

    def _print_results(self, fragments: list):
        print("🔪 FRAGMENTATION RESULTS:")
        for frag in fragments:
            print(f"  [Frag {frag['Fragment']}] Total Length: {frag['Total Length']:<5} | "
                  f"Payload: {frag['Data Payload']:<5} | "
                  f"MF: {frag['MF Bit']} | "
                  f"Offset: {frag['Offset (Scaled)']}")
        print(f"{'-'*65}\n")


def interactive_mode():
    """Handles CLI input and sanitizes user errors."""
    print("="*65)
    print(" IPv4 FRAGMENTATION ENGINE ".center(65, "="))
    print("="*65)
    
    while True:
        try:
            packet_in = input("\n[?] Enter Total Packet Size in bytes (or 'q' to quit): ").strip()
            if packet_in.lower() == 'q':
                print("[+] Exiting engine.")
                break
            if not packet_in:
                continue
                
            total_packet_size = int(packet_in)
            mtu = int(input("[?] Enter Network MTU in bytes [e.g., 1500]      : ").strip())
            
            header_in = input("[?] Enter IP Header Size in bytes [Default: 20]  : ").strip()
            header_size = int(header_in) if header_in else 20
            
            # Execute Engine
            engine = IPv4FragmentationEngine(total_packet_size, mtu, header_size)
            engine.calculate_fragments()
            
        except ValueError as e:
            # Catch string-to-int conversion errors cleanly
            if "invalid literal" in str(e):
                print("[!] ERROR: Please enter valid numeric values. No letters or symbols.")
            else:
                # Catch our custom architectural rules
                print(f"{e}")
        except KeyboardInterrupt:
            print("\n[+] Exiting engine.")
            sys.exit(0)

if __name__ == "__main__":
    interactive_mode()