"""
Core Logic: When a host wants to send an IP packet to a local destination, it must 
wrap that IP packet in an Ethernet frame. To do that, it needs the destination's 
physical MAC address. If it doesn't have it, it must pause the transmission and 
initiate Address Resolution Protocol (ARP - RFC 826).

An ARP Request is not an IP packet. It has no IP header. It is a raw 28-byte payload 
sitting directly inside an Ethernet frame (EtherType 0x0806). 

The 28-byte payload is mathematically structured as follows:
- Hardware Type (HTYPE): 2 Bytes (0x0001 for Ethernet)
- Protocol Type (PTYPE): 2 Bytes (0x0800 for IPv4)
- Hardware Address Length (HLEN): 1 Byte (0x06 for MAC)
- Protocol Address Length (PLEN): 1 Byte (0x04 for IPv4)
- Operation Code (OPER): 2 Bytes (0x0001 for Request, 0x0002 for Reply)
- Sender Hardware Address (SHA): 6 Bytes
- Sender Protocol Address (SPA): 4 Bytes
- Target Hardware Address (THA): 6 Bytes (Set to 00:00:00:00:00:00 in Requests)
- Target Protocol Address (TPA): 4 Bytes

Because the sender doesn't know the Target MAC, the outer Ethernet frame encapsulates 
this payload and uses the physical Broadcast address (FF:FF:FF:FF:FF:FF) so every 
switch ASIC on the subnet floods it to every connected machine.
"""

import sys
import re
import shutil
import time
import socket
import struct
from typing import Any, Dict

class ARPHexEncoderEngine:
    arp_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.arp_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_mac(self, mac_input: str, name: str) -> str:
        cleaned = re.sub(r'[:\-\.\s]', '', mac_input).upper()
        if len(cleaned) != 12 or not all(c in '0123456789ABCDEF' for c in cleaned):
            raise ValueError(f"Syntax Error: Invalid MAC format for {name}. Expected 12 hex chars.")
        return ":".join([cleaned[i:i+2] for i in range(0, 12, 2)])

    def validate_ip(self, ip_input: str, name: str) -> str:
        try:
            # Validates IPv4 and normalizes it
            socket.inet_aton(ip_input)
            return ip_input
        except socket.error:
            raise ValueError(f"Syntax Error: Invalid IPv4 format for {name}.")

    def ip_to_hex(self, ip_addr: str) -> str:
        """Converts an IPv4 address to its 4-byte hex representation."""
        packed_ip = socket.inet_aton(ip_addr)
        return packed_ip.hex().upper()

    def mac_to_hex(self, mac_addr: str) -> str:
        """Strips colons to return a raw 6-byte hex string."""
        return mac_addr.replace(":", "").upper()

    def execute_arp_encoding(self, sender_mac: str, sender_ip: str, target_ip: str, op_type: str) -> None:
        """Constructs the raw 28-byte RFC 826 hexadecimal payload."""
        
        # 1. Static Fields (Ethernet / IPv4)
        htype = "0001" # 2 Bytes
        ptype = "0800" # 2 Bytes
        hlen = "06"    # 1 Byte
        plen = "04"    # 1 Byte
        
        # 2. Dynamic Operation Field
        is_request = (op_type == "REQUEST")
        oper = "0001" if is_request else "0002" # 2 Bytes
        
        # 3. Dynamic Addresses
        sha_hex = self.mac_to_hex(sender_mac)
        spa_hex = self.ip_to_hex(sender_ip)
        
        if is_request:
            tha_mac = "00:00:00:00:00:00"
            tha_hex = "000000000000"
            outer_dst_mac = "FF:FF:FF:FF:FF:FF (Broadcast)"
            mechanics = "The sender does not know the Target MAC. THA is zeroed out. The outer frame is Broadcast."
        else:
            # Simulate a reply from a fictional target (usually provided by OS)
            tha_mac = "AA:BB:CC:DD:EE:FF" 
            tha_hex = self.mac_to_hex(tha_mac)
            outer_dst_mac = f"{tha_mac} (Unicast)"
            mechanics = "The target replies directly. The outer frame is a Unicast directly to the sender's MAC."
            
        tpa_hex = self.ip_to_hex(target_ip)
        
        # 4. Payload Concatenation (28 Bytes total)
        raw_payload = f"{htype}{ptype}{hlen}{plen}{oper}{sha_hex}{spa_hex}{tha_hex}{tpa_hex}"
        
        # Format for readability
        formatted_hex = " ".join([raw_payload[i:i+4] for i in range(0, len(raw_payload), 4)])

        insight = (
            "ARP does not use IP routing. It operates strictly at Layer 2.5. By dissecting the raw "
            "hexadecimal, we see that the payload relies completely on the physical broadcast capability "
            "of the Ethernet switch to reach the target machine's CPU."
        )

        self.arp_state = {
            "op_type": op_type,
            "sender_mac": sender_mac,
            "sender_ip": sender_ip,
            "target_mac": tha_mac if not is_request else "[UNKNOWN]",
            "target_ip": target_ip,
            "outer_dst": outer_dst_mac,
            "hex_payload": formatted_hex,
            "mechanics": mechanics,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.arp_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04A: RFC 826 ARP HEX ENCODER ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] ARP TRANSACTION PARAMETERS:")
        print(f"     -> Operation        : ARP {state['op_type']}")
        print(f"     -> Sender Config    : {state['sender_ip']} ({state['sender_mac']})")
        print(f"     -> Target Config    : {state['target_ip']} ({state['target_mac']})")
        print("-" * width)
        
        print(" [i] L2 ETHERNET ENCAPSULATION:")
        time.sleep(0.3)
        print(f"     -> EtherType        : 0x0806 (ARP)")
        print(f"     -> Outer Dest MAC   : {state['outer_dst']}")
        print(f"     -> {state['mechanics']}")
        print("-" * width)
        
        print(" [!] RAW 28-BYTE HEXADECIMAL PAYLOAD:")
        time.sleep(0.4)
        print(f"     -> {state['hex_payload']}")
        print("        |HTYP|PTYP|HL|PL|OPCD| SHA (6B) | SPA(4B)| THA (6B) | TPA(4B)|")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL WIRE INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = ARPHexEncoderEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04A_RFC826_HEX_ENCODER INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure ARP Payload Variables:")
            
            mac_in = input("    Sender MAC Address [Default: 00:11:22:33:44:55] : ").strip() or "00:11:22:33:44:55"
            if mac_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            sip_in = input("    Sender IPv4        [Default: 192.168.1.10]      : ").strip() or "192.168.1.10"
            tip_in = input("    Target IPv4        [Default: 192.168.1.1]       : ").strip() or "192.168.1.1"
            
            print("\n    Select Operation:")
            print("      1: ARP Request (Who has Target IP?)")
            print("      2: ARP Reply   (I have Target IP)")
            op_in = input("    Choice (1/2)       [Default: 1]                 : ").strip() or "1"
            
            sender_mac = engine.validate_mac(mac_in, "Sender MAC")
            sender_ip = engine.validate_ip(sip_in, "Sender IP")
            target_ip = engine.validate_ip(tip_in, "Target IP")
            op_type = "REQUEST" if op_in == "1" else "REPLY"
            
            engine.execute_arp_encoding(sender_mac, sender_ip, target_ip, op_type)
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