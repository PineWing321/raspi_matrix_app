from datetime import datetime
from src.db import does_shift_overlap
def validate_shift_times(start_str, end_str,
                         break1_start_str, break1_end_str,
                         lunch_start_str, lunch_end_str,
                         break2_start_str, break2_end_str):
    try:
        start = datetime.fromisoformat(start_str) if start_str else None
        end = datetime.fromisoformat(end_str) if end_str else None
        break1_start = datetime.fromisoformat(break1_start_str) if break1_start_str else None
        break1_end = datetime.fromisoformat(break1_end_str) if break1_end_str else None
        lunch_start = datetime.fromisoformat(lunch_start_str) if lunch_start_str else None
        lunch_end = datetime.fromisoformat(lunch_end_str) if lunch_end_str else None
        break2_start = datetime.fromisoformat(break2_start_str) if break2_start_str else None
        break2_end = datetime.fromisoformat(break2_end_str) if break2_end_str else None
    except ValueError:
        return "Invalid date or time format."

    if not start or not end:
        return "Shift start and end times are required."
    if start >= end:
        return "Shift start time must be before end time."

    # Helper to check break pair logic
    def check_break_pair(b_start, b_end, name):
        if b_start and not b_end:
            return f"{name} start time is set but end time is missing."
        if b_end and not b_start:
            return f"{name} end time is set but start time is missing."
        if b_start and b_end:
            if b_start >= b_end:
                return f"{name} start time must be before end time."
            if b_start < start or b_end > end:
                return f"{name} must be fully within the shift window."
        return None

    for b_start, b_end, name in [
        (break1_start, break1_end, "Break 1"),
        (lunch_start, lunch_end, "Lunch"),
        (break2_start, break2_end, "Break 2"),
    ]:
        msg = check_break_pair(b_start, b_end, name)
        if msg:
            return msg

    # Collect all fully-formed breaks for overlap checking
    breaks = []
    if break1_start and break1_end:
        breaks.append((break1_start, break1_end, "Break 1"))
    if lunch_start and lunch_end:
        breaks.append((lunch_start, lunch_end, "Lunch"))
    if break2_start and break2_end:
        breaks.append((break2_start, break2_end, "Break 2"))

    # Check for overlaps between breaks
    for i in range(len(breaks)):
        for j in range(i + 1, len(breaks)):
            b1_start, b1_end, b1_name = breaks[i]
            b2_start, b2_end, b2_name = breaks[j]
            if b1_end > b2_start and b1_start < b2_end:
                return f"{b1_name} overlaps with {b2_name}."

    return None

def validate_shift(data, editing=False):
    error_msg = validate_shift_times(
        data.get("start"),
        data.get("end"),
        data.get("break1_start"),
        data.get("break1_end"),
        data.get("lunch_start"),
        data.get("lunch_end"),
        data.get("break2_start"),
        data.get("break2_end")
    )

    if error_msg:
        return False, error_msg

    # Overlap check
    from datetime import datetime
    try:
        start = datetime.fromisoformat(data.get("start").replace("Z", "")[:19])
        end = datetime.fromisoformat(data.get("end").replace("Z", "")[:19])
    except:
        return False, "Start or end time format is invalid."

    shift_id = data.get("id") if editing else None
    if does_shift_overlap(start, end, exclude_id=shift_id):
        return False, "This shift overlaps with another existing shift."

    return True, None