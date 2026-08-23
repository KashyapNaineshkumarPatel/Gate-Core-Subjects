"""
Core Logic: Because ARP is a multiplexer that supports variable-length addresses (as seen in 04B), 
the operating system kernel cannot use a static C-structure to read the Target Protocol Address (TPA).

If a network driver receives a standard Ethernet/IPv4 ARP packet, the TPA starts exactly at byte 
offset 24. However, if the packet is InfiniBand/IPv4, the TPA starts at byte offset 52. If the 
kernel blindly read from offset 24, it would parse junk MAC data as an IP address, corrupting 
the routing table.

To prevent this, the OS kernel uses dynamic pointer arithmetic. The fixed ARP header is always 
8 bytes. The kernel reads HLEN and PLEN from bytes 4 and 5. It then mathematically calculates 
the memory offsets for SHA, SPA, THA, and TPA on the fly. 

If a malicious actor sends an ARP packet with HLEN=255, but the physical Ethernet frame is only 
64 bytes long, an unpatched kernel attempting to read the TPA via pointer arithmetic will trigger 
a Buffer Overflow or Segmentation Fault, causing a kernel panic (Blue Screen of Death). Modern 
kernels strictly validate (8 + 2*HLEN + 2*PLEN) against the socket buffer's physical length (sk_buff).
"""

import sys
import shutil
import time
from typing import Any, Dict

class ARPMemoryAllocatorEngine:
    alloc_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.alloc_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_length(self, length_input: str, name: str) -> int:
        try:
            val = int(length_input)
            if not 0 <= val <= 255:
                raise ValueError(f"Bounds Error: {name} must be a valid 1-byte integer (0-255).")
            return val
        except ValueError as e:
            raise ValueError(f"Type Error: {name} must be an integer. {e}")

    def execute_memory_allocation(self, hlen: int, plen: int, frame_len: int = 64) -> None:
        """Simulates OS kernel pointer arithmetic and bounds checking for ARP structures."""
        
        base_offset = 8
        
        # Kernel Pointer Arithmetic
        sha_offset = base_offset
        spa_offset = sha_offset + hlen
        tha_offset = spa_offset + plen
        tpa_offset = tha_offset + hlen
        total_arp_size = tpa_offset + plen
        
        # Vulnerability / Bounds Checking Simulation
        kernel_panic = False
        action = ""
        
        if total_arp_size > frame_len:
            kernel_panic = True
            action = (
                f"KERNEL PANIC (SEGFAULT): Pointer calculated TPA ends at byte {total_arp_size}, "
                f"but physical frame socket buffer (sk_buff) is only {frame_len} bytes. "
                "The kernel attempted to read unallocated memory!"
            )
        else:
            action = (
                f"BOUNDS CHECK PASSED: Required {total_arp_size} bytes <= Buffer {frame_len} bytes. "
                "Pointers safely cast to extract addresses."
            )

        mechanics = (
            f"uint8_t *arp_ptr = buffer; \n"
            f"     SHA = arp_ptr + {sha_offset}; \n"
            f"     SPA = arp_ptr + {spa_offset}; \n"
            f"     THA = arp_ptr + {tha_offset}; \n"
            f"     TPA = arp_ptr + {tpa_offset};"
        )

        insight = (
            "This dynamic offset calculation is the Achilles' heel of C-based network drivers. "
            "Historically, attackers could craft packets with spoofed HLEN/PLEN fields to force the "
            "kernel to read out-of-bounds memory, leading to remote denial-of-service or memory disclosure "
            "vulnerabilities in the networking stack."
        )

        self.alloc_state = {
            "hlen": hlen,
            "plen": plen,
            "total_size": total_arp_size,
            "sha_offset": sha_offset,
            "spa_offset": spa_offset,
            "tha_offset": tha_offset,
            "tpa_offset": tpa_offset,
            "frame_len": frame_len,
            "kernel_panic": kernel_panic,
            "action": action,
            "mechanics": mechanics,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.alloc_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04C: HLEN/PLEN KERNEL MEMORY ALLOCATOR ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] KERNEL POINTER ARITHMETIC (C-STRUCT OFFSETS):")
        time.sleep(0.2)
        print(f"     -> Base Header End  : Byte {8}")
        print(f"     -> SHA Offset       : Byte {state['sha_offset']} (Length: {state['hlen']})")
        print(f"     -> SPA Offset       : Byte {state['spa_offset']} (Length: {state['plen']})")
        print(f"     -> THA Offset       : Byte {state['tha_offset']} (Length: {state['hlen']})")
        print(f"     -> TPA Offset       : Byte {state['tpa_offset']} (Length: {state['plen']})")
        print("-" * width)
        
        print(" [i] C-CODE MEMORY EXTRACTION SIMULATION:")
        for line in state['mechanics'].split('\n'):
            time.sleep(0.1)
            print(f"     {line}")
        print("-" * width)
        
        print(" [!] SOCKET BUFFER BOUNDS CHECKING:")
        time.sleep(0.3)
        print(f"     -> Computed ARP Size: {state['total_size']} Bytes")
        print(f"     -> Physical L2 Frame: {state['frame_len']} Bytes")
        status = "[ X ] FATAL EXCEPTION" if state['kernel_panic'] else "[ > ] ALLOCATION SAFE"
        print(f"     -> Status           : {status}")
        time.sleep(0.2)
        print(f"     -> {state['action']}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = ARPMemoryAllocatorEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04C_HLEN_PLEN_MEMORY_ALLOCATOR INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Configure ARP Payload Length Definitions:")
            
            print("    (Tip: Standard Ethernet HLEN is 6. InfiniBand is 20.)")
            hlen_in = input("    Hardware Address Length (HLEN) [Default: 6]  : ").strip() or "6"
            if hlen_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            print("    (Tip: Standard IPv4 PLEN is 4. IPv6 is 16.)")
            plen_in = input("    Protocol Address Length (PLEN) [Default: 4]  : ").strip() or "4"
            
            print("\n    (Simulating a minimum 64-byte Ethernet frame padding)")
            frame_in = input("    Received Physical Frame Size   [Default: 64] : ").strip() or "64"
            
            hlen = engine.validate_length(hlen_in, "HLEN")
            plen = engine.validate_length(plen_in, "PLEN")
            frame_len = engine.validate_length(frame_in, "Frame Size")
            
            engine.execute_memory_allocation(hlen, plen, frame_len)
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