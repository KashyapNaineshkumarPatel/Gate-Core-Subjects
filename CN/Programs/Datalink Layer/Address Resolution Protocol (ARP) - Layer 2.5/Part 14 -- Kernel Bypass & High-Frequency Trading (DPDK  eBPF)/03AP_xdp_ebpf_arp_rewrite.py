"""
Core Logic: The Linux network stack is highly robust, but inherently slow. 
When a frame arrives, the NIC fires a hardware interrupt, the driver allocates 
an `sk_buff` (socket buffer) in RAM, and the packet traverses multiple software 
layers (Netfilter, Routing, TCP/IP) before reaching the application.

XDP (eXpress Data Path) allows engineers to attach custom, highly restricted C code 
(compiled to eBPF bytecode) directly into the Network Interface Card (NIC) driver, 
BEFORE the kernel even knows the packet exists.

The XDP_TX ARP Rewrite:
1. An ARP Request arrives at the physical NIC.
2. Before an `sk_buff` is ever allocated, the eBPF program reads the raw packet 
   bytes directly from the NIC's DMA ring buffer.
3. If it matches a known IP, the eBPF code modifies the bytes in place (swapping 
   the Source and Destination MACs, changing Opcode to Reply, and writing the 
   target MAC).
4. The program returns the command `XDP_TX`.
5. The NIC instantly bounces the modified frame back out the physical wire.

The Linux kernel is completely bypassed. CPU context switching is avoided. 
Latency drops from ~50,000 nanoseconds to ~300 nanoseconds.
"""

import sys
import shutil
import time
from typing import Any, Dict

class XDPeBPFARPEngine:
    xdp_state: Dict[str, Any]

    def __init__(self) -> None:
        self.xdp_state = {}
        
        # High-Frequency Trading Target
        self.target_ip = "10.0.50.5"
        self.target_mac = "00:AA:BB:CC:DD:EE"
        
        # Baseline Latencies (Nanoseconds)
        self.kernel_latency_ns = 55000
        self.xdp_latency_ns = 350

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_packet_path(self, path_type: str) -> None:
        """Simulates the lifecycle of an ARP Request in Standard Linux vs XDP eBPF."""
        
        flow = []
        frames = []
        
        flow.append(f"1. [Physical Wire]: ARP Request arrives at NIC -> 'Who has {self.target_ip}?'")
        
        if path_type == "1":
            # Standard Linux Kernel Path
            flow.append("2. [NIC Hardware]: Fires Hard IRQ. Wakes CPU core.")
            flow.append("3. [NIC Driver]: Allocates 'sk_buff' data structure in main RAM (Expensive).")
            flow.append("4. [Linux Kernel]: Packet traverses GRO, TC, and Netfilter hooks.")
            flow.append("5. [ARP Subsystem]: Kernel executes routing table and ARP cache lookups.")
            flow.append(f"6. [ARP Subsystem]: Generates ARP Reply -> '{self.target_ip} is at {self.target_mac}'.")
            flow.append("7. [Linux Kernel]: Traverses egress TC and Qdisc (Queuing Disciplines).")
            flow.append("8. [NIC Driver]: Transmits frame. Frees 'sk_buff' memory.")
            
            action = "STANDARD KERNEL PROCESSING"
            latency = self.kernel_latency_ns
            insight = (
                "The standard Linux stack is incredibly safe and feature-rich, but the overhead of memory "
                "allocation (sk_buff) and traversing multiple subsystem locks introduces massive latency jitter. "
                "In High-Frequency Trading, 55 microseconds means you just lost the trade."
            )
            
            frame_1 = {
                "stage": "Egress (Kernel Managed)",
                "action": "Allocated, Queued, Transmitted",
                "cpu_cost": "High (Interrupts, Context Switches, Memory Allocation)"
            }
            frames.append(frame_1)

        else:
            # eBPF / XDP Fast Path
            flow.append("2. [NIC Driver]: eBPF program triggered AT THE INGRESS HOOK (pre-sk_buff).")
            flow.append("3. [eBPF VM]: Bytecode reads raw packet header straight from DMA ring buffer.")
            flow.append(f"4. [eBPF VM]: ARP matched. Modifying byte offsets in-place to construct Reply.")
            flow.append(f"   -> Swap MAC addresses (Bytes 0-11)")
            flow.append(f"   -> Change Opcode to 0x0002 (Reply)")
            flow.append(f"   -> Write Hardware Address {self.target_mac}")
            flow.append("5. [eBPF VM]: Program returns 'XDP_TX' exit code.")
            flow.append("6. [NIC Hardware]: Frame instantly bounced back out the physical Tx queue.")
            flow.append("7. [Linux Kernel]: Completely unaware the packet ever existed. Zero memory allocated.")
            
            action = "eBPF XDP_TX KERNEL BYPASS"
            latency = self.xdp_latency_ns
            insight = (
                "By intercepting the packet inside the driver ring buffer and returning XDP_TX, we turn "
                "a standard Linux server into a line-rate hardware switch. The OS kernel never wakes up, "
                "saving tens of thousands of nanoseconds and millions of CPU cycles under heavy DDoS load."
            )
            
            frame_1 = {
                "stage": "Egress (eBPF XDP_TX)",
                "action": "In-Place Byte Modification, Instant TX",
                "cpu_cost": "Microscopic (Pre-Allocation, No Context Switch)"
            }
            frames.append(frame_1)

        self.xdp_state = {
            "type": "Standard Linux Network Stack" if path_type == "1" else "XDP/eBPF Kernel Bypass",
            "latency": latency,
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.xdp_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AP: XDP eBPF ARP REWRITE ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] DATAPLANE ARCHITECTURE : {state['type']}")
        print("-" * width)
        
        print(" [i] PACKET LIFECYCLE SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.1)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] PERFORMANCE METRICS:")
        time.sleep(0.3)
        for frame in state['frames']:
            print(f"\n     [{frame['stage']}]")
            print(f"     Processing Action : {frame['action']}")
            print(f"     CPU Overhead      : {frame['cpu_cost']}")
        
        print(f"\n     -> End-to-End Latency : {state['latency']:,} nanoseconds")
        
        print("\n" + "-" * width)
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = XDPeBPFARPEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AP_XDP_EBPF_ARP_REWRITE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select NIC Ingress Architecture:")
            print("    1. Standard Linux Kernel (sk_buff, Netfilter, Routing)")
            print("    2. eBPF / XDP Hook (Driver-level XDP_TX execution)")
            
            choice = input("    Select architecture (1/2) [Default: 2] : ").strip() or "2"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice not in ["1", "2"]:
                raise ValueError("Selection Error: Please choose 1 or 2.")
            
            engine.execute_packet_path(choice)
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