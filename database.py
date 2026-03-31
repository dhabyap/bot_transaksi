import sqlite3
from datetime import datetime

DB_NAME = "finance_bot.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tipe TEXT,
            item TEXT,
            nominal REAL,
            kategori TEXT,
            timestamp TEXT
        )
    ''')
    
    # Create inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            nama_barang TEXT,
            kuantitas INTEGER,
            status TEXT,
            timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_transaction(user_id, tipe, item, nominal, kategori):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO transactions (user_id, tipe, item, nominal, kategori, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, tipe, item, nominal, kategori, timestamp))
    conn.commit()
    conn.close()

def insert_inventory(user_id, nama_barang, kuantitas, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO inventory (user_id, nama_barang, kuantitas, status, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, nama_barang, kuantitas, status, timestamp))
    conn.commit()
    conn.close()

def get_monthly_report(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    current_month = datetime.now().strftime("%Y-%m")
    
    cursor.execute('''
        SELECT tipe, SUM(nominal) 
        FROM transactions 
        WHERE timestamp LIKE ? AND user_id = ?
        GROUP BY tipe
    ''', (f"{current_month}%", user_id))
    
    results = cursor.fetchall()
    conn.close()
    
    report = {"pemasukan": 0, "pengeluaran": 0}
    for tipe, total in results:
        if tipe.lower() == "pemasukan":
            report["pemasukan"] = total
        elif tipe.lower() == "pengeluaran":
            report["pengeluaran"] = total
            
    return report
