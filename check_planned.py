# check_planned.py
import sqlite3

conn = sqlite3.connect("shift_data.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM planned_shifts ORDER BY id DESC LIMIT 1")
row = cursor.fetchone()
print("Most recent planned shift:", row)

conn.close()
