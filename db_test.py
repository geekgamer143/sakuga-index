import sqlite3   # built into Python — no install needed

# 1. CONNECT to the database file (it already exists from schema.sql)
conn = sqlite3.connect("sakuga.db")

# A "cursor" is the object you use to run SQL statements
cursor = conn.cursor()

# 2. EXECUTE an insert. The ? is a placeholder — we'll explain why below.
cursor.execute(
    "INSERT OR IGNORE INTO studios (name) VALUES (?)",
    ("ufotable",)
)

# 3. COMMIT — make the change permanent
conn.commit()

# Now read it back to prove it landed
cursor.execute("SELECT * FROM studios")
rows = cursor.fetchall()   # get all matching rows
print("Studios in the database:")
for row in rows:
    print(row)

# 4. CLOSE the connection
conn.close()