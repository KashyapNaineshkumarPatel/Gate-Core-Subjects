"""
Core Logic: Modern Kubernetes architectures (like GKE Dataplane V2 / Cilium) utilize 
eBPF (Extended Berkeley Packet Filter) to bypass the traditional Linux networking 
stack entirely for Pod-to-Pod communication.

The eBPF ARP-less Architecture:
1. The Cilium Agent runs on every K8s Worker Node. It watches the K8s API Server 
   and builds a globally synchronized eBPF Map in kernel space containing every 
   Pod IP, MAC, and Node location.
2. A small eBPF C program is attached to the Traffic Control (tc) ingress hook of 
   every Pod's virtual interface.
3. When Pod-A tries to communicate with Pod-B, if Pod-A's OS generates an ARP Request, 
   the eBPF program intercepts it instantly. It looks up the target IP in the eBPF Map, 
   synthesizes the ARP Reply, and injects it back to Pod-A. The broadcast is killed.
4. Better yet, when the actual IP packet is sent, eBPF intercepts it, directly 
   rewrites the Layer 2 Ethernet Destination MAC in memory, and uses a helper function 
   (`bpf_redirect_peer`) to instantly jump the packet to Pod-B's interface. 

No Linux bridge. No iptables routing. ARP is reduced to a local, synthesized illusion.
"""

import sys
import shutil
import time
from typing import Any, Dict

