from threading import Event

# Global state
render_ack_event = Event()
total_parts = 0
total_rejects = 0

def update_current_parts_and_rejects(parts, rejects):
    global total_parts
    global total_rejects
    try:
        total_parts = int(parts)
        total_rejects = int(rejects)
    except (ValueError, TypeError):
        print(f"[ERROR] Invalid parts/rejects: {parts}, {rejects}")

def grab_total_parts():
    global total_parts
    return total_parts

def grab_total_rejects():
    global total_rejects
    return total_rejects
