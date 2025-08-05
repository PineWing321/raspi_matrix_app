

# plc.py (Refactored for persistent, batched reads)

from pycomm3 import LogixDriver
from src.db import get_bit_from_mock_tags
import random

PLC_IP = "192.168.1.60"
USE_MOCK = False
TAGS = {
    "cycle_on": "MatrixDataTracking.Status.Running",
    "cycle_off": "MatrixDataTracking.Status.Stopped",
    "parts": "MatrixDataTracking.ProductionCounts.Total.ACC",
    "rejects": "MatrixDataTracking.ProductionCounts.Fail.ACC",
    "starved": "MatrixDataTracking.Status.Starved",
    "blocked": "MatrixDataTracking.Status.Blocked",
    "event_flags": "Eventbitvalues",  # ✅ new unified tag
}
# Persistent connection setup
plc = None
if not USE_MOCK:
    try:
        plc = LogixDriver(PLC_IP)
        plc.open()
    except Exception as e:
        print(f"[PLC ERROR] Failed to open connection: {e}")
        plc = None

def mock_read(tag_name):
    if tag_name == "CycleStatus":
        return random.choice([True, False])
    elif tag_name == "TotalParts":
        return random.randint(10, 50)
    elif tag_name == "TotalRejects":
        return random.randint(0, 5)
    elif tag_name == "StopCode":
        return random.choice(["missed_pick", "fence_fault", "none"])
    return None



def get_live_shift_data():
    USE_MOCK = False
    if USE_MOCK:
        value = get_bit_from_mock_tags()
        return {
     
            "cycle_status": value,
            "total_parts": mock_read("TotalParts"),
            "total_rejects": mock_read("TotalRejects"),
            "starved" : False,
            "blocked": True
        }

    if not plc:
        return {"cycle_status": None, "total_parts": 0, "total_rejects": 0}

    try:
        result = plc.read(
            TAGS["cycle_on"],
            TAGS["cycle_off"],
            TAGS["parts"],
            TAGS["rejects"],
            TAGS["blocked"],
            TAGS["starved"]
        )
        print("hello whats up") 
        
        on = result[0].value
        off = result[1].value
        parts = result[2].value
        rejects = result[3].value
        starved = result[5].value
        blocked = result[4].value
        
        if blocked:
            if starved:
                blocked = starved = None
            else:
                print("yeah")
        
        if on and off:
            cycle_status = None
        elif on:
            cycle_status = True
        elif off:
            cycle_status = False
        else:
            cycle_status = None

        return {
            "cycle_status": cycle_status,
            "total_parts": int(parts) if parts is not None else 0,
            "total_rejects": int(rejects) if rejects is not None else 0,
            "starved" : starved,
            "blocked": blocked
        }

    except Exception as e:
        print(f"[PLC ERROR] Failed batch read: {e}")
        return {"cycle_status": None, "total_parts": 0, "total_rejects": 0}


def get_stop_cause():
    USE_MOCK = False
    if USE_MOCK:
        active_causes = ["fence_fault","e-stop"]
        return active_causes

    if not plc:
        return ["other"]

    try:
        result = plc.read(TAGS["event_flags"])
        value = result.value
        if value == 64:
            print("ahajajdshdajhfdjashfasjhfjawhfj")
            return 10
        if value is None:
            return ["other"]

        bit_map = {
            1: "fence_fault",
            2: "e_stop",
            3: "collision",
            4: "sensor_audit_flag",
            5: "missed_pick",
            6: "missed_placement",
            8: "operator_stop",
            9: "quality_stop",
        }
        print("what does the bit_map look like", bit_map)
        print("what does the value look like", value) 
        active_causes = [
            name for bit, name in bit_map.items()
            if value & (1 << bit)
        ]

        if active_causes:
            if len(active_causes) > 1:
                print("⚠️ Multiple stop causes detected:", active_causes)
            return active_causes
        else:
            print("nothing i read got triggered") 
            return ["other"]

    except Exception as e:
        print(f"[PLC ERROR] Failed stop cause read: {e}")
        return ["other"]
