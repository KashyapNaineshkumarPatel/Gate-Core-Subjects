"""
Core Logic: The DPU (Data Processing Unit) is essentially a complete computer 
plugged into the PCIe slot of the main server. It has its own ARM CPU cores, 
its own RAM, and its own embedded Linux OS.

The Hardware Offload Paradigm:
1. The main Host OS (x86 CPU running the AI workload or hypervisor) is completely 
   stripped of networking duties. 
2. The entire Open vSwitch (OVS) datapath, routing tables, and ARP caches are 
   pushed down into the DPU's ARM cores and ASIC.
3. When an ARP Request arrives from the wire, it hits the DPU.
4. The DPU's embedded ARM processor intercepts it, queries its isolated memory, 
   and generates the ARP Reply directly from the NIC.
5. The x86 Host CPU never receives a hardware interrupt. It remains in deep sleep 
   (C-states) or stays 100% focused on crunching AI matrices.

The network stack is physically physically divorced from the application compute.
"""

import sys
import shutil
import time
from typing import Any, Dict

class SmartNICDPUEngine:
    dpu_state: Dict[str, Any]

    def __init__(self) -> None:
        self.dpu_state = {}
        
        # Main Server (Host) State
        self.x86_host_ip = "10.200.1.50"
        self.x86_cpu_state = "IDLE (Deep C-State) / 100% Dedicated to Compute"
        
        # DPU (SmartNIC) State embedded on the PCIe card
        self.dpu_mac = "DP:UU:00:11:22:33"
        self.dpu_arm_cores = "ACTIVE (Handling Network Stack)"
        self.dpu_arp_cache = {
            "10.200.1.50": self.dpu_mac,
            "10.200.1.1": "GW:AA:BB:CC:DD:EE"
        }

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_dpu_offload(self, target_ip: str) -> None:
        """Simulates the DPU intercepting L2 traffic to protect x86 host compute cycles."""
        
        flow = []
        frames = []
        action = ""
        insight = ""
        
        flow.append(f"1. [Physical Wire]: Ingress ARP Request arrives at Server PCIe slot -> 'Who has {target_ip}?'")
        
        if target_ip == self.x86_host_ip:
            flow.append("2. [DPU Hardware]: Packet ingested into DPU local SRAM.")
            flow.append("3. [DPU ARM Cores]: Embedded Linux intercepts frame BEFORE it reaches the PCIe bus.")
            flow.append("4. [DPU ARM Cores]: Querying hardware-offloaded ARP/OVS table.")
            flow.append(f"5. [DPU ARM Cores]: Match found for Host IP. Synthesizing ARP Reply -> {self.dpu_mac}.")
            flow.append("6. [DPU Hardware]: Transmitting Reply back to wire.")
            flow.append("7. [x86 Host OS]: ZERO interrupts received. CPU continues rendering without jitter.")
            
            action = "HARDWARE OFFLOAD SUCCESS (Zero x86 Overhead)"
            insight = "By offloading the control plane and data plane to the DPU's ARM cores, the cloud provider can sell 100% of the x86 CPUs to the customer. The server OS doesn't even know it's connected to a network; it just reads and writes to a virtual PCIe memory buffer."
            
            frame = {
                "stage": "DPU Egress (Offloaded)",
                "processor": "ARM Cortex-A72 (On SmartNIC)",
                "x86_interrupts": "0 (Zero CPU Context Switches)"
            }
            frames.append(frame)

        else:
            flow.append("2. [DPU Hardware]: Packet ingested into DPU local SRAM.")
            flow.append("3. [DPU ARM Cores]: Intercepts frame. Queries offloaded routing tables.")
            flow.append("4. [DPU ARM Cores]: Target IP does not belong to the hosted x86 tenant.")
            flow.append("5. [DPU Hardware]: Frame silently dropped at the ASIC level.")
            flow.append("6. [x86 Host OS]: Securely isolated from background broadcast radiation.")
            
            action = "SILENT DROP (Hardware Enforced)"
            insight = "Unlike standard NICs that pass broadcasts up to the OS for evaluation, the DPU acts as a hard physical firewall at the edge of the server. Background network noise physically cannot cross the PCIe bus to steal host CPU cycles."
            
            frame = {
                "stage": "DPU Ingress Drop",
                "processor": "DPU ASIC Silicon",
                "x86_interrupts": "0"
            }
            frames.append(frame)

        self.dpu_state = {
            "target": target_ip,
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.dpu_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AV: SMARTNIC DPU ARP OFFLOAD ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] HARDWARE ISOLATION BOUNDARY:")
        print(f"     [Server Motherboard] x86 CPU State : {self.x86_cpu_state}")
        print(f"     [PCIe SmartNIC]      ARM CPU State : {self.dpu_arm_cores}")
        print(f"     [PCIe SmartNIC]      Offloaded IPs : {list(self.dpu_arp_cache.keys())}")
        print("-" * width)
        
        print(" [i] DATAPATH EXECUTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        if state['frames']:
            print(" [!] COMPUTE METRICS:")
            time.sleep(0.3)
            for frame in state['frames']:
                print(f"\n     [{frame['stage']}]")
                print(f"     Executing Processor : {frame['processor']}")
                print(f"     Host CPU Cost       : {frame['x86_interrupts']}")
                time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f"     -> Offload Status  : [ {state['action']} ]")
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = SmartNICDPUEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AV_SMARTNIC_DPU_ARP_OFFLOAD INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate Ingress Network Traffic to DPU:")
            print("    1. ARP Request for Hosted Tenant (10.200.1.50)")
            print("    2. ARP Request for Unrelated IP / Subnet Scan (10.200.1.99)")
            
            choice = input("    Select scenario (1/2) [Default: 1] : ").strip() or "1"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice == "1":
                target = "10.200.1.50"
            elif choice == "2":
                target = "10.200.1.99"
            else:
                raise ValueError("Selection Error: Please choose 1 or 2.")
            
            engine.execute_dpu_offload(target)
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