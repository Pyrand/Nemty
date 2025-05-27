import sqlite3

conn = sqlite3.connect("destinations.db")
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS users;")
conn.commit()
conn.close()
