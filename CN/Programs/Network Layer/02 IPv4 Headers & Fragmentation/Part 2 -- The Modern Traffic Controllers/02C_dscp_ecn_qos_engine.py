import sys
import shutil
import time
from typing import Any, Dict, Tuple

class IPv4QoSEngine:
    qos_state: Dict[str, Any]

    def __init__(self) -> None:
        # State Management Engine
        self.qos_state = {}

    def get_terminal_width(self) -> int:
        # Dynamic Scaled Rendering
        return min(shutil.get_terminal_size().columns, 90)

    def validate_inputs(self, dscp_input: str, ecn_input: str) -> Tuple[int, int]:
        # 1. DSCP Validation
        try:
            dscp_val = int(dscp_input)
        except ValueError as exc:
            raise ValueError("Type Error: DSCP value must be an integer.") from exc
            
        if dscp_val < 0 or dscp_val > 63:
            raise ValueError(
                f"Architecture Error: DSCP is a 6-bit field. "
                f"The maximum physical value is 63 (binary 111111). You entered {dscp_val}."
            )

        # 2. ECN Validation
        try:
            ecn_val = int(ecn_input)
        except ValueError as exc:
            raise ValueError("Type Error: ECN value must be an integer.") from exc
            
        if ecn_val < 0 or ecn_val > 3:
            raise ValueError(
                f"Architecture Error: ECN is a 2-bit field. "
                f"The maximum physical value is 3 (binary 11). You entered {ecn_val}."
            )

        return dscp_val, ecn_val

    def _get_dscp_profile(self, dscp: int) -> str:
        """Translates raw DSCP decimal into enterprise QoS profiles."""
        if dscp == 0: return "Best Effort (BE) - Default Internet Traffic"
        if dscp == 46: return "Expedited Forwarding (EF) - VoIP / Real-Time Voice"
        if dscp == 34: return "Assured Forwarding (AF41) - Interactive Video"
        if dscp == 10: return "Assured Forwarding (AF11) - Bulk Data Transfers"
        if dscp == 48: return "Class Selector 6 (CS6) - Network Control / Routing Updates"
        return "Custom / Unstandardized Profile"

    def _get_ecn_profile(self, ecn: int) -> str:
        """Translates raw ECN decimal into congestion states."""
        if ecn == 0: return "Non-ECT - Legacy equipment. Drops packets on congestion."
        if ecn == 1: return "ECT(1) - ECN Capable Transport."
        if ecn == 2: return "ECT(0) - ECN Capable Transport."
        if ecn == 3: return "CE (Congestion Encountered) - Router marks this instead of dropping."
        return "Unknown"

    def calculate_tos_byte(self, dscp: int, ecn: int) -> None:
        """The Traffic Prioritization Mechanic: Shifts bits to form the 8-bit ToS byte."""
        # DSCP occupies the 6 most significant bits. ECN occupies the 2 least significant bits.
        # Shift DSCP left by 2 spaces, then use bitwise OR to combine with ECN.
        tos_byte = (dscp << 2) | ecn
        
        dscp_bin = f"{dscp:06b}"
        ecn_bin = f"{ecn:02b}"
        tos_bin = f"{tos_byte:08b}"
        
        # Security & Architecture Insights
        insight = ""
        if dscp == 46 and ecn == 3:
            insight = "CRITICAL: Voice traffic (EF) marked with Congestion Encountered (CE).\n     Expect severe audio jitter. Router queues are overflowing."
        elif dscp == 0:
            insight = "STANDARD: Traffic has no priority. It will be dropped first during network saturation."
        elif ecn == 0:
            insight = "WARNING: Without ECN capability, routers must drop packets (Tail Drop) to signal congestion, halving TCP throughput."
        else:
            insight = "OPTIMIZED: Traffic is classified and ECN-aware, allowing smooth flow control."

        # Update State Tree
        self.qos_state = {
            "dscp_dec": dscp,
            "ecn_dec": ecn,
            "dscp_bin": dscp_bin,
            "ecn_bin": ecn_bin,
            "tos_dec": tos_byte,
            "tos_hex": f"0x{tos_byte:02X}",
            "tos_bin": tos_bin,
            "dscp_desc": self._get_dscp_profile(dscp),
            "ecn_desc": self._get_ecn_profile(ecn),
            "insight": insight
        }

    def render_ui(self) -> None:
        # Asynchronous UI Throttle
        time.sleep(0.2) 
        width = self.get_terminal_width()
        state = self.qos_state
        
        print("\n" + "=" * width)
        print(" [>] MODULE 02C: DSCP & ECN QoS ENGINE ".center(width))
        print("=" * width)
        
        print(" [i] 8-BIT ToS ARCHITECTURE ASSEMBLY:")
        print(f"     -> DSCP (6-bit) : {state['dscp_dec']:<3} | Binary: {state['dscp_bin']}")
        print(f"     -> ECN  (2-bit) : {state['ecn_dec']:<3} | Binary: {state['ecn_bin']}")
        print(f"     -> Final ToS    : {state['tos_dec']:<3} | Binary: {state['tos_bin']} | Hex: {state['tos_hex']}")
        print("-" * width)
        
        print(" [+] QoS Profile Traffic Analysis:")
        print(f"     -> Class  : {state['dscp_desc']}")
        print(f"     -> State  : {state['ecn_desc']}")
        print("-" * width)
        
        print(" [!] ENGINEERING DIAGNOSTIC:")
        print(f"     -> {state['insight']}")
        print("=" * width + "\n")

def interactive_loop() -> None:
    engine = IPv4QoSEngine()
    width = engine.get_terminal_width()
    
    print("\n" + "=" * width)
    print(" 02C_DSCP_ECN_QoS_ENGINE INITIALIZED ".center(width))
    print(" Type 'quit' or press Ctrl+C to safely shut down.".center(width))
    print("=" * width)

    # Graceful Exception Handling Loop
    while True:
        try:
            print("\n[?] Select DSCP QoS Profile (0-63):")
            print("    [0: Best Effort, 10: Bulk Data, 34: Video, 46: VoIP, 48: Network Control]")
            dscp_in = input("    DSCP Value: ").strip()
            
            if dscp_in.lower() in ['quit', 'exit']: sys.exit(0)
            if not dscp_in: continue
            
            print("\n[?] Select ECN State (0-3):")
            print("    [0: Non-ECT, 1/2: ECN Capable, 3: Congestion Encountered]")
            ecn_in = input("    ECN Value : ").strip()
                
            dscp_val, ecn_val = engine.validate_inputs(dscp_in, ecn_in)
            engine.calculate_tos_byte(dscp_val, ecn_val)
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