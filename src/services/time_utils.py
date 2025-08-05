from datetime import datetime

def parse_time(time_str):
    if time_str:
        return datetime.strptime(time_str, "%H:%M").time()
    return None

def time_to_str(time_obj):
    return time_obj.strftime("%H:%M") if time_obj else None

def get_current_html_time() -> str:
    now = datetime.now()
    return f"{now:%H:%M}"
