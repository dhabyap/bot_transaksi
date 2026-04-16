import os
import mysql.connector
from mysql.connector import pooling
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "finance_bot")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

# Konfigurasi Koneksi
db_config = {
    "host": DB_HOST,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME
}

# Inisialisasi Connection Pool
try:
    db_pool = pooling.MySQLConnectionPool(
        pool_name="finance_bot_pool",
        pool_size=DB_POOL_SIZE,
        **db_config
    )
    print(f"Connection pool created with size: {DB_POOL_SIZE}")
except mysql.connector.Error as err:
    print(f"Error creating connection pool: {err}")
    db_pool = None

def get_base_connection():
    """
    Membangun koneksi dasar ke server MySQL (tanpa spesifik database).
    Digunakan untuk operasi level administratif seperti CREATE DATABASE.

    Returns:
        mysql.connector.connection.MySQLConnection: Objek koneksi MySQL.
    """
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )

def get_connection():
    """
    Mengambil koneksi database dari pool jika tersedia, atau membuat koneksi baru.
    
    Returns:
        mysql.connector.connection.MySQLConnection: Objek koneksi database yang aktif.
    """
    if db_pool:
        return db_pool.get_connection()
    return mysql.connector.connect(**db_config)

def init_db():
    """
    Inisialisasi database dan semua tabel yang diperlukan.
    Melakukan pengecekan database, pembuatan tabel, dan migrasi kolom jika diperlukan.
    """
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
        migration_columns = [
            "ALTER TABLE users ADD COLUMN has_accepted_disclaimer TINYINT(1) DEFAULT 0",
            "ALTER TABLE users ADD COLUMN streak_count INT DEFAULT 0",
            "ALTER TABLE users ADD COLUMN last_streak_date DATE DEFAULT NULL"
        ]
        
        for sql in migration_columns:
            try:
                cursor.execute(sql)
                conn.commit()
            except mysql.connector.Error as err:
                if err.errno == 1060: # Column already exists
                    pass
                else:
                    print(f"Migration error for '{sql}': {err}")
        
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
    except mysql.connector.Error as err:
        if err.errno == 1060:
            pass # Kolom sudah ada
        else:
            print(f"Database migration error: {err}")
    
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
    """
    Menyimpan data transaksi baru ke dalam database.

    Args:
        user_id (int): ID unik user Telegram.
        tipe (str): Tipe transaksi (pemasukan, pengeluaran, investasi).
        item (str): Deskripsi barang atau keterangan transaksi.
        nominal (float): Nilai nominal uang dalam transaksi.
        kategori (str): Kategori transaksi (misal: makanan, transportasi).

    Returns:
        int: ID baris (primary key) dari transaksi yang baru saja dimasukkan.
    """
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
    """
    Menyimpan data barang inventaris baru ke dalam database.

    Args:
        user_id (int): ID unik user Telegram.
        nama_barang (str): Nama barang yang dicatat.
        kuantitas (int): Jumlah barang.
        status (str): Status barang (misal: ada, habis, dipinjam).

    Returns:
        int: ID baris dari data inventaris yang baru saja dimasukkan.
    """
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
    """
    Mengambil ringkasan laporan bulanan (total pemasukan, pengeluaran, investasi).

    Args:
        user_id (int, optional): ID user untuk filter laporan personal.
        month_str (str, optional): Bulan laporan dalam format 'YYYY-MM'. 
                                  Default adalah bulan saat ini.

    Returns:
        dict: Dictionary berisi total nominal untuk tiap tipe transaksi.
    """
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
    """
    Menghapus data transaksi tertentu berdasarkan ID dan User ID.

    Args:
        tx_id (int): ID transaksi yang akan dihapus.
        user_id (int): ID user pemilik transaksi tersebut.

    Returns:
        bool: True jika berhasil dihapus, False jika data tidak ditemukan.
    """
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
    """
    Menghapus data inventaris tertentu berdasarkan ID dan User ID.

    Args:
        inv_id (int): ID inventaris yang akan dihapus.
        user_id (int): ID user pemilik inventaris tersebut.

    Returns:
        bool: True jika berhasil dihapus, False jika data tidak ditemukan.
    """
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
    """
    Memperbarui data transaksi yang sudah ada.

    Args:
        tx_id (int): ID transaksi yang akan diubah.
        user_id (int): ID user pemilik transaksi.
        tipe (str): Tipe baru transaksi.
        item (str): Deskripsi baru transaksi.
        nominal (float): Nominal baru transaksi.
        kategori (str): Kategori baru transaksi.

    Returns:
        bool: True jika berhasil diupdate, False jika tidak ada baris yang berubah.
    """
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
    """
    Memperbarui data inventaris yang sudah ada.

    Args:
        inv_id (int): ID inventaris yang akan diubah.
        user_id (int): ID user pemilik inventaris.
        nama_barang (str): Nama barang baru.
        kuantitas (int): Jumlah barang baru.
        status (str): Status baru barang.

    Returns:
        bool: True jika berhasil diupdate, False jika tidak ada baris yang berubah.
    """
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
    """
    Mengambil riwayat gabungan dari transaksi dan inventaris user.

    Args:
        user_id (int): ID user Telegram.
        limit (int, optional): Jumlah maksimal data yang diambil. Default 10.

    Returns:
        list: List of dictionaries berisi data riwayat terurut dari yang terbaru.
    """
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

        if user_id:
            # Query dengan filter user_id
            params = (month_str, user_id)
            
            # Total jumlah transaksi
            cursor.execute(
                "SELECT COUNT(*) as total FROM transactions WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s AND user_id = %s",
                params
            )
            total_tx = (cursor.fetchone() or {}).get('total', 0)

            # Rata-rata pengeluaran harian
            cursor.execute(
                """
                SELECT AVG(daily_total) as avg_daily FROM (
                    SELECT DATE(timestamp) as d, SUM(nominal) as daily_total
                    FROM transactions
                    WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s AND user_id = %s AND tipe = 'pengeluaran'
                    GROUP BY DATE(timestamp)
                ) sub
                """,
                params
            )
            avg_daily = (cursor.fetchone() or {}).get('avg_daily') or 0

            # Kategori terbesar
            cursor.execute(
                """
                SELECT kategori, SUM(nominal) as total
                FROM transactions
                WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s AND user_id = %s AND tipe = 'pengeluaran'
                GROUP BY kategori
                ORDER BY total DESC
                LIMIT 1
                """,
                params
            )
        else:
            # Query tanpa filter user_id (global)
            params = (month_str,)
            
            # Total jumlah transaksi
            cursor.execute(
                "SELECT COUNT(*) as total FROM transactions WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s",
                params
            )
            total_tx = (cursor.fetchone() or {}).get('total', 0)

            # Rata-rata pengeluaran harian
            cursor.execute(
                """
                SELECT AVG(daily_total) as avg_daily FROM (
                    SELECT DATE(timestamp) as d, SUM(nominal) as daily_total
                    FROM transactions
                    WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s AND tipe = 'pengeluaran'
                    GROUP BY DATE(timestamp)
                ) sub
                """,
                params
            )
            avg_daily = (cursor.fetchone() or {}).get('avg_daily') or 0

            # Kategori terbesar
            cursor.execute(
                """
                SELECT kategori, SUM(nominal) as total
                FROM transactions
                WHERE DATE_FORMAT(timestamp, '%Y-%m') = %s AND tipe = 'pengeluaran'
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

        if month_str and user_id:
            sql = '''
                SELECT t.id, t.user_id, t.tipe, t.item, t.nominal, t.kategori, t.timestamp,
                       u.first_name, u.last_name, u.username
                FROM transactions t
                LEFT JOIN users u ON t.user_id = u.user_id
                WHERE DATE_FORMAT(t.timestamp, '%Y-%m') = %s AND t.user_id = %s
                ORDER BY t.timestamp DESC
            '''
            params = (month_str, user_id)
        elif month_str:
            sql = '''
                SELECT t.id, t.user_id, t.tipe, t.item, t.nominal, t.kategori, t.timestamp,
                       u.first_name, u.last_name, u.username
                FROM transactions t
                LEFT JOIN users u ON t.user_id = u.user_id
                WHERE DATE_FORMAT(t.timestamp, '%Y-%m') = %s
                ORDER BY t.timestamp DESC
            '''
            params = (month_str,)
        elif user_id:
            sql = '''
                SELECT t.id, t.user_id, t.tipe, t.item, t.nominal, t.kategori, t.timestamp,
                       u.first_name, u.last_name, u.username
                FROM transactions t
                LEFT JOIN users u ON t.user_id = u.user_id
                WHERE t.user_id = %s
                ORDER BY t.timestamp DESC
            '''
            params = (user_id,)
        else:
            sql = '''
                SELECT t.id, t.user_id, t.tipe, t.item, t.nominal, t.kategori, t.timestamp,
                       u.first_name, u.last_name, u.username
                FROM transactions t
                LEFT JOIN users u ON t.user_id = u.user_id
                ORDER BY t.timestamp DESC
            '''
            params = ()

        cursor.execute(sql, params)
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()

def get_user_balance(user_id):
    """
    Menghitung total saldo saat ini dari user (Pemasukan - Pengeluaran - Investasi).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # Hitung saldo: sum income - sum expense - sum investment
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN tipe = 'pemasukan' THEN nominal ELSE 0 END) - 
                SUM(CASE WHEN tipe = 'pengeluaran' THEN nominal ELSE 0 END) - 
                SUM(CASE WHEN tipe = 'investasi' THEN nominal ELSE 0 END) as balance
            FROM transactions 
            WHERE user_id = %s
        ''', (user_id,))
        res = cursor.fetchone()
        return res['balance'] if res['balance'] is not None else 0
    finally:
        cursor.close()
        conn.close()

def update_user_streak(user_id):
    """
    Update streak harian user. 
    Returns: (new_streak, is_new_milestone)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT streak_count, last_streak_date FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return 0, False
            
        current_streak = user['streak_count'] or 0
        last_date = user['last_streak_date']
        
        # Jika last_date adalah string (tergantung driver/config), parse ke date object
        if isinstance(last_date, str):
            try:
                last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
            except:
                last_date = None
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        new_streak = current_streak
        is_new_milestone = False
        
        if last_date is None:
            # Streak pertama kali
            new_streak = 1
        elif last_date == today:
            # Sudah diupdate hari ini, biarkan
            return current_streak, False
        elif last_date == yesterday:
            # Melanjutkan streak
            new_streak = current_streak + 1
        else:
            # Streak terputus (melewati > 1 hari)
            new_streak = 1
            
        # Update ke DB
        cursor.execute(
            "UPDATE users SET streak_count = %s, last_streak_date = %s WHERE user_id = %s",
            (new_streak, today, user_id)
        )
        conn.commit()
        
        # Cek milestone (3, 7, 14, 30)
        if new_streak in [3, 7, 14, 30]:
            is_new_milestone = True
            
        return new_streak, is_new_milestone
    finally:
        cursor.close()
        conn.close()
