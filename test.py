import sqlite3
import csv

# 1. Conectar y crear tablas
conn = sqlite3.connect('mi_db.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    product TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
)
''')

# 2. Datos de ejemplo (desnormalizados, como vendrían para un CSV)
datos_originales = [
    {"customer": "Ana", "product": "Laptop"},
    {"customer": "Luis", "product": "Mouse"},
    {"customer": "Ana", "product": "Teclado"},
]

# 3. Mapa para guardar la relación nombre_cliente -> id_real
customer_map = {}

# 4. Insertar clientes únicos y guardar sus IDs generados
clientes_unicos = set(d["customer"] for d in datos_originales)
for nombre in clientes_unicos:
    cursor.execute("INSERT INTO customers (name) VALUES (?)", (nombre,))
    customer_map[nombre] = cursor.lastrowid  # PK generada (int)

# 5. Insertar órdenes usando la FK desde el mapa
for dato in datos_originales:
    customer_id = customer_map[dato["customer"]]
    cursor.execute(
        "INSERT INTO orders (customer_id, product) VALUES (?, ?)",
        (customer_id, dato["product"])
    )

conn.commit()

# 6. Exportar a CSV la tabla orders (ya con FK resuelta)
with open('orders.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["id", "customer_id", "product"])
    cursor.execute("SELECT * FROM orders")
    writer.writerows(cursor.fetchall())



conn.close()
