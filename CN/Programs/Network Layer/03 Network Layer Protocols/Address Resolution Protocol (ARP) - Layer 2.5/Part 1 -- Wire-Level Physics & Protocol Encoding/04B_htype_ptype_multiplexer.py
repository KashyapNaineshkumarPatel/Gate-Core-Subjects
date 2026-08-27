"""
Core Logic: When most people think of ARP, they think of mapping IPv4 addresses to 
Ethernet MAC addresses. However, RFC 826 was deliberately engineered to be a universal 
translator. It is not hardcoded to Ethernet or IPv4.

The first 4 bytes of the ARP payload define the Hardware Type (HTYPE) and Protocol Type (PTYPE).
- HTYPE (2 Bytes): Defines the physical network (e.g., 0x0001 for Ethernet, 0x0020 for InfiniBand).
- PTYPE (2 Bytes): Defines the logical network (e.g., 0x0800 for IPv4, 0x809B for AppleTalk).

Because different physical and logical networks have different address sizes, the next 
2 bytes define the Hardware Length (HLEN) and Protocol Length (PLEN). 
For example, an Ethernet MAC is 6 bytes (HLEN=0x06), but an InfiniBand GUID is 20 bytes 
(HLEN=0x14). 

By acting as a multiplexer, the ARP protocol can dynamically adapt its memory allocation 
and payload structure to bridge entirely different generations of technology.
"""

import sys
import shutil
import time
from typing import Any, Dict

class HTYPEPTYPEMultiplexerEngine:
    mux_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.mux_state = {}
        
        # Hardware Type Database (HTYPE / HLEN)
        self.hardware_db = {
            "1": {"name": "Ethernet (10Mb)", "htype": "0001", "hlen": "06", "len_dec": 6},
            "2": {"name": "IEEE 802 Networks / Token Ring", "htype": "0006", "hlen": "06", "len_dec": 6},
            "3": {"name": "InfiniBand", "htype": "0020", "hlen": "14", "len_dec": 20},
            "4": {"name": "Serial Line (SLIP)", "htype": "001C", "hlen": "00", "len_dec": 0}
        }
        
        # Protocol Type Database (PTYPE / PLEN)
        self.protocol_db = {
            "1": {"name": "IPv4", "ptype": "0800", "plen": "04", "len_dec": 4},
            "2": {"name": "AppleTalk (EtherTalk)", "ptype": "809B", "plen": "04", "len_dec": 4},
            "3": {"name": "IPX (Novell)", "ptype": "8137", "plen": "0A", "len_dec": 10}
        }

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def execute_multiplexing(self, hw_choice: str, proto_choice: str) -> None:
        """Simulates the dynamic ARP header construction based on HTYPE/PTYPE."""
        
        if hw_choice not in self.hardware_db:
            raise ValueError("Configuration Error: Invalid Hardware Type selection.")
        if proto_choice not in self.protocol_db:
            raise ValueError("Configuration Error: Invalid Protocol Type selection.")
            
        hw = self.hardware_db[hw_choice]
        proto = self.protocol_db[proto_choice]
        
        # Calculate total dynamic address payload size
        # SHA + SPA + THA + TPA = (HLEN + PLEN) * 2
        total_addr_bytes = (hw['len_dec'] + proto['len_dec']) * 2
        total_payload_bytes = 8 + total_addr_bytes # 8 bytes for fixed header
        
        header_hex = f"{hw['htype']} {proto['ptype']} {hw['hlen']} {proto['plen']}"
        
        if hw['name'] == "InfiniBand":
            mechanics = (
                "InfiniBand uses massive 20-byte Global Unique Identifiers (GUIDs). The OS dynamically "
                f"reads HLEN=0x14 and shifts the memory offsets so the {proto['name']} address isn't corrupted."
            )
        elif hw['name'] == "Serial Line (SLIP)":
            mechanics = (
                "SLIP is a point-to-point physical medium with no hardware addresses. HLEN is dynamically "
                "set to 0x00, completely removing the SHA and THA fields from the memory allocation."
            )
        else:
            mechanics = (
                f"Standard resolution: The ASIC prepares a memory block for {hw['len_dec']}-byte physical "
                f"addresses and {proto['len_dec']}-byte logical addresses."
            )

        insight = (
            "This multiplexing architecture is why ARP has survived for 40+ years. It separates the "
            "logical network (Layer 3) from the physical wire (Layer 1/2). As long as the OS updates "
            "its HTYPE dictionary, ARP can resolve IPs over physical mediums that hadn't even been "
            "invented when RFC 826 was written."
        )

        self.mux_state = {
            "hw_name": hw['name'],
            "proto_name": proto['name'],
            "header_hex": header_hex,
            "hlen_dec": hw['len_dec'],
            "plen_dec": proto['len_dec'],
            "total_bytes": total_payload_bytes,
            "mechanics": mechanics,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.mux_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04B: HTYPE/PTYPE PROTOCOL MULTIPLEXER ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] ARP PROTOCOL STACK CONFIGURATION:")
        print(f"     -> Hardware Layer (HTYPE) : {state['hw_name']}")
        print(f"     -> Logical Layer  (PTYPE) : {state['proto_name']}")
        print("-" * width)
        
        print(" [i] DYNAMIC HEADER GENERATION:")
        time.sleep(0.3)
        print(f"     -> Formatted Hex : [ {state['header_hex']} ]")
        print(f"     -> Field Mapping : [ HTYP | PTYP | HL | PL ]")
        print("-" * width)
        
        print(" [!] MEMORY ALLOCATION & PHYSICS:")
        time.sleep(0.3)
        print(f"     -> Target Hardware Size : {state['hlen_dec']} Bytes")
        print(f"     -> Target Protocol Size : {state['plen_dec']} Bytes")
        print(f"     -> Total Payload Size   : {state['total_bytes']} Bytes")
        print(f"     -> {state['mechanics']}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL ABSTRACTION INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = HTYPEPTYPEMultiplexerEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04B_HTYPE_PTYPE_MULTIPLEXER INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select Physical Hardware Layer (HTYPE):")
            print("    1. Ethernet (10Mb/1Gb/10Gb)")
            print("    2. Token Ring (IEEE 802)")
            print("    3. InfiniBand (20-Byte GUIDs)")
            print("    4. Serial Line (SLIP - No Hardware Address)")
            hw_in = input("    Choice (1-4) [Default: 3]: ").strip() or "3"
            if hw_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            print("\n[?] Select Logical Protocol Layer (PTYPE):")
            print("    1. IPv4 (4-Byte Address)")
            print("    2. AppleTalk (4-Byte Address)")
            print("    3. IPX / Novell (10-Byte Address)")
            proto_in = input("    Choice (1-3) [Default: 1]: ").strip() or "1"
            
            engine.execute_multiplexing(hw_in, proto_in)
            engine.render_ui()
            
        except ValueError as ve:
            print(f"\n[X] INTERCEPT TRIGGERED:\n    {ve}")
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()