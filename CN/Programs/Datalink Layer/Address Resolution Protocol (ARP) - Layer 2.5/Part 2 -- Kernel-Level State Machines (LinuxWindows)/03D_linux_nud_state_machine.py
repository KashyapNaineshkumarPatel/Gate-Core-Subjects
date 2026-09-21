"""
Core Logic: Basic networking tutorials suggest that an ARP entry is either "in the cache" 
or "not in the cache." In reality, modern OS kernels (like Linux and Windows) use a highly 
complex Neighbour Unreachability Detection (NUD) state machine.

An ARP entry in the Linux kernel moves through specific transitional states:
- INCOMPLETE: The OS has sent an ARP Request and is waiting for a reply.
- REACHABLE: The OS received a reply. The MAC is known and trusted.
- STALE: The 'reachable' timer (e.g., 30s) expired. The OS keeps the MAC in memory to 
  avoid broadcasting, but marks it as untrusted.
- DELAY: An application wants to send data to a STALE entry. The OS sends the packet 
  using the old MAC, but starts a short delay timer waiting for proof of reachability.
- PROBE: The delay timer expired without proof. The OS actively sends Unicast ARP 
  Requests to the old MAC to verify it's still alive.
- FAILED: No response to probes. The MAC is deleted and packets are dropped.

Crucially, the OS can transition an entry from STALE back to REACHABLE without ever 
sending an ARP request, if a higher-layer protocol (like a TCP ACK) confirms two-way 
reachability.
"""

import sys
import shutil
import time
from typing import Any, Dict

class LinuxNUDStateMachineEngine:
    nud_state: Dict[str, Any]
    current_state: str

    def __init__(self) -> None:
        # Initial Kernel State
        self.current_state = "NONE"
        self.nud_state = {}

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 105)

    def validate_event(self, event_choice: str) -> str:
        choice = event_choice.strip()
        valid_events = {
            "1": "TX_DATA",
            "2": "RX_ARP_REPLY",
            "3": "TIMEOUT",
            "4": "UPPER_LAYER_CONFIRM"
        }
        if choice not in valid_events:
            raise ValueError("Event Error: Select a valid trigger event (1-4).")
        return valid_events[choice]

    def execute_state_transition(self, event: str) -> None:
        """Simulates the Linux kernel NUD (Neighbour Unreachability Detection) state machine."""
        
        prev_state = self.current_state
        action = ""
        insight = ""
        
        if event == "TX_DATA":
            if self.current_state == "NONE" or self.current_state == "FAILED":
                self.current_state = "INCOMPLETE"
                action = "Kernel creates new entry. Queues application packet. Transmits Broadcast ARP Request."
                insight = "The packet is buffered. If the queue overflows, older packets are dropped."
            elif self.current_state == "STALE":
                self.current_state = "DELAY"
                action = "Kernel transmits packet using cached MAC, but starts DELAY timer."
                insight = "Optimistic transmission: We assume the MAC is still good to avoid latency, but we must verify."
            elif self.current_state in ["INCOMPLETE", "REACHABLE", "DELAY", "PROBE"]:
                action = "Kernel transmits packet (or queues it if INCOMPLETE)."
                insight = "State remains unchanged during standard data transmission in these states."
                
        elif event == "RX_ARP_REPLY":
            if self.current_state in ["INCOMPLETE", "PROBE", "DELAY"]:
                self.current_state = "REACHABLE"
                action = "Valid ARP Reply received. Kernel updates MAC and flushes packet queue."
                insight = "The entry is now fully trusted for the duration of the base_reachable_time (default ~30s)."
            else:
                action = "Unsolicited ARP Reply received. Kernel updates MAC if entry exists."
                self.current_state = "REACHABLE"
                
        elif event == "TIMEOUT":
            if self.current_state == "REACHABLE":
                self.current_state = "STALE"
                action = "Reachable timer expired. Entry remains in memory but is marked untrusted."
                insight = "STALE entries do not actively send ARPs. They just sit passively to save network bandwidth."
            elif self.current_state == "DELAY":
                self.current_state = "PROBE"
                action = "Delay timer expired. Kernel actively sends Unicast ARP Request."
                insight = "No upper-layer confirmation arrived, so the OS must manually verify the MAC."
            elif self.current_state == "PROBE":
                self.current_state = "FAILED"
                action = "Max probes sent with no reply. Entry invalidated."
                insight = "The kernel will now drop the queued packets and return an error to the application."
            elif self.current_state == "INCOMPLETE":
                self.current_state = "FAILED"
                action = "ARP Request timed out. No reply received."
                insight = "Target is genuinely offline or unreachable."
            else:
                action = "Timer event ignored for current state."
                
        elif event == "UPPER_LAYER_CONFIRM":
            if self.current_state in ["STALE", "DELAY", "PROBE"]:
                self.current_state = "REACHABLE"
                action = "TCP ACK or similar L4 payload received. Kernel bypasses ARP entirely."
                insight = "If TCP receives an ACK, two-way L2 connectivity is mathematically guaranteed. Sending an ARP would be a waste of bandwidth."
            else:
                action = "Upper layer confirm logged, but no state change required."

        self.nud_state = {
            "prev_state": prev_state,
            "event": event,
            "new_state": self.current_state,
            "action": action,
            "insight": insight if insight else "State machine transition executed."
        }

    def render_ui(self) -> None:
        time.sleep(0.3)
        width = self.get_terminal_width()
        state = self.nud_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 04D: LINUX NUD STATE MACHINE ENGINE ".center(width))
        print("=" * width)
        
        print(" [+] KERNEL EVENT TRIGGER:")
        print(f"     -> Previous NUD State : [ {state['prev_state']} ]")
        print(f"     -> Event Triggered    : {state['event']}")
        print("-" * width)
        
        print(" [i] STATE MACHINE TRANSITION:")
        time.sleep(0.3)
        print(f"     -> New NUD State      : [ {state['new_state']} ]")
        time.sleep(0.2)
        print(f"     -> Kernel Action      : {state['action']}")
        print("-" * width)
        
        print(f" [!] ARCHITECTURAL KERNEL INSIGHT:")
        time.sleep(0.2)
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")


def interactive_loop() -> None:
    engine = LinuxNUDStateMachineEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 04D_LINUX_NUD_STATE_MACHINE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    while True:
        try:
            print(f"\n[?] Current Kernel State: [ {engine.current_state} ]")
            print("    Trigger a System Event:")
            print("      1: Application sends IP packet (TX_DATA)")
            print("      2: Network receives ARP Reply  (RX_ARP_REPLY)")
            print("      3: Kernel Timer Expires        (TIMEOUT)")
            print("      4: TCP ACK Received            (UPPER_LAYER_CONFIRM)")
            
            event_in = input("    Choice (1-4) [Default: 1]: ").strip() or "1"
            if event_in.lower() in ['quit', 'exit']: sys.exit(0)
            
            event = engine.validate_event(event_in)
            
            engine.execute_state_transition(event)
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