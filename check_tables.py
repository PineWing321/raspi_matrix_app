# check_tables.py
import sqlite3

conn = sqlite3.connect("shift_data.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables found:", tables)
conn.close()
