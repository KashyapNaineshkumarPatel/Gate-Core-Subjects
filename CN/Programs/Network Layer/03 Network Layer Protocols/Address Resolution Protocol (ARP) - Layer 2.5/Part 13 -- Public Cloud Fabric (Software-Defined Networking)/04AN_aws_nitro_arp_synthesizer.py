"""
Core Logic: If you spin up two EC2 instances in an AWS Virtual Private Cloud (VPC) 
and run Wireshark, you will see ARP traffic. But this is a matrix-level illusion.

Public cloud providers (AWS, Azure, GCP) do not run traditional Layer 2 broadcast 
domains. If one tenant's ARP broadcast could reach another tenant's VM, the security 
and scalability of the cloud would collapse. 

The AWS Nitro System (SmartNIC / Hypervisor) employs ARP Synthesis.
1. An EC2 instance needs to communicate with another instance in the same VPC subnet.
2. The EC2 OS (Linux/Windows) doesn't know it's in the cloud. It naturally generates 
   a standard FF:FF:FF:FF:FF:FF L2 ARP broadcast.
3. The frame never touches a physical wire. The AWS Nitro card attached to the VM 
   intercepts the broadcast instantly.
4. Nitro queries the AWS centralized SDN Control Plane (the VPC Mapping Service).
5. The SDN controller returns the destination's MAC and physical host location.
6. Nitro locally generates a completely synthesized ARP Reply and injects it back 
   up into the EC2 instance's memory, pretending the target responded.

The broadcast is mathematically terminated at the edge. True Layer 2 does not exist.
"""

import sys
import shutil
import time
from typing import Any, Dict

class AWSNitroARPEngine:
    nitro_state: Dict[str, Any]

    def __init__(self) -> None:
        self.nitro_state = {}
        
        # Centralized VPC SDN Mapping Service (The "Source of Truth")
        self.vpc_mapping_service = {
            "10.0.1.50": {"mac": "02:50:00:00:00:01", "host": "PHYSICAL_RACK_A1"},
            "10.0.1.51": {"mac": "02:50:00:00:00:02", "host": "PHYSICAL_RACK_B4"},
            "10.0.1.1":  {"mac": "02:50:00:00:00:FF", "host": "AWS_VPC_ROUTER"}
        }
        
        self.ec2_source_ip = "10.0.1.50"
        self.ec2_source_mac = self.vpc_mapping_service[self.ec2_source_ip]["mac"]

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_arp_synthesis(self, target_ip: str) -> None:
        """Simulates the AWS Nitro hypervisor intercepting and synthesizing an ARP reply."""
        
        flow = []
        frames = []
        
        flow.append(f"1. [EC2 Instance OS]: Generating standard ARP Broadcast -> 'Who has {target_ip}?'")
        
        # Frame 1: The EC2 Illusion
        frame_1 = {
            "stage": "Guest OS Output (Trapped by Hypervisor)",
            "l2_src": self.ec2_source_mac, "l2_dst": "FF:FF:FF:FF:FF:FF",
            "action": "TRAPPED (Never hits a physical wire)"
        }
        frames.append(frame_1)
        
        flow.append("2. [AWS Nitro SmartNIC]: Intercepts Broadcast. Drops L2 frame to protect cloud fabric.")
        flow.append(f"3. [AWS Nitro SmartNIC]: Queries VPC Mapping Service via gRPC for IP {target_ip}.")
        
        if target_ip in self.vpc_mapping_service:
            target_data = self.vpc_mapping_service[target_ip]
            flow.append(f"4. [VPC SDN Controller]: Match found. IP belongs to MAC {target_data['mac']} on {target_data['host']}.")
            flow.append("5. [AWS Nitro SmartNIC]: Synthesizing fake ARP Reply using SDN data.")
            flow.append("6. [AWS Nitro SmartNIC]: Injecting synthesized frame directly into EC2 vNIC memory.")
            
            # Frame 2: The Synthesized Reply
            frame_2 = {
                "stage": "Hypervisor Injection (Synthesized Reply)",
                "l2_src": target_data['mac'], "l2_dst": self.ec2_source_mac,
                "action": "INJECTED (Appears real to EC2 OS)"
            }
            frames.append(frame_2)
            
            action = "SYNTHESIZED REPLY SUCCESS"
            insight = "By synthesizing ARP at the hypervisor boundary, AWS eliminates broadcast storms entirely. The VPC can scale to millions of instances because the physical spine-leaf network never sees a single ARP broadcast. It operates purely as a high-speed IP transport underlay."
        else:
            flow.append(f"4. [VPC SDN Controller]: Query failed. Target IP {target_ip} not provisioned in this VPC.")
            flow.append("5. [AWS Nitro SmartNIC]: Silently discards the request. No reply injected.")
            action = "SILENT DROP (Unprovisioned IP)"
            insight = "In a traditional network, scanning a subnet creates massive broadcast noise. In AWS, scanning unprovisioned IPs generates zero network traffic. The hypervisor silently drops the queries, rendering standard L2 network discovery tools useless."

        self.nitro_state = {
            "target": target_ip,
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.nitro_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AN: AWS NITRO ARP SYNTHESIZER ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] AWS VPC SDN MAPPING SERVICE (CENTRAL TRUTH):")
        for ip, data in self.vpc_mapping_service.items():
            print(f"     -> IP: {ip:<12} | MAC: {data['mac']} | Location: {data['host']}")
        print("-" * width)
        
        print(" [i] HYPERVISOR INTERCEPTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        if state['frames']:
            print(" [!] DATAPLANE ILLUSION STATE:")
            time.sleep(0.3)
            for frame in state['frames']:
                print(f"\n     [{frame['stage']}]")
                print(f"     L2 Structure : [ Src: {frame['l2_src']} -> Dst: {frame['l2_dst']} ]")
                print(f"     Nitro Action : {frame['action']}")
                time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f"     -> Outcome Outcome  : [ {state['action']} ]")
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = AWSNitroARPEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AN_AWS_NITRO_ARP_SYNTHESIZER INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Simulate EC2 Instance ARP Request:")
            print("    1. Request known Peer EC2 (10.0.1.51)")
            print("    2. Request AWS VPC Default Router (10.0.1.1)")
            print("    3. Request an Unprovisioned IP (10.0.1.99)")
            
            choice = input("    Select target (1/2/3) [Default: 1] : ").strip() or "1"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice == "1":
                target_ip = "10.0.1.51"
            elif choice == "2":
                target_ip = "10.0.1.1"
            elif choice == "3":
                target_ip = "10.0.1.99"
            else:
                raise ValueError("Selection Error: Please choose 1, 2, or 3.")
            
            engine.execute_arp_synthesis(target_ip)
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