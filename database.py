import os
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "finance_bot")

def get_base_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def init_db():
    # Buat database jika belum ada
    base_conn = get_base_connection()
    cursor = base_conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    base_conn.commit()
    cursor.close()
    base_conn.close()

    # Buat tabel
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            tipe VARCHAR(50),
            item VARCHAR(255),
            nominal DOUBLE,
            kategori VARCHAR(100),
            timestamp DATETIME
        )
    ''')
    
    # Create inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            nama_barang VARCHAR(255),
            kuantitas INT,
            status VARCHAR(50),
            timestamp DATETIME
        )
    ''')

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            username VARCHAR(255),
            language_code VARCHAR(10),
            first_seen DATETIME,
            last_active DATETIME,
            message_count INT DEFAULT 0
        )
    ''')

    # Create chat_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            message TEXT,
            timestamp DATETIME
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()


def upsert_user(user):
    """Simpan atau update data user setiap kali ada pesan masuk."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = '''
        INSERT INTO users (user_id, first_name, last_name, username, language_code, first_seen, last_active, message_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
        ON DUPLICATE KEY UPDATE
            first_name = VALUES(first_name),
            last_name = VALUES(last_name),
            username = VALUES(username),
            language_code = VALUES(language_code),
            last_active = VALUES(last_active),
            message_count = message_count + 1
    '''
    cursor.execute(sql, (
        user.id,
        user.first_name,
        getattr(user, 'last_name', None),
        getattr(user, 'username', None),
        getattr(user, 'language_code', None),
        now,
        now
    ))
    conn.commit()
    cursor.close()
    conn.close()

def insert_transaction(user_id, tipe, item, nominal, kategori):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = '''
        INSERT INTO transactions (user_id, tipe, item, nominal, kategori, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
    '''
    cursor.execute(sql, (user_id, tipe, item, nominal, kategori, timestamp))
    conn.commit()
    cursor.close()
    conn.close()

def insert_inventory(user_id, nama_barang, kuantitas, status):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = '''
        INSERT INTO inventory (user_id, nama_barang, kuantitas, status, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    '''
    cursor.execute(sql, (user_id, nama_barang, kuantitas, status, timestamp))
    conn.commit()
    cursor.close()
    conn.close()

def get_monthly_report(user_id=None, month_str=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    if not month_str:
        month_str = datetime.now().strftime("%Y-%m")
    
    if user_id:
        sql = '''
            SELECT tipe, SUM(nominal) as total
            FROM transactions 
            WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s AND user_id = %s
            GROUP BY tipe
        '''
        cursor.execute(sql, (month_str, user_id))
    else:
        sql = '''
            SELECT tipe, SUM(nominal) as total
            FROM transactions 
            WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s
            GROUP BY tipe
        '''
        cursor.execute(sql, (month_str,))
        
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    report = {"pemasukan": 0, "pengeluaran": 0}
    for row in results:
        tipe = row['tipe'].lower()
        if tipe == "pemasukan":
            report["pemasukan"] = row['total']
        elif tipe == "pengeluaran":
            report["pengeluaran"] = row['total']
            
    return report

def get_transactions_by_month(month_str, user_id=None):
    """
    Mengambil transaksi untuk bulan tertentu (format YYYY-MM) diurutkan dari yang terbaru
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    if user_id:
        sql = '''
            SELECT * FROM transactions 
            WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s AND user_id = %s
            ORDER BY timestamp DESC
        '''
        cursor.execute(sql, (month_str, user_id))
    else:
        sql = '''
            SELECT * FROM transactions 
            WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s
            ORDER BY timestamp DESC
        '''
        cursor.execute(sql, (month_str,))
        
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def delete_transaction(tx_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM transactions WHERE id = %s AND user_id = %s"
    cursor.execute(sql, (tx_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0

def delete_inventory(inv_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM inventory WHERE id = %s AND user_id = %s"
    cursor.execute(sql, (inv_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0

def update_transaction(tx_id, user_id, tipe, item, nominal, kategori):
    conn = get_connection()
    cursor = conn.cursor()
    sql = '''
        UPDATE transactions 
        SET tipe = %s, item = %s, nominal = %s, kategori = %s 
        WHERE id = %s AND user_id = %s
    '''
    cursor.execute(sql, (tipe, item, nominal, kategori, tx_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0

def update_inventory(inv_id, user_id, nama_barang, kuantitas, status):
    conn = get_connection()
    cursor = conn.cursor()
    sql = '''
        UPDATE inventory 
        SET nama_barang = %s, kuantitas = %s, status = %s 
        WHERE id = %s AND user_id = %s
    '''
    cursor.execute(sql, (nama_barang, kuantitas, status, inv_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0

def get_history(user_id, limit=10):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get combined history of transactions and inventory
    sql = '''
        (SELECT 'T' as prefix, id, tipe as label, item, nominal as val, timestamp 
         FROM transactions WHERE user_id = %s)
        UNION ALL
        (SELECT 'I' as prefix, id, status as label, nama_barang as item, kuantitas as val, timestamp 
         FROM inventory WHERE user_id = %s)
        ORDER BY timestamp DESC
        LIMIT %s
    '''
    cursor.execute(sql, (user_id, user_id, limit))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def get_all_users():
    """Ambil semua data user yang pernah menggunakan bot."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users ORDER BY last_active DESC')
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def insert_chat_log(user_id, message_text):
    """Log incoming user chat to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = '''
        INSERT INTO chat_logs (user_id, message, timestamp)
        VALUES (%s, %s, %s)
    '''
    cursor.execute(sql, (user_id, message_text, timestamp))
    conn.commit()
    cursor.close()
    conn.close()
