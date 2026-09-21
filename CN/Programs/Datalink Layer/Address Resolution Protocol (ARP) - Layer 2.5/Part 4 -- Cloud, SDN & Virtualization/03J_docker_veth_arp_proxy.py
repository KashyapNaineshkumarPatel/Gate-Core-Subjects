"""
Core Logic: Container networking relies on Linux Network Namespaces to provide 
isolated TCP/IP stacks. But an isolated namespace has no physical connection to the wire. 
To bridge this gap, Linux uses a "veth pair" (Virtual Ethernet Pair).

A veth pair is a software-defined tube. One end sits inside the container's isolated 
namespace and is named 'eth0'. The other end sits in the host's root namespace, usually 
given a random name like 'veth3a9b1c', and is plugged into a virtual switch (docker0).

When Container A wants to reach the Internet, it sends an ARP Request for its Default 
Gateway (the docker0 bridge IP). 
1. The ARP broadcast enters the container's eth0.
2. It travels instantly through the veth tube to the host's root namespace.
3. The packet emerges from veth3a9b1c and hits the docker0 virtual bridge.
4. The host kernel intercepts the ARP request on the bridge and generates an ARP Reply 
   using the bridge's virtual MAC address.

If Container A wants to talk to Container B, the docker0 bridge acts as a standard Layer 2 
switch, flooding the ARP broadcast down all other connected veth tubes until Container B replies.
"""

import sys
import shutil
import time
from typing import Any, Dict

class DockerVethARPPhysicsEngine:
    veth_state: Dict[str, Any]

    def __init__(self) -> None:
        # Protected State Management
        self.veth_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def execute_namespace_physics(self, scenario: str) -> None:
        """Simulates ARP traversal across Linux Network Namespaces via veth pairs."""
        
        topology = ""
        arp_flow = []
        resolution = ""
        insight = ""

        # Base simulated environment
        container_a_ip = "172.17.0.2"
        container_a_mac = "02:42:ac:11:00:02"
        container_b_ip = "172.17.0.3"
        container_b_mac = "02:42:ac:11:00:03"
        bridge_ip = "172.17.0.1"
        bridge_mac = "02:42:75:32:11:01"

        if scenario == "1":
            # Scenario 1: Container to External (Gateway ARP)
            topology = "Container -> Host Root Namespace (docker0 Bridge)"
            
            arp_flow.append(f"1. [Namespace A]: App wants to reach 8.8.8.8. ARP generated for Gateway {bridge_ip}.")
            arp_flow.append(f"2. [Namespace A]: Broadcast sent into local 'eth0' [{container_a_mac}].")
            arp_flow.append("3. [Kernel]: Frame traverses the veth tube across namespace boundaries.")
            arp_flow.append(f"4. [Root Namespace]: Frame emerges from 'veth90c1a' and hits 'docker0' bridge.")
            arp_flow.append(f"5. [Root Namespace]: Host kernel intercepts. 'docker0' owns {bridge_ip}.")
            arp_flow.append(f"6. [Root Namespace]: Host kernel crafts ARP Reply with MAC {bridge_mac} and pushes back down veth tube.")
            
            resolution = f"SUCCESS: Container A caches Gateway MAC {bridge_mac}. Traffic routed via Host."
            
            insight = (
                "The docker0 bridge is not just a switch; it is a Layer 3 interface on the host. "
                "The host kernel acts as a proxy, routing traffic from the private 172.17.0.0/16 "
                "namespace out to the physical eth0 interface using NAT (IP Masquerading)."
            )

        else:
            # Scenario 2: Container to Container (L2 Flooding)
            topology = "Container A -> docker0 Bridge -> Container B"
            
            arp_flow.append(f"1. [Namespace A]: App wants to reach {container_b_ip}. Generates ARP Request.")
            arp_flow.append("2. [Namespace A]: Broadcast sent into 'eth0', traverses veth tube.")
            arp_flow.append("3. [Root Namespace]: Frame hits 'docker0' bridge.")
            arp_flow.append("4. [Root Namespace]: Bridge acts as L2 Switch. Floods broadcast to all other veth endpoints.")
            arp_flow.append(f"5. [Namespace B]: Frame drops out of 'eth0'. Container B matches {container_b_ip}.")
            arp_flow.append(f"6. [Namespace B]: Container B generates Unicast ARP Reply [{container_b_mac}] back up its veth tube.")
            
            resolution = f"SUCCESS: Container A caches Container B MAC {container_b_mac}. Direct L2 communication established."
            
            insight = (
                "While veth pairs provide excellent isolation, passing packets through the Linux network "
                "stack twice (once in the container namespace, once in the root namespace) creates massive "
                "CPU overhead. This is why high-performance K8s clusters abandon veth pairs for eBPF or macvlan."
            )

        self.veth_state = {
            "scenario_name": topology,
            "flow": arp_flow,
            "resolution": resolution,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.veth_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04J: DOCKER VETH ARP PROXY ENGINE ".center(width))
        print("=" * width)
        
        print(f" [+] NAMESPACE TOPOLOGY:")
        print(f"     -> Logical Path : {state['scenario_name']}")
        print("-" * width)
        
        print(" [i] VETH PAIR TRANSACTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.4)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] KERNEL RESOLUTION STATE:")
        time.sleep(0.3)
        print(f"     -> {state['resolution']}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL PERFORMANCE INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = DockerVethARPPhysicsEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04J_DOCKER_VETH_ARP_PROXY INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select Container Networking Scenario:")
            print("    1. Container to Internet (ARPing for docker0 Default Gateway)")
            print("    2. Container to Container (L2 Bridge Flooding via veth)")
            scenario_in = input("    Choice (1/2) [Default: 1] : ").strip() or "1"
            
            if scenario_in.lower() in ['quit', 'exit']: sys.exit(0)
            if scenario_in not in ["1", "2"]:
                raise ValueError("Selection Error: Please choose 1 or 2.")
            
            engine.execute_namespace_physics(scenario_in)
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