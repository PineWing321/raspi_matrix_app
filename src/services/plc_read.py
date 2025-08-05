from pycomm3 import LogixDriver

print("Trying to connect to PLC at 192.168.1.60...")

try:
    with LogixDriver('192.168.1.60') as plc:
        if plc.connected:
            print("✅ Successfully connected to PLC!")
        else:
            print("❌ Failed to connect.")
except Exception as e:
    print(f"❌ Connection error: {e}")
