import sqlite3


conn = sqlite3.connect("company.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT,
    salary INTEGER
)
""")

cursor.execute("""
INSERT INTO employees
(name, department, salary)
VALUES
('Rahul', 'IT', 60000),
('Ananya', 'HR', 50000),
('Vikram', 'Finance', 70000)
""")

conn.commit()

conn.close()

print("Database initialized")