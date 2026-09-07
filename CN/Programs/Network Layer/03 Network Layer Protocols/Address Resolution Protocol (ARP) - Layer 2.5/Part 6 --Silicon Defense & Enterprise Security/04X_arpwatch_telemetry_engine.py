"""
Core Logic: When hardware features like Dynamic ARP Inspection (DAI) are not available 
(e.g., on legacy unmanaged switches, IoT networks, or generic cloud bridges), defenders 
must rely on out-of-band passive telemetry. 'arpwatch' is the industry-standard UNIX 
daemon for this.

ARPwatch places a defender's Network Interface Card (NIC) into Promiscuous Mode, listening 
to all ARP broadcast traffic traversing the subnet. It builds a flat-file database of 
IP-to-MAC mappings over time.

Alerting Logic:
1. NEW STATION: If an IP/MAC pair is seen for the first time, it logs it as a new device.
2. CHANGED ETHERNET ADDRESS: If a known IP address suddenly sends an ARP payload claiming 
   a completely different MAC address, the daemon updates its database and alerts the SOC.
3. FLIP FLOP: If an IP rapidly toggles between two different MAC addresses, this is the 
   classic signature of a Man-in-the-Middle (MitM) cache poisoning race condition.

While ARPwatch cannot stop an attack (it is out-of-band and entirely passive), it provides 
the critical visibility required to detect Layer 2 exploitation on flat networks before 
data exfiltration occurs.
"""

import sys
import shutil
import time
import ipaddress
import re
from typing import Any, Dict

class ArpwatchTelemetryEngine:
    telemetry_state: Dict[str, Any]
    arpwatch_db: Dict[str, str]

    def __init__(self) -> None:
        self.telemetry_state = {}
        # Historical Database of learned IP:MAC pairs (Simulating arp.dat)
        self.arpwatch_db = {
            "10.10.1.1": "00:50:56:11:11:11",  # Known Default Gateway
            "10.10.1.50": "00:50:56:22:22:22"  # Known Production Server
        }

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 110)

    def validate_ip(self, ip_input: str) -> str:
        try:
            ipaddress.IPv4Address(ip_input.strip())
            return ip_input.strip()
        except ValueError:
            raise ValueError("Syntax Error: Invalid IPv4 address format (e.g., 10.10.1.1).")

    def validate_mac(self, mac_input: str) -> str:
        cleaned = re.sub(r'[:\-\.\s]', '', mac_input).upper()
        if len(cleaned) != 12 or not all(c in '0123456789ABCDEF' for c in cleaned):
            raise ValueError("Syntax Error: Invalid MAC format. Expected 12 hex chars.")
        return ":".join([cleaned[i:i+2] for i in range(0, 12, 2)])

    def execute_telemetry_analysis(self, packet_ip: str, packet_mac: str) -> None:
        """Simulates passive ARP anomaly detection via stateful tracking."""
        
        flow = []
        flow.append(f"1. [Arpwatch Daemon]: Promiscuous mode captured ARP broadcast -> IP: {packet_ip}, MAC: {packet_mac}")
        
        if packet_ip not in self.arpwatch_db:
            flow.append("2. [Database Lookup]: IP Address not found in historical arp.dat flat-file.")
            flow.append(f"3. [Telemetry Engine]: Recording new network binding {packet_ip} -> {packet_mac}.")
            
            # Update Database
            self.arpwatch_db[packet_ip] = packet_mac
            
            action = "LOG: NEW STATION DETECTED"
            alert = "LOW (Informational Syslog Generated)"
            insight = "In highly dynamic DHCP environments (like guest Wi-Fi), 'New Station' logs happen constantly and are generally ignored. However, in static datacenter VLANs, an unannounced new station is highly suspicious."
            
        elif self.arpwatch_db[packet_ip] == packet_mac:
            flow.append("2. [Database Lookup]: Match found in arp.dat. Known valid binding.")
            flow.append("3. [Telemetry Engine]: Traffic conforms to historical baseline.")
            
            action = "PASSIVE OK (Known Good Baseline)"
            alert = "NONE (Silently Logged)"
            insight = "Standard operational traffic. The daemon remains silent to prevent alert fatigue in the SOC."
            
        else:
            old_mac = self.arpwatch_db[packet_ip]
            flow.append(f"2. [Database Lookup]: ANOMALY! Known IP {packet_ip} historically maps to {old_mac}.")
            flow.append(f"3. [Telemetry Engine]: Received MAC {packet_mac} strictly violates historical record.")
            flow.append("4. [Alert Pipeline]: Triggering SMTP email and SIEM webhook to Security Operations Center.")
            
            # Update DB to the new MAC (simulating the reality that network caches have now been poisoned)
            self.arpwatch_db[packet_ip] = packet_mac
            
            action = "ALERT: CHANGED ETHERNET ADDRESS / FLIP FLOP"
            alert = "CRITICAL (Syslog, SMTP, SIEM Alert dispatched)"
            insight = "A 'Changed Ethernet Address' or rapid 'Flip Flop' is the absolute hallmark of an ARP Cache Poisoning attack, or a High Availability (HA) firewall failover. The SOC must investigate the MAC OUI immediately to determine if the change is a rogue attacker or an administrative event."

        self.telemetry_state = {
            "ip": packet_ip,
            "mac": packet_mac,
            "flow": flow,
            "action": action,
            "alert": alert,
            "insight": insight
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.telemetry_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04X: ARPWATCH TELEMETRY ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] PASSIVE DATABASE STATE (arp.dat):")
        for ip, mac in self.arpwatch_db.items():
            print(f"     -> {ip:<15} : {mac}")
        print("-" * width)
        
        print(" [i] TELEMETRY ANALYSIS SEQUENCE:")
        for step in state['flow']:
            time.sleep(0.2)
            print(f"     {step}")
        print("-" * width)
        
        print(" [!] SOC NOTIFICATION STATE:")
        time.sleep(0.3)
        print(f"     -> Arpwatch Event   : [ {state['action']} ]")
        print(f"     -> SIEM Alert Level : {state['alert']}")
        
        print("-" * width)
        print(f" [!] ARCHITECTURAL SECURITY INSIGHT:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = ArpwatchTelemetryEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04X_ARPWATCH_TELEMETRY_ENGINE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print("\n[?] Inject intercepted ARP broadcast into Telemetry Daemon:")
            print("    (Tip: Use 10.10.1.1 with MAC DE:AD:BE:EF:00:11 to trigger a Flip Flop spoof alert)")
            
            ip_in = input("    Intercepted Sender IP  [Default: 10.10.1.1]         : ").strip() or "10.10.1.1"
            if ip_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            mac_in = input("    Intercepted Sender MAC [Default: DE:AD:BE:EF:00:11] : ").strip() or "DE:AD:BE:EF:00:11"
            
            packet_ip = engine.validate_ip(ip_in)
            packet_mac = engine.validate_mac(mac_in)
            
            engine.execute_telemetry_analysis(packet_ip, packet_mac)
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