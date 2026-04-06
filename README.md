# Personal Finance & Inventory Bot 🤖

Bot Telegram cerdas untuk manajemen keuangan dan stok barang, ditenagai oleh Gemini 2.5 Flash AI dan sinkronisasi MySQL lokal. Terintegrasi dengan Web Dashboard interaktif.

## Fitur

- 🧠 **Natural Language Processing (NLP)**: Bisa memahami bahasa manusia, tanpa command ribet. (contoh: "beli sabun 20rb", "gaji 2 juta", "stok handuk 5 unit").
- 💰 **Manajemen Keuangan**: Mencatat pemasukan, pengeluaran, dan investasi secara otomatis.
- 📦 **Manajemen Stok Barang**: Mencatat stok inventaris dan perubahannya.
- 📊 **Laporan Bulanan & Web Dashboard**: Melihat ringkasan keuangan secara real-time melalui tampilan antarmuka web lengkap dengan grafik interaktif (Pie, Bar, Line chart).
- 📥 **Export Excel (.xlsx)** _(Fitur Baru!)_: Unduh data transaksi langsung ke Microsoft Excel, lengkap dengan 2 sheet (Transaksi + Ringkasan), styling warna per tipe (Pemasukan/Pengeluaran/Investasi), frozen header, dan auto-column width. Bisa difilter per user dan per bulan.
- 🗑️ **Manajemen Data Lanjutan**: Hapus & edit data transaksi langsung dari bot maupun Dashboard Web.
- 🗄️ **MySQL Database**: Tersimpan aman dan efisien menggunakan local MySQL (Laragon/XAMPP).

## Tech Stack

- Python 3.10+
- `google-genai` (Gemini API)
- `pyTelegramBotAPI` (Telebot)
- `mysql-connector-python` (Database)
- `Flask` & HTML/CSS (Web Dashboard)
- `openpyxl` (Export Excel)
- `python-dotenv`

## Struktur Folder

```
finance_bot_project/
├── .env                  # File konfigurasi yang berisi API Keys (perlu dibuat terlebih dahulu)
├── .env.example          # Contoh file konfigurasi API Keys
├── ai_brain.py           # Logika AI untuk menghubungi Gemini API
├── bot.py                # Core sistem Telegram Bot
├── config.py             # Konfigurasi terpusat (nama bulan, dll.)
├── dashboard.py          # Framework web (Flask) untuk melihat laporan UI + export Excel
├── database.py           # Pengaturan dan operasi Database MySQL
├── handlers/
│   ├── __init__.py       # Registrasi semua handler
│   ├── basic.py          # Handler /start, /help, /profile
│   ├── management.py     # Handler /hapus, /edit
│   ├── nlp_message.py    # Handler pesan bebas (NLP AI)
│   └── report.py         # Handler /laporan, /riwayat
├── templates/
│   └── index.html        # View UI Dashboard Laporan
└── README.md             # Dokumentasi proyek
```

## Perintah Bot Telegram

| Perintah | Deskripsi |
|----------|-----------|
| `/start` atau `/help` | Menampilkan panduan penggunaan bot |
| `/laporan` | Laporan keuangan bulanan dengan navigasi bulan |
| `/riwayat` | Riwayat 10 transaksi terakhir |
| `/edit <ID> <Teks>` | Edit transaksi (contoh: `/edit 10 gaji naik 5 juta`) |
| `/hapus <ID>` | Hapus transaksi (contoh: `/hapus 10` atau `/hapus T-10`) |
| `/profile` | Lihat profil & statistik penggunaan bot |
| `/export` | Download Excel bulan ini langsung di Telegram |
| `/export 2026-03` | Download Excel bulan tertentu (format YYYY-MM) |
| `/export all` | Download Excel semua transaksi (semua bulan) |
| _(Teks bebas)_ | AI otomatis mendeteksi dan mencatat transaksi keuangan |

## Fitur Dashboard Web

| Fitur | Deskripsi |
|-------|-----------|
| Filter bulan & user | Saring data berdasarkan bulan dan/atau pengguna tertentu |
| Summary cards | 5 kartu ringkasan: Pemasukan, Pengeluaran, Investasi, Cash, Saldo Bersih |
| Tab Overview | Pie chart, Bar chart, dan Line chart tren harian |
| Tab Transaksi | Tabel lengkap dengan tombol hapus per baris |
| **Export Excel** | Tombol download `.xlsx` di area filter dan di header tabel transaksi |

## Export Excel — Panduan Penggunaan

### Cara Export dari Dashboard Web

