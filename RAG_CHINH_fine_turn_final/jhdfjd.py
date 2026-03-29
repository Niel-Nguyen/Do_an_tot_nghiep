import sqlite3
conn = sqlite3.connect('restaurant.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
for row in cursor:
    print(row)
for line in conn.iterdump():
    print(line)
conn.close()