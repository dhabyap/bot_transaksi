from flask import Flask, render_template, request, redirect, url_for, flash
import database
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key" # Dibutuhkan untuk memunculkan flash message

# Inisialisasi database MySQL saat aplikasi web mulai jalan
try:
    database.init_db()
except Exception as e:
    print(f"Gagal menginisialisasi database: {e}")

@app.route('/')
def index():
    # Ambil filter bulan dari query (default ke bulan ini jika kosong)
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    # Ambil data filter user_id (opsional)
    user_id_filter = request.args.get('user_id', '')
    
    uid = None
    if user_id_filter.isdigit():
        uid = int(user_id_filter)
        
    try:
        # Panggil database SQL
        transactions = database.get_transactions_by_month(month, uid)
        report = database.get_monthly_report(uid)
        
        # Handle kondisi where report["pemasukan"] / pengeluaran might be None (jika tidak ada data)
        pemasukan = report.get('pemasukan') or 0
        pengeluaran = report.get('pengeluaran') or 0
        
    except Exception as e:
        flash(f"Error mengakses database: {e}", "error")
        transactions = []
        pemasukan = 0
        pengeluaran = 0

    saldo = pemasukan - pengeluaran

    return render_template(
        'index.html',
        transactions=transactions,
        month=month,
        user_id_filter=user_id_filter,
        pemasukan=pemasukan,
        pengeluaran=pengeluaran,
        saldo=saldo
    )

@app.route('/delete/<int:tx_id>', methods=['POST'])
def delete_tx(tx_id):
    try:
        success = database.delete_transaction(tx_id)
        if success:
            flash("Data transaksi berhasil dihapus!", "success")
        else:
            flash("Data transaksi gagal dihapus (id tidak ditemukan).", "error")
    except Exception as e:
        flash(f"Error system: {e}", "error")
        
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