1. Buka dashboard di `http://localhost:5000`
2. **Opsional**: Atur filter Bulan / User sesuai kebutuhan
3. Klik tombol **"⬇ Export Excel"** (hijau) — tersedia di:
   - Area Filter (baris paling kanan)
   - Header tabel di tab **Transaksi**
4. File `.xlsx` akan otomatis terunduh

### URL Langsung

```
# Export semua transaksi bulan April 2026
http://localhost:5000/export/excel?month=2026-04

# Export transaksi bulan April 2026 untuk user tertentu
http://localhost:5000/export/excel?month=2026-04&user_id=123456789
```

### Format File Excel

File yang dihasilkan berisi **2 Sheet**:

**Sheet 1 — "Transaksi":**
- Kolom: No, ID, Tanggal & Waktu, User, Username, Tipe, Item/Keterangan, Kategori, Nominal (Rp)
- Baris berwarna: 🟢 Hijau = Pemasukan, 🔴 Merah = Pengeluaran, 🔵 Biru = Investasi
- Header beku (freeze panes) agar mudah scroll
- Kolom Nominal format angka Rupiah

**Sheet 2 — "Ringkasan":**
- Total Pemasukan, Pengeluaran, Investasi
- Saldo Cash (Pem. - Peng.)
- Saldo Bersih (setelah investasi)
- Total jumlah transaksi

## Persiapan & Setup

### 1. Cara Mendapatkan Token BotFather (Telegram)

1. Buka aplikasi Telegram.
2. Cari `@BotFather` pada kolom pencarian.
3. Kirim pesan `/newbot`.
4. Masukkan nama bot dan username (harus berakhiran `bot`, misal `FinanceTracker_bot`).
5. Copy **HTTP API Token** yang diberikan oleh BotFather.

### 2. Cara Mendapatkan API Key Gemini (Gratis)

1. Kunjungi [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Login dengan akun Google.
3. Klik tombol **Create API key**.
4. Copy **API Key** yang dihasilkan.

### 3. Cara Instalasi

1. **Clone/Download Project**
   Pastikan kamu berada di folder proyek (contoh: `d:\Latihan\transaksi`)
2. **Setup Virtual Environment (Disarankan)**

   ```bash
   python -m venv venv
   # Di Windows:
   venv\Scripts\activate
   # Di Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   Pip install library yang dibutuhkan:

   ```bash
   pip install pyTelegramBotAPI google-genai python-dotenv mysql-connector-python flask openpyxl
   ```

4. **Konfigurasi Environment Variable (.env)**
   Copy file `.env.example` ke `.env`:
   ```bash
   # Di Windows (PowerShell/CMD):
   copy .env.example .env
   # Di Linux/Mac:
   cp .env.example .env
   ```
   Buka file `.env` dengan teks editor (misal VSCode atau Notepad), dan ubah nilainya menjadi token dan key milikmu.
   ```env
   TELEGRAM_BOT_TOKEN="token_dari_botfather"
   GEMINI_API_KEY="api_key_dari_google"
   
   # Database (MySQL Laragon/XAMPP local)
   DB_HOST="localhost"
   DB_USER="root"
   DB_PASSWORD=""
   DB_NAME="finance_bot"
   ```

### 4. Cara Menjalankan Sistem

Jalankan bot telegram di terminal pertama:

```bash
python bot.py
```

Jika berhasil, terminal akan memunculkan tulisan `Bot is running...`.

**Lalu Untuk Membuka Dashboard Laporan**, buka Tab Terminal (CMD/Powershell) **BARU** di folder yang sama, dan jalankan:
```bash
python dashboard.py
```
Aplikasi Laporan Web akan berjalan. Buka *browser* dan kunjungi: **`http://localhost:5000`**

---

## Changelog

### v2.1 — April 2026
- ✨ **Fitur Export Excel**: Download transaksi ke `.xlsx` dengan styling warna, 2 sheet (Transaksi + Ringkasan), dan frozen header.
- 🔔 Banner notifikasi fitur baru di Dashboard Web.
- 📐 Fungsi database baru: `get_all_transactions_export()` dan `get_all_transactions_by_user()`.
- 📖 README diperbarui dengan dokumentasi lengkap Export Excel.

### v2.0 — Maret/April 2026
- Refactor arsitektur ke modul `handlers/`
- Implementasi `/profile`, `/edit`, `/hapus`, `/riwayat`
- Dashboard Web dengan Chart.js (Pie, Bar, Line)
- Filter bulan & user, delete transaksi dari dashboard
- Logging chat ke database
- Notifikasi startup/shutdown bot