class CiliumeBPFEngine:
    cilium_state: Dict[str, Any]

    def __init__(self) -> None:
        self.cilium_state = {}
        
        # Kubernetes eBPF Map (Synchronized by Cilium Agent via API Server)
        # BPF_MAP_TYPE_HASH stored directly in kernel memory
        self.ebpf_endpoint_map = {
            "10.0.1.50": {"mac": "AA:BB:CC:00:01:50", "node": "worker-node-1", "veth": "lxc_pod_a"},
            "10.0.1.51": {"mac": "AA:BB:CC:00:01:51", "node": "worker-node-1", "veth": "lxc_pod_b"},
            "10.0.2.99": {"mac": "AA:BB:CC:00:02:99", "node": "worker-node-2", "veth": "lxc_pod_c"}
        }
        
        self.source_pod_ip = "10.0.1.50"
        self.source_pod_mac = "AA:BB:CC:00:01:50"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 115)

    def execute_ebpf_datapath(self, target_ip: str, scenario: str) -> None:
        """Simulates eBPF TC hooks intercepting ARP and L3 traffic in K8s."""
        
        flow = []
        frames = []
        action = ""
        insight = ""
        
        if target_ip not in self.ebpf_endpoint_map:
            flow.append(f"1. [Cilium Agent]: IP {target_ip} not found in cluster eBPF map.")
            flow.append("2. [eBPF TC Hook]: Packet passed up to standard Linux routing stack (Default Gateway).")
            action = "FALLBACK TO LINUX STACK"
            insight = "If a packet is destined for the external internet, eBPF hands it back to the host OS for standard NAT and routing. It only optimizes intra-cluster traffic."
        else:
            target_data = self.ebpf_endpoint_map[target_ip]
            
            if scenario == "1":
                # Simulated ARP Interception
                flow.append(f"1. [Pod-A OS]: Initiating connection to {target_ip}. Generates ARP Request.")
                flow.append("2. [eBPF TC Hook]: Intercepts ARP Broadcast at Pod-A's veth interface.")
                flow.append(f"3. [Kernel eBPF Map]: Look up target {target_ip} -> Found MAC {target_data['mac']}.")
                flow.append("4. [eBPF Program]: Modifies frame in-place to construct ARP Reply.")
                flow.append("5. [eBPF Program]: Returns 'XDP_TX' / 'TC_ACT_SHOT'. Reply injected directly into Pod-A.")
                flow.append("6. [Linux Bridge]: Avoided. Broadcast storm eliminated.")
                
                action = "eBPF ARP SYNTHESIS (Local Proxy)"
                insight = "Inside a massive GKE cluster with 5,000 nodes, ARP broadcasts would cripple the network. Cilium eBPF mathematically prevents ARP from ever leaving the Pod namespace, isolating the noise entirely."
                
                frame = {
                    "stage": "eBPF BPF_MAP_TYPE_HASH Lookup",
                    "operation": f"Map Get: Key({target_ip}) -> Value({target_data['mac']})",
                    "result": "ARP Reply Synthesized in Kernel Space"
                }
                frames.append(frame)

            elif scenario == "2":
                # Direct L3 Packet Redirection (Bypassing IP Stack)
                flow.append(f"1. [Pod-A OS]: ARP resolved. Transmitting IP packet to {target_ip}.")
                flow.append("2. [eBPF TC Hook]: Intercepts L3 packet at ingress.")
                flow.append(f"3. [Kernel eBPF Map]: Target {target_ip} is on local node ({target_data['node']}).")
                flow.append(f"4. [eBPF Program]: Rewriting L2 Dest MAC to {target_data['mac']}.")
                flow.append(f"5. [eBPF Program]: Executing 'bpf_redirect_peer({target_data['veth']})'.")
                flow.append(f"6. [Dataplane]: Packet instantly teleported to Pod-B's interface.")
                flow.append("7. [iptables/netfilter]: Completely bypassed. Zero rules evaluated.")
                
                action = "eBPF DIRECT PEER REDIRECT (Zero-Copy)"
                insight = "This is why Google uses eBPF for Dataplane V2. By calling `bpf_redirect_peer`, the kernel moves the packet directly from Pod A's network namespace to Pod B's network namespace without ever traversing the node's IP routing tables or iptables. It is the lowest possible latency achievable in a software defined network."
                
                frame = {
                    "stage": "eBPF Fast Path Redirection",
                    "operation": "bpf_redirect_peer()",
                    "result": f"Packet routed to {target_data['veth']} without Linux bridging"
                }
                frames.append(frame)

        self.cilium_state = {
            "target": target_ip,
            "scenario": scenario,
            "flow": flow,
            "frames": frames,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.cilium_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AW: KUBERNETES CILIUM eBPF ARP-LESS ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] KERNEL eBPF ENDPOINT MAP (CLUSTER STATE):")
        for ip, data in self.ebpf_endpoint_map.items():
            print(f"     -> {ip:<12} : {data['mac']} | Node: {data['node']} | Iface: {data['veth']}")
        print("-" * width)
        
        print(" [i] eBPF INGRESS HOOK SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        if state['frames']:
            print(" [!] BPF KERNEL OPERATIONS:")
            time.sleep(0.3)
            for frame in state['frames']:
                print(f"\n     [{frame['stage']}]")
                print(f"     Execution : {frame['operation']}")
                print(f"     Outcome   : {frame['result']}")
                time.sleep(0.4)
        
        print("\n" + "-" * width)
        print(f"     -> Dataplane Action : [ {state['action']} ]")
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = CiliumeBPFEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AW_KUBERNETES_CILIUM_EBPF_ARPLESS INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select eBPF Interception Scenario (Pod-A -> Pod-B [10.0.1.51]):")
            print("    1. Pod OS generates ARP Request (eBPF Local Proxy Synthesis)")
            print("    2. Pod OS transmits IP Packet (eBPF Fast-Path Direct Redirect)")
            
            choice = input("    Select scenario (1/2) [Default: 2] : ").strip() or "2"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice not in ["1", "2"]:
                raise ValueError("Selection Error: Please choose 1 or 2.")
            
            engine.execute_ebpf_datapath("10.0.1.51", choice)
            engine.render_ui()
            
            break # Auto-break for flow
            
        except ValueError as ve:
            print(f"\n[X] INTERCEPT TRIGGERED:\n    {ve}")
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()