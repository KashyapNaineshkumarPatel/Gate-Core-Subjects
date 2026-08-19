import sys
import re
import shutil
import time
import random
from typing import Any, Dict, List, Tuple

class IPIDIdleScannerEngine:
    scanner_state: Dict[str, Any]

    def __init__(self) -> None:
        # State Management Engine
        self.scanner_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 100)

    def validate_inputs(self, zombie_ip: str, target_ip: str, port_in: str, zombie_os: str, target_state: str) -> Tuple[str, str, int, bool, bool]:
        # 1. IP Input Validation
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        
        for ip, label in [(zombie_ip, "Zombie IP"), (target_ip, "Target IP")]:
            match = re.match(ip_pattern, ip)
            if not match:
                raise ValueError(f"Syntax Error: {label} format invalid (e.g., 192.168.1.50)")
            for idx, octet_str in enumerate(match.groups()):
                if int(octet_str) > 255:
                    raise ValueError(f"System Error: {label} Octet {idx+1} ({octet_str}) exceeds 8-bit limit.")
                    
        if zombie_ip == target_ip:
            raise ValueError("Logical Error: Zombie IP and Target IP cannot be the same for an Idle Scan.")

        # 2. Port Validation
        try:
            port = int(port_in)
        except ValueError as exc:
            raise ValueError("Type Error: Target Port must be an integer.") from exc
            
        if port < 1 or port > 65535:
            raise ValueError(f"Architecture Error: TCP/UDP ports are 16-bit. Valid range is 1-65535. You entered {port}.")

        # 3. OS & State Validation
        z_os = zombie_os.strip().lower()
        legacy_values = {'legacy', 'l', 'predictable'}
        modern_values = {'modern', 'm', 'random'}
        if z_os in legacy_values:
            is_predictable = True
        elif z_os in modern_values:
            is_predictable = False
        else:
            raise ValueError("Type Error: Zombie OS must be 'legacy' or 'modern'.")
            
        t_state = target_state.strip().lower()
        open_values = {'open', 'o'}
        closed_values = {'closed', 'c'}
        if t_state in open_values:
            is_open = True
        elif t_state in closed_values:
            is_open = False
        else:
            raise ValueError("Type Error: Target port state must be 'open' or 'closed'.")

        return zombie_ip, target_ip, port, is_predictable, is_open

    def simulate_idle_scan(self, zombie: str, target: str, port: int, is_predictable: bool, is_open: bool) -> None:
        """The Stealth Scanning Mechanic: Exploits IP ID increments to deduce port states."""

        base_id = random.randint(10000, 60000)
        scan_log: List[Dict[str, str]] = []

        # Step 1: Probe the Zombie
        scan_log = [{
            "step": "1. INITIAL PROBE",
            "action": f"Attacker sends SYN/ACK to Zombie ({zombie}).",
            "result": f"Zombie replies with RST. IP ID = {base_id}."
        }]

        common_probe = {
            "step": "2. SPOOFED SYN",
            "action": f"Attacker sends SYN to Target ({target}:{port}), spoofing source as Zombie.",
        }

        # Determine Zombie's IP ID behavior
        if not is_predictable:
            # Modern OS: Randomizes IP ID for every packet to prevent this exact attack
            scan_log.extend([
                common_probe | {"result": "Target processes the spoofed packet."},
                {
                    "step": "3. TARGET REACTION",
                    "action": "Target responds directly to Zombie.",
                    "result": "Zombie processes packet (silently drops or RSTs). Modern OS randomizes next ID."
                },
            ])
            final_id = random.randint(10000, 60000)
            insight = "FAILURE: The Zombie OS uses randomized IP IDs. The delta is unpredictable. The Idle Scan failed."
            delta = "Random"
            conclusion = "Unknown (Zombie is immune)"

        else:
            # Legacy OS: Predictable +1 Increment
            current_zombie_id = base_id
            scan_log.extend([
                common_probe | {"result": "Target believes the packet came from the Zombie."},
            ])

            if is_open:
                scan_log.append({
                    "step": "3. TARGET REACTION",
                    "action": "Target port is OPEN. Target sends SYN/ACK to Zombie.",
                    "result": f"Zombie didn't expect a SYN/ACK. It replies with RST. Zombie IP ID increments to {current_zombie_id + 1}."
                })
                current_zombie_id += 1
            else:
                scan_log.append({
                    "step": "3. TARGET REACTION",
                    "action": "Target port is CLOSED. Target sends RST to Zombie.",
                    "result": "Zombie ignores unsolicited RST. It sends nothing. Zombie IP ID remains unchanged."
                })

            # Step 4: Final Probe increments it by 1 regardless (since we are pinging it)
            final_id = current_zombie_id + 1

            delta = final_id - base_id
            if delta == 2:
                insight = f"SUCCESS: IP ID Delta is 2 ({base_id} -> {final_id}). The Zombie sent a packet to the Target, proving the port is OPEN."
                conclusion = f"Port {port} is OPEN."
            else:
                insight = f"SUCCESS: IP ID Delta is 1 ({base_id} -> {final_id}). The Zombie sent nothing to the Target, proving the port is CLOSED."
                conclusion = f"Port {port} is CLOSED."

        scan_log.append({
            "step": "4. FINAL PROBE",
            "action": "Attacker sends SYN/ACK to Zombie again.",
            "result": f"Zombie replies with RST. IP ID = {final_id}."
        })

        # Update State Tree
        self.scanner_state = {
            "zombie": zombie,
            "target": target,
            "port": port,
            "is_predictable": is_predictable,
            "log": scan_log,
            "insight": insight,
            "delta": delta,
            "conclusion": conclusion
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.3) 
        width = self.get_terminal_width()
        state = self.scanner_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 02G: IP ID IDLE SCANNER (ZOMBIE EXPLOIT) ".center(width))
        print("=" * width)
        
        print(f" [+] Zombie Host      : {state['zombie']} (Predictable IP ID: {state['is_predictable']})")
        print(f" [+] Target Host      : {state['target']} (Port {state['port']})")
        print("-" * width)
        
        print(" [i] ATTACK TRAVERSAL LOG (STEALTH MODE):")
        for entry in state['log']:
            print(f"\n     {entry['step']}")
            print(f"     -> {entry['action']}")
            print(f"     -> {entry['result']}")
            # Micro-throttle for effect
            time.sleep(0.2)
            
        print("-" * width)
        
        print(" [!] MATHEMATICAL DEDUCTION:")
        print(f"     -> IP ID Delta : {state['delta']}")
        print(f"     -> Conclusion  : {state['conclusion']}")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = IPIDIdleScannerEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 02G_IP_ID_IDLE_SCANNER INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            print("\n[?] Enter Stealth Scan Parameters:")
            zombie_in = input("    Zombie IP                 : ").strip()
            if zombie_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not zombie_in: continue
            
            target_in = input("    Target IP                 : ").strip()
            port_in = input("    Target Port (e.g., 443)   : ").strip()
            z_os_in = input("    Zombie OS (Legacy/Modern) : ").strip()
            t_state_in = input("    Simulate Target Port (Open/Closed): ").strip()
                
            zombie, target, port, is_predictable, is_open = engine.validate_inputs(zombie_in, target_in, port_in, z_os_in, t_state_in)
            engine.simulate_idle_scan(zombie, target, port, is_predictable, is_open)
            engine.render_ui()
            
        except ValueError as ve:
            print(f"\n[X] INTERCEPT TRIGGERED:\n    {ve}")
        except KeyboardInterrupt:
            print("\n\n[!] Interrupt signal received. Safely spinning down engine...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[X] CRITICAL SYSTEM FAULT: {e}")

if __name__ == "__main__":
    interactive_loop()