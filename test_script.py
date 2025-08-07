#pip install psycopg2-binary
import os
import sys
import random
import psycopg2

from dotenv import load_dotenv

load_dotenv()

# Настройки подключения к базе данных
DB_NAME = os.getenv("TEST_POSTGRES_DB")
DB_USER = os.getenv("TEST_POSTGRES_USER")
DB_PASSWORD = os.getenv("TEST_POSTGRES_PASSWORD")
DB_HOST = os.getenv("TEST_POSTGRES_HOST")
DB_PORT = os.getenv("TEST_POSTGRES_PORT")

# Соединение с базой данных
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
cur = conn.cursor()

# Главная функция обработки команд
def main(command):
    if command == "create_table":
        drop_ram_metrics_table()
        create_ram_metrics_table()
    elif command == "add_positive_data":
        insert_random_data(min_val=0, max_val=80, iterations=3)
    elif command == "add_negative_data":
        insert_random_data(min_val=80, max_val=110, iterations=2)
    else:
        print("Unknown command.")

# Удаление таблицы RAMMetrics
def drop_ram_metrics_table():
    cur.execute("DROP TABLE IF EXISTS RAMMetrics;")
    conn.commit()
    print("Old table dropped.")

# Функция создания таблицы RAMMetrics
def create_ram_metrics_table():
    cur.execute("""
        CREATE TABLE RAMMetrics (
            id SERIAL PRIMARY KEY,
            server_name VARCHAR(255),
            ram FLOAT,
            created_dt TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    print("Table created successfully with timestamp column!")

# Функция вставки случайных данных в таблицу
def insert_random_data(min_val, max_val, iterations):
    data_points = [(f"test_server_{i}", random.uniform(min_val, max_val)) for i in range(iterations)]
    values = ", ".join([f"('{server}', {ram:.2f})" for server, ram in data_points])
    sql = f"INSERT INTO RAMMetrics(server_name, ram) VALUES {values};"
    cur.execute(sql)
    conn.commit()
    print(f"Inserted {len(data_points)} rows of data into the table.")

# Выполнение скрипта
if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].strip()
        main(command)
    else:
        print("Please provide a valid command (create_table/add_positive_data/add_negative_data)")

# Закрытие соединения с базой данных
cur.close()
conn.close()