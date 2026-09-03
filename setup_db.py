import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Conectar a postgres por defecto
conn_default = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'postgres'),
    dbname='postgres'
)
conn_default.autocommit = True
cur_default = conn_default.cursor()

try:
    cur_default.execute("CREATE DATABASE mantenimiento_predictivo;")
    print("Base de datos creada exitosamente.")
except psycopg2.errors.DuplicateDatabase:
    print("La base de datos ya existe.")

cur_default.close()
conn_default.close()

# Conectar a la nueva base de datos
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'postgres'),
    dbname='mantenimiento_predictivo'
)
cur = conn.cursor()

def run_sql_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    sql_commands = []
    for line in lines:
        if line.strip().startswith('\\c') or line.strip().startswith('CREATE DATABASE'):
            continue
        sql_commands.append(line)
        
    sql_script = "".join(sql_commands)
    cur.execute(sql_script)
    conn.commit()
    print(f"Archivo {filename} ejecutado correctamente.")

try:
    run_sql_file('database/init_db.sql')
    run_sql_file('database/seed_data.sql')
    print("Inicialización completada con éxito.")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
