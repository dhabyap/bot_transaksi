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
    try:
        cursor = base_conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        base_conn.commit()
    finally:
        cursor.close()
        base_conn.close()

    # Buat tabel
    conn = get_connection()
    try:
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
                message_count INT DEFAULT 0,
                has_accepted_disclaimer TINYINT(1) DEFAULT 0
            )
        ''')

        # Migration: Tambahkan kolom if not exists (untuk database yang sudah ada)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN has_accepted_disclaimer TINYINT(1) DEFAULT 0")
            conn.commit()
        except:
            pass # Kolom sudah ada
        
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
    finally:
        cursor.close()
        conn.close()


def upsert_user(user):
    """Simpan atau update data user setiap kali ada pesan masuk."""
    conn = get_connection()
    try:
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
    finally:
        cursor.close()
        conn.close()

def get_disclaimer_status(user_id):
    """Cek apakah user sudah menyetujui disclaimer experimental."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT has_accepted_disclaimer FROM users WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        return result['has_accepted_disclaimer'] if result else 0
    finally:
        cursor.close()
        conn.close()

def update_disclaimer_status(user_id, status=1):
    """Update status persetujuan disclaimer user."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET has_accepted_disclaimer = %s WHERE user_id = %s', (status, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def insert_transaction(user_id, tipe, item, nominal, kategori):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = '''
            INSERT INTO transactions (user_id, tipe, item, nominal, kategori, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(sql, (user_id, tipe, item, nominal, kategori, timestamp))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def insert_inventory(user_id, nama_barang, kuantitas, status):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = '''
            INSERT INTO inventory (user_id, nama_barang, kuantitas, status, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        '''
        cursor.execute(sql, (user_id, nama_barang, kuantitas, status, timestamp))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def get_monthly_report(user_id=None, month_str=None):
    conn = get_connection()
    try:
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
        
        report = {"pemasukan": 0, "pengeluaran": 0, "investasi": 0}
        for row in results:
            tipe = row['tipe'].lower()
            if tipe == "pemasukan":
                report["pemasukan"] = row['total']
            elif tipe == "pengeluaran":
                report["pengeluaran"] = row['total']
            elif tipe == "investasi":
                report["investasi"] = row['total']
                
        return report
    finally:
        cursor.close()
        conn.close()

def get_transactions_by_month(month_str, user_id=None):
    """
    Mengambil transaksi untuk bulan tertentu (format YYYY-MM) diurutkan dari yang terbaru
    """
    conn = get_connection()
    try:
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
            
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def delete_transaction(tx_id, user_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "DELETE FROM transactions WHERE id = %s AND user_id = %s"
        cursor.execute(sql, (tx_id, user_id))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        cursor.close()
        conn.close()

def admin_delete_transaction(tx_id):
    """Hapus transaksi manapun (tanpa filter user_id). Digunakan oleh dashboard admin."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "DELETE FROM transactions WHERE id = %s"
        cursor.execute(sql, (tx_id,))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        cursor.close()
        conn.close()

def delete_inventory(inv_id, user_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "DELETE FROM inventory WHERE id = %s AND user_id = %s"
        cursor.execute(sql, (inv_id, user_id))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        cursor.close()
        conn.close()

def update_transaction(tx_id, user_id, tipe, item, nominal, kategori):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = '''
            UPDATE transactions 
            SET tipe = %s, item = %s, nominal = %s, kategori = %s 
            WHERE id = %s AND user_id = %s
        '''
        cursor.execute(sql, (tipe, item, nominal, kategori, tx_id, user_id))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        cursor.close()
        conn.close()

def update_inventory(inv_id, user_id, nama_barang, kuantitas, status):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = '''
            UPDATE inventory 
            SET nama_barang = %s, kuantitas = %s, status = %s 
            WHERE id = %s AND user_id = %s
        '''
        cursor.execute(sql, (nama_barang, kuantitas, status, inv_id, user_id))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        cursor.close()
        conn.close()

def get_history(user_id, limit=10):
    conn = get_connection()
    try:
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
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_all_users():
    """Ambil semua data user yang pernah menggunakan bot."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users ORDER BY last_active DESC')
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_all_user_chat_ids():
    """Ambil semua user_id (chat_id) untuk keperluan broadcast bot."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

def insert_chat_log(user_id, message_text):
    """Log incoming user chat to the database."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = '''
            INSERT INTO chat_logs (user_id, message, timestamp)
            VALUES (%s, %s, %s)
        '''
        cursor.execute(sql, (user_id, message_text, timestamp))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_user_profile(user_id):
    """Fetch user profile details for /profile command."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def get_category_breakdown(month_str, user_id=None):
    """
    Ambil total nominal per kategori untuk tipe 'pengeluaran' saja.
    Digunakan untuk pie chart distribusi pengeluaran.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        if user_id:
            sql = """
                SELECT kategori, SUM(nominal) as total
                FROM transactions
                WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s
                  AND tipe = 'pengeluaran'
                  AND user_id = %s
                GROUP BY kategori
                ORDER BY total DESC
            """
            cursor.execute(sql, (month_str, user_id))
        else:
            sql = """
                SELECT kategori, SUM(nominal) as total
                FROM transactions
                WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s
                  AND tipe = 'pengeluaran'
                GROUP BY kategori
                ORDER BY total DESC
            """
            cursor.execute(sql, (month_str,))

        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_daily_trend(month_str, user_id=None):
    """
    Ambil total nominal per hari untuk setiap tipe transaksi.
    Digunakan untuk line chart tren harian.
    Returns list of {day, tipe, total}.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        if user_id:
            sql = """
                SELECT DAY(timestamp) as day, tipe, SUM(nominal) as total
                FROM transactions
                WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s
                  AND user_id = %s
                GROUP BY DAY(timestamp), tipe
                ORDER BY day ASC
            """
            cursor.execute(sql, (month_str, user_id))
        else:
            sql = """
                SELECT DAY(timestamp) as day, tipe, SUM(nominal) as total
                FROM transactions
                WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s
                GROUP BY DAY(timestamp), tipe
                ORDER BY day ASC
            """
            cursor.execute(sql, (month_str,))

        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_stats_summary(month_str, user_id=None):
    """
    Ambil statistik ringkasan: jumlah transaksi, rata-rata pengeluaran harian,
    dan kategori dengan pengeluaran terbesar.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # Bangun filter dan params sekali, gunakan ulang per query
        if user_id:
            base_where = "DATE_FORMAT(timestamp, '%Y-%m') = %s AND user_id = %s"
            params = (month_str, user_id)
        else:
            base_where = "DATE_FORMAT(timestamp, '%Y-%m') = %s"
            params = (month_str,)

        # Total jumlah transaksi
        cursor.execute(
            f"SELECT COUNT(*) as total FROM transactions WHERE {base_where}",
            params
        )
        total_tx = (cursor.fetchone() or {}).get('total', 0)

        # Rata-rata pengeluaran harian — gunakan dua parameter terpisah untuk subquery
        cursor.execute(
            f"""
            SELECT AVG(daily_total) as avg_daily FROM (
                SELECT DATE(timestamp) as d, SUM(nominal) as daily_total
                FROM transactions
                WHERE {base_where} AND tipe = 'pengeluaran'
                GROUP BY DATE(timestamp)
            ) sub
            """,
            params  # params cukup 1x karena MySQL hanya butuh 1 pass per prepared statement
        )
        avg_daily = (cursor.fetchone() or {}).get('avg_daily') or 0

        # Kategori terbesar
        cursor.execute(
            f"""
            SELECT kategori, SUM(nominal) as total
            FROM transactions
            WHERE {base_where} AND tipe = 'pengeluaran'
            GROUP BY kategori
            ORDER BY total DESC
            LIMIT 1
            """,
            params
        )
        top_cat_row = cursor.fetchone()
        top_category = top_cat_row['kategori'] if top_cat_row else '-'
        top_category_val = top_cat_row['total'] if top_cat_row else 0

        return {
            'total_tx': total_tx,
            'avg_daily_pengeluaran': round(avg_daily),
            'top_category': top_category,
            'top_category_val': top_category_val,
        }
    finally:
        cursor.close()
        conn.close()

def get_all_transactions_by_user(user_id):
    """
    Ambil SEMUA transaksi milik satu user (tanpa filter bulan).
    Digunakan untuk fitur export Excel per-user.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        sql = '''
            SELECT t.id, t.tipe, t.item, t.nominal, t.kategori, t.timestamp,
                   u.first_name, u.last_name, u.username
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.user_id
            WHERE t.user_id = %s
            ORDER BY t.timestamp DESC
        '''
        cursor.execute(sql, (user_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_all_transactions_export(month_str=None, user_id=None):
    """
    Ambil transaksi untuk keperluan export Excel.
    Bisa difilter berdasarkan bulan dan/atau user_id.
    Jika keduanya None, ambil semua transaksi.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        conditions = []
        params = []

        if month_str:
            conditions.append("DATE_FORMAT(t.timestamp, '%Y-%m') = %s")
            params.append(month_str)
        if user_id:
            conditions.append("t.user_id = %s")
            params.append(user_id)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        sql = f'''
            SELECT t.id, t.user_id, t.tipe, t.item, t.nominal, t.kategori, t.timestamp,
                   u.first_name, u.last_name, u.username
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.user_id
            {where_clause}
            ORDER BY t.timestamp DESC
        '''
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_daily_summary_per_user(user_id, date_str):
    """
    Ambil total per tipe transaksi untuk user tertentu pada tanggal tertentu.
    date_str format: 'YYYY-MM-DD'
    Return: dict {'pemasukan': X, 'pengeluaran': Y, 'investasi': Z}
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = '''
            SELECT tipe, SUM(nominal) as total
            FROM transactions 
            WHERE user_id = %s AND DATE(timestamp) = %s
            GROUP BY tipe
        '''
        cursor.execute(sql, (user_id, date_str))
        results = cursor.fetchall()
        
        report = {"pemasukan": 0, "pengeluaran": 0, "investasi": 0}
        for row in results:
            tipe = row['tipe'].lower()
            if tipe in report:
                report[tipe] = row['total']
                
        return report
    finally:
        cursor.close()
        conn.close()

def get_weekly_summary_per_user(user_id, start_date, end_date):
    """
    Ambil total pengeluaran per kategori untuk user dalam rentang tanggal.
    start_date, end_date format: 'YYYY-MM-DD'
    Return: dict {'total_pengeluaran': X, 'top_kategori': Y, 'top_kategori_nominal': Z}
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Total pengeluaran mingguan
        sql_total = '''
            SELECT SUM(nominal) as total
            FROM transactions 
            WHERE user_id = %s AND DATE(timestamp) BETWEEN %s AND %s AND tipe = 'pengeluaran'
        '''
        cursor.execute(sql_total, (user_id, start_date, end_date))
        total_res = cursor.fetchone()
        total_pengeluaran = total_res['total'] if total_res and total_res['total'] else 0
        
        # Kategori terboros
        sql_top = '''
            SELECT kategori, SUM(nominal) as total
            FROM transactions
            WHERE user_id = %s AND DATE(timestamp) BETWEEN %s AND %s AND tipe = 'pengeluaran'
            GROUP BY kategori
            ORDER BY total DESC
            LIMIT 1
        '''
        cursor.execute(sql_top, (user_id, start_date, end_date))
        top_res = cursor.fetchone()
        
        return {
            'total_pengeluaran': total_pengeluaran,
            'top_kategori': top_res['kategori'] if top_res else '-',
            'top_kategori_nominal': top_res['total'] if top_res else 0
        }
    finally:
        cursor.close()
        conn.close()
