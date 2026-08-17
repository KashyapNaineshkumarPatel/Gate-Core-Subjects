import sys
import shutil
import time
from typing import Any, Dict

class TTLFingerprintEngine:
    fingerprint_state: Dict[str, Any]

    def __init__(self) -> None:
        # State Management Engine
        self.fingerprint_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 90)

    def validate_ttl(self, ttl_input: str) -> int:
        # Input Bounds Validation & Descriptive Errors
        try:
            received_ttl = int(ttl_input)
        except ValueError as exc:
            raise ValueError("Type Error: The received TTL must be a whole number.") from exc
            
        if received_ttl < 1 or received_ttl > 255:
            if received_ttl == 0:
                raise ValueError(
                    "Physics Error: A received TTL of 0 is impossible in a packet capture. "
                    "When a router decrements a TTL to 0, the packet is instantly dropped and an "
                    "ICMP 'Time Exceeded' message is sent back. It will never reach your NIC."
                )
            raise ValueError(
                f"Architecture Error: TTL is an 8-bit field. "
                f"The physical bounds are 1 to 255. You entered {received_ttl}."
            )
            
        return received_ttl

    def calculate_fingerprint(self, received_ttl: int) -> None:
        """The Reconnaissance Engine: Derives OS and Network Distance based on TTL decay."""
        
        # Step 1: Determine the likely Original TTL
        # Network packets rarely traverse more than 15-20 hops on the modern internet.
        # We round up to the nearest standard OS boundary.
        initial_ttl = 0
        os_guess = "Unknown"
        
        if received_ttl <= 64:
            initial_ttl = 64
            os_guess = "Linux / Unix / MacOS / Android"
        elif received_ttl <= 128:
            initial_ttl = 128
            os_guess = "Windows (NT / 10 / 11 / Server)"
        elif received_ttl <= 255:
            initial_ttl = 255
            os_guess = "Cisco IOS / Enterprise Network Gear"

        # Step 2: Calculate routing hops
        hops_taken = initial_ttl - received_ttl
        
        # Step 3: Security & Network Diagnostics
        insight = ""
        if hops_taken == 0:
            insight = "LOCAL HOST: The TTL has not decayed. This machine is on your exact same LAN (Layer 2)."
        elif hops_taken > 30:
            insight = "ANOMALY DETECTED: A hop count this high usually indicates routing loops or spoofed traffic."
        else:
            insight = f"REMOTE HOST: The packet successfully traversed {hops_taken} Layer 3 routers to reach you."

        # Update State Tree
        self.fingerprint_state = {
            "received_ttl": received_ttl,
            "initial_ttl": initial_ttl,
            "hops_taken": hops_taken,
            "os_guess": os_guess,
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.2) 
        width = self.get_terminal_width()
        state = self.fingerprint_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 02D: TTL OS FINGERPRINTER ".center(width))
        print("=" * width)
        
        print(f" [+] Received TTL      : {state['received_ttl']}")
        print(f" [+] Deduced Start TTL : {state['initial_ttl']} (Nearest OS Boundary)")
        print("-" * width)
        
        print(" [i] RECONNAISSANCE ANALYSIS:")
        print(f"     -> Target OS      : {state['os_guess']}")
        print(f"     -> Distance       : {state['hops_taken']} Hops (Routers Crossed)")
        print("-" * width)
        
        print(" [!] ENGINEERING DIAGNOSTIC:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = TTLFingerprintEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 02D_TTL_OS_FINGERPRINTER INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            print("\n[?] Enter the TTL value from your packet capture (e.g., from Wireshark or Ping):")
            ttl_in = input("    Received TTL (1-255): ").strip()
            
            if ttl_in.lower() in ['quit', 'exit']:
                print("\n[+] Graceful shutdown initiated. Goodbye.")
                sys.exit(0)
            if not ttl_in: continue
                
            valid_ttl = engine.validate_ttl(ttl_in)
            engine.calculate_fingerprint(valid_ttl)
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