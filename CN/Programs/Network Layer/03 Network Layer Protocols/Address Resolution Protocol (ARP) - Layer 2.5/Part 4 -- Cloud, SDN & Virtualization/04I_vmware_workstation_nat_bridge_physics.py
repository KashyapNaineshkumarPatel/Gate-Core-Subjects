"""
Core Logic: When you run a Virtual Machine on a Windows/Linux desktop (via VMware Workstation 
or VirtualBox), the hypervisor must figure out how to connect a fake, software-generated MAC 
address to a real physical network. It uses two primary ARP manipulation methods:

1. BRIDGED MODE (VMnet0): The hypervisor forces your physical host NIC into "Promiscuous Mode", 
   allowing it to read all packets on the wire, not just its own. The VM generates its own ARP 
   broadcasts, and the physical switch records the VM's software MAC in its CAM table. The 
   network treats the VM as a distinct physical machine.

2. NAT MODE (VMnet8): The hypervisor creates a hidden virtual router inside your host OS. 
   When the VM sends an ARP request for the Internet, the VMware NAT service intercepts it and 
   replies with a virtual MAC. When traffic leaves your physical PC, it is translated. The 
   physical switch and external network *never* see the VM's MAC address—they only see your 
   host machine's physical MAC.
"""

import sys
import shutil
import time
from typing import Any, Dict

class VMwareARPPhysicsEngine:
    vm_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.vm_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def execute_vmware_physics(self, mode: str, vm_mac: str, host_mac: str) -> None:
        """Simulates the ARP bridging and NAT physics inside desktop hypervisors."""
        
        switch_cam_table = {}
        host_nic_state = ""
        arp_flow = []
        insight = ""

        if mode == "1":
            # Bridged Mode Physics
            net_type = "VMnet0 (Bridged Networking)"
            host_nic_state = "PROMISCUOUS MODE (Accepting frames for both Host and VM MACs)"
            
            arp_flow.append("1. VM generates raw ARP Request [SHA: " + vm_mac + "].")
            arp_flow.append("2. VMware Bridge protocol injects frame directly onto physical wire.")
            arp_flow.append("3. Physical Switch reads Source MAC and updates its CAM table.")
            
            # Switch sees both the host and the VM
            switch_cam_table["Port_FastEth0/1"] = [host_mac, vm_mac]
            
            insight = (
                "In Bridged mode, the switch ASIC sees multiple MAC addresses originating from a single "
                "physical port. If the enterprise switch has Port Security (Sticky MAC) limited to 1 address, "
                "running a bridged VM will instantly trigger an Err-Disable port shutdown."
            )
            
        else:
            # NAT Mode Physics
            net_type = "VMnet8 (NAT Networking)"
            host_nic_state = "STANDARD MODE (Accepting frames only for Host MAC)"
            
            arp_flow.append("1. VM generates ARP Request for external IP [SHA: " + vm_mac + "].")
            arp_flow.append("2. VMware NAT Service (vmnat.exe) intercepts ARP, replies with virtual gateway MAC.")
            arp_flow.append("3. Host OS routes payload. Modifies packet using Host IP and Host MAC.")
            arp_flow.append("4. Physical Switch only sees the physical host's MAC address.")
            
            # Switch only sees the host
            switch_cam_table["Port_FastEth0/1"] = [host_mac]
            
            insight = (
                "NAT mode provides implicit Layer 2 security. Because the VM's MAC address is trapped "
                "inside the host's virtual switch (VMnet8), the VM is mathematically isolated from external "
                "ARP spoofing attacks, and the enterprise network administrator is blind to the VM's existence."
            )

        self.vm_state = {
            "net_type": net_type,
            "host_mac": host_mac,
            "vm_mac": vm_mac,
            "nic_state": host_nic_state,
            "flow": arp_flow,
            "cam": switch_cam_table,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.vm_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04I: VMWARE NAT/BRIDGE PHYSICS ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] HYPERVISOR CONFIGURATION: {state['net_type']}")
        print(f"     -> Host Physical MAC    : {state['host_mac']}")
        print(f"     -> VM Software MAC      : {state['vm_mac']}")
        print(f"     -> Host NIC Driver State: {state['nic_state']}")
        print("-" * width)
        
        print(" [i] ARP TRANSACTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.3)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] PHYSICAL SWITCH CAM TABLE RESULT:")
        time.sleep(0.4)
        for port, macs in state['cam'].items():
            for m in macs:
                print(f"     -> {port} : {m}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = VMwareARPPhysicsEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04I_VMWARE_WORKSTATION_NAT_BRIDGE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select Hypervisor Network Mode:")
            print("    1. Bridged Mode (VMnet0 - Direct Physical Access)")
            print("    2. NAT Mode     (VMnet8 - Host Routing)")
            mode_in = input("    Choice (1/2) [Default: 2] : ").strip() or "2"
            if mode_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            if mode_in not in ["1", "2"]:
                raise ValueError("Selection Error: Please choose 1 or 2.")
                
            host_mac = "AA:AA:AA:AA:AA:AA (Windows PC)"
            vm_mac = "00:50:56:C0:00:08 (VMware OUI)"
            
            engine.execute_vmware_physics(mode_in, vm_mac, host_mac)
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