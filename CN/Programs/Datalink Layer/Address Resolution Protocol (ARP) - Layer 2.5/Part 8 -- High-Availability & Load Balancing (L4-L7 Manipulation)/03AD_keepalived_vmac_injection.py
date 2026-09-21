"""
Core Logic: When building High Availability (HA) clusters with Keepalived, two Load 
Balancers (Master and Backup) share a Virtual IP (VIP). 

In a basic setup, if the Master dies, the Backup takes the VIP and broadcasts a 
Gratuitous ARP (GARP) telling the network: "The VIP is now at my physical MAC."
The Flaw: Many legacy clients, firewalls, and strict routers ignore unprompted GARPs. 
Their ARP caches remain stale, sending traffic to the dead Master's MAC until the 
cache naturally times out (which can take hours), causing a massive outage.

The Solution: Virtual MAC (VMAC) Injection via VRRP (Virtual Router Redundancy Protocol).
1. The VIP is permanently bound to a shared, mathematically generated Virtual MAC 
   (e.g., 00:00:5E:00:01:<VRID>).
2. The Client's ARP cache perfectly maps the VIP to this VMAC. It never changes.
3. When the Master dies, the Backup node transitions to Master.
4. The Backup does not need the clients to change their ARP caches. Instead, the 
   Backup injects a frame into the network using the VMAC as the Source MAC.
5. The Physical Switch intercepts this frame. It instantly updates its Layer 2 CAM 
   table, moving the VMAC from the dead Master's physical port to the Backup's port.
6. Failover is instantaneous (sub-second) because we manipulated the Switch's CAM 
   table, completely bypassing the flawed Client ARP caches.
"""

import sys
import shutil
import time
from typing import Any, Dict

class VRRPVMACFailoverEngine:
    vrrp_state: Dict[str, Any]

    def __init__(self) -> None:
        self.vrrp_state = {}
        
        # VRRP / Keepalived Configuration (VRID = 51 -> Hex 33)
        self.vip = "10.100.1.254"
        self.vmac = "00:00:5E:00:01:33"
        
        self.lb1_port = "GigabitEthernet1/1"
        self.lb1_pmac = "00:11:11:11:11:11"
        
        self.lb2_port = "GigabitEthernet1/2"
        self.lb2_pmac = "00:22:22:22:22:22"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def execute_vrrp_failover(self, failover_type: str) -> None:
        """Simulates HA failover physics: Standard GARP vs VRRP VMAC."""
        
        flow = []
        
        # Initial State
        client_arp = {self.vip: self.lb1_pmac if failover_type == "1" else self.vmac}
        switch_cam = {client_arp[self.vip]: self.lb1_port}
        
        flow.append("1. [Steady State]: LB1 is MASTER. LB2 is BACKUP.")
        flow.append(f"   -> Client ARP Cache : {self.vip} maps to {client_arp[self.vip]}")
        flow.append(f"   -> Switch CAM Table : {client_arp[self.vip]} is on {switch_cam[client_arp[self.vip]]}")
        flow.append("2. [Disaster Event]: LB1 motherboard suffers catastrophic failure.")
        flow.append("3. [Keepalived]: LB2 misses 3 VRRP heartbeats. Promotes itself to MASTER.")

        if failover_type == "1":
            # Standard GARP Failover (No VMAC)
            flow.append(f"4. [LB2 OS]: Broadcasts GARP -> '{self.vip} is now at Physical MAC {self.lb2_pmac}'.")
            flow.append("5. [Switch]: Updates CAM table for LB2's physical MAC.")
            flow.append("6. [Client OS]: GARP received... but dropped! (Strict ARP policies / Ignore unprompted).")
            flow.append("7. [Dataplane]: Client continues sending L3 traffic to dead MAC 00:11:11:11:11:11.")
            
            # Outcome State
            switch_cam[self.lb2_pmac] = self.lb2_port
            
            action = "FAILOVER FAILED (Traffic Blackholed)"
            insight = "Without VMACs, failover relies entirely on every client/router on the subnet honoring the GARP broadcast to update their L3-to-L2 mappings. If even one critical router ignores it, traffic blackholes until the cache naturally expires."
        else:
            # VRRP VMAC Failover
            flow.append(f"4. [LB2 OS]: Injects GARP with Source MAC = {self.vmac}.")
            flow.append(f"5. [Switch]: Receives frame. Detects {self.vmac} moved from {self.lb1_port} to {self.lb2_port}.")
            
            # The Magic: CAM Table Update
            del switch_cam[self.vmac]
            switch_cam[self.vmac] = self.lb2_port
            
            flow.append("6. [Switch]: CAM Table instantly overwritten. L2 topology updated.")
            flow.append(f"7. [Client OS]: ARP Cache unchanged. Still sending to {self.vmac}.")
            flow.append("8. [Dataplane]: Switch forwards traffic to LB2. Zero packets dropped.")
            
            action = "FAILOVER SUCCESSFUL (Sub-Second)"
            insight = "VMACs shift the failover burden from L3 (Client ARP) to L2 (Switch CAM). Physical switches are hardcoded in silicon to update their CAM tables instantly when a MAC address moves ports. We manipulate the switch's hardware learning to steer the traffic."

        self.vrrp_state = {
            "type": "Standard GARP (Physical MAC)" if failover_type == "1" else "VRRP (Virtual MAC)",
            "client_arp": client_arp,
            "switch_cam": switch_cam,
            "flow": flow,
            "action": action,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.vrrp_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04AD: KEEPALIVED VRRP VMAC INJECTION ".center(width))
        print("=" * width)
        
        print(f" [+] FAILOVER ARCHITECTURE : {state['type']}")
        print("-" * width)
        
        print(" [i] FAILOVER EXECUTION SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.3)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] POST-FAILOVER TOPOLOGY STATE:")
        time.sleep(0.3)
        print(f"     -> Final Outcome    : [ {state['action']} ]")
        
        print(f"\n     [Client OS ARP Cache (L3 -> L2)]")
        for ip, mac in state['client_arp'].items():
            print(f"     {ip} -> {mac}")
            
        print(f"\n     [Switch CAM Table (L2 -> Physical Port)]")
        for mac, port in state['switch_cam'].items():
            print(f"     {mac} -> {port}")
        
        print("\n" + "-" * width)
        print(f" [!] ARCHITECTURAL ENGINEERING INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = VRRPVMACFailoverEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04AD_KEEPALIVED_VMAC_INJECTION INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Select Keepalived Failover Architecture:")
            print("    1. Standard GARP (Physical MAC Failover - Vulnerable)")
            print("    2. VRRP Virtual MAC (Sub-Second L2 Steering - Enterprise Standard)")
            
            choice = input("    Select architecture (1/2) [Default: 2] : ").strip() or "2"
            if choice.lower() in ['quit', 'exit']: sys.exit(0)
            
            if choice not in ["1", "2"]:
                raise ValueError("Selection Error: Please choose 1 or 2.")
            
            engine.execute_vrrp_failover(choice)
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