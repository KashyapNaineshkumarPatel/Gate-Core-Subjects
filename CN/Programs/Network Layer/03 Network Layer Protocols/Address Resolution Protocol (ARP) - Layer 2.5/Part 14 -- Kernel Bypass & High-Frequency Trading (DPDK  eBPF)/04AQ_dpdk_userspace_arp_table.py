"""
Core Logic: XDP (Module 04AP) runs inside the kernel's driver space. The Data Plane 
Development Kit (DPDK) takes the absolute extreme approach: it completely divorces 
the Network Interface Card (NIC) from the Linux Kernel.

The DPDK Architecture:
1. Unbinding: The NIC is physically unbound from the standard Linux driver (ixgbe/i40e) 
   and bound to a kernel-bypass module like `vfio-pci` or `igb_uio`.
2. OS Blindness: Once unbound, the interface disappears from the OS. `ifconfig`, 
   `ip route`, and `ip neigh` (ARP table) no longer see the hardware.
3. Poll Mode Driver (PMD): Instead of relying on hardware interrupts to wake the CPU 
   when a packet arrives, a DPDK application pins a thread to a dedicated CPU core. 
   That core spins at 100% utilization in an infinite loop, constantly polling the 
   NIC's RX ring buffer.
4. Userspace ARP: Because the kernel is blind, the standard OS ARP cache is gone. 
   If an HFT trading algorithm wants to send a FIX protocol packet to the exchange, 
   the DPDK application must manually maintain its own ARP table in userspace memory 
   (using Hugepages and rte_hash) and manually construct the Layer 2 Ethernet headers.

By operating entirely in userspace and polling memory instead of waiting for interrupts, 
DPDK achieves 10-40 million packets per second (Mpps) per CPU core, reducing latency 
to the absolute physical limit of the PCIe bus.
"""

import sys
import shutil
import time
from typing import Any, Dict

class DPDKUserspaceARPEngine:
    dpdk_state: Dict[str, Any]

    def __init__(self) -> None:
        self.dpdk_state = {}
        
        # DPDK Userspace Memory (Backed by 1GB Hugepages)
        self.rte_hash_arp_table = {
            "10.0.99.10": "EE:XX:CC:HH:AA:NN",  # Exchange Matching Engine
            "10.0.99.1":  "GG:AA:TT:EE:01:01"   # Default Gateway
        }
        
        self.app_ip = "10.0.99.50"
        self.app_mac = "HF:T0:00:11:22:33"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_dpdk_pipeline(self, target_ip: str) -> None:
        """Simulates an HFT application manually resolving L2 headers in userspace."""
        
        flow = []
        frames = []
        cpu_state = "100% UTILIZATION (POLL MODE DRIVER ACTIVE)"
        
        flow.append("1. [CPU Core 2]: Pinned thread spinning infinite while(1) loop (PMD).")
        flow.append(f"2. [HFT Algorithm]: Signal triggered. Initiating FIX order to {target_ip}.")
        flow.append("3. [DPDK Dataplane]: Querying userspace rte_hash ARP table in Hugepages.")
        
        if target_ip in self.rte_hash_arp_table:
            target_mac = self.rte_hash_arp_table[target_ip]
            flow.append(f"4. [DPDK Dataplane]: Memory Hit -> {target_mac}. Zero context switches incurred.")
            flow.append("5. [DPDK Dataplane]: Allocating 'rte_mbuf' directly from memory pool.")
            flow.append("6. [DPDK Dataplane]: Manually writing L2 Ethernet Header bytes (Src/Dst MAC).")
            flow.append("7. [NIC DMA]: DPDK writes buffer pointer directly to hardware TX ring.")
            
            action = "USERSPACE TX SUCCESS (SUB-MICROSECOND)"
            insight = "Because the application manages its own ARP state in RAM and bypasses interrupts entirely, the packet moves from the trading algorithm to the physical wire in under 1 microsecond. The OS kernel is completely oblivious."
            
            frame_1 = {
                "stage": "DPDK Zero-Copy TX",
                "encap": f"[ L2 MAC: {self.app_mac} -> {target_mac} ] | [ L3 IP: {self.app_ip} -> {target_ip} ] | [ FIX Payload ]",
                "memory": "rte_mbuf (Hugepages)"
            }
            frames.append(frame_1)
            
        else:
            flow.append("4. [DPDK Dataplane]: Memory Miss. Target IP not in userspace ARP table.")
            flow.append("5. [DPDK Dataplane]: WARNING - DPDK does not automatically resolve ARPs.")
            flow.append("6. [DPDK Application]: Must manually halt trading, construct an ARP Broadcast 'rte_mbuf', and inject it to TX.")
            flow.append("7. [DPDK Application]: Polling RX queue waiting for the Exchange to reply.")
            
            action = "USERSPACE ARP RESOLUTION REQUIRED"
            insight = "DPDK gives you raw speed, but strips away all conveniences. The developer must write their own C/C++ code to handle ARP, ICMP (Ping), and TCP states. If you forget to write an ARP resolver in your HFT app, you physically cannot communicate with the network."
            
            frame_1 = {
                "stage": "DPDK Manual ARP Broadcast Synthesis",
                "encap": f"[ L2 MAC: {self.app_mac} -> FF:FF:FF:FF:FF:FF ] | [ ARP Request: Who has {target_ip}? ]",
                "memory": "rte_mbuf (Hugepages)"
            }
            frames.append(frame_1)

        self.dpdk_state = {
            "target": target_ip,
            "cpu_state": cpu_state,
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.dpdk_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AQ: DPDK USERSPACE ARP & MEMORY ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] DPDK KERNEL-BYPASS ENVIRONMENT:")
        print(f"     -> CPU Core State    : {state['cpu_state']}")
        print(f"     -> OS ARP Table      : OFFLINE (NIC Unbound from Linux)")
        print(f"     -> rte_hash (RAM)    : {list(self.rte_hash_arp_table.keys())}")
        print("-" * width)
        
        print(" [i] USERSPACE PACKET PROCESSING SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] MEMORY & ENCAPSULATION STATE:")
        time.sleep(0.3)
        for frame in state['frames']:
            print(f"\n     [{frame['stage']}]")
            print(f"     Structure : {frame['encap']}")
            print(f"     Allocated : {frame['memory']}")
            time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f"     -> Dataplane Action : [ {state['action']} ]")
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = DPDKUserspaceARPEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AQ_DPDK_USERSPACE_ARP_TABLE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate HFT Order Execution (Target IP):")
            print("    1. Target Exchange Matching Engine (10.0.99.10) - Known in memory")
            print("    2. Target New Feed Handler (10.0.99.15) - Unknown in memory")
            
            choice = input("    Select target (1/2) [Default: 1] : ").strip() or "1"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice == "1":
                target_ip = "10.0.99.10"
            elif choice == "2":
                target_ip = "10.0.99.15"
            else:
                raise ValueError("Selection Error: Please choose 1 or 2.")
            
            engine.execute_dpdk_pipeline(target_ip)
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