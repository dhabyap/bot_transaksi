# Personal Finance & Inventory Bot 🤖

Bot Telegram cerdas untuk manajemen keuangan dan stok barang, ditenagai oleh Gemini 1.5/2.5 Flash AI dan sinkronisasi MySQL lokal. Terintegrasi dengan Web Dashboard interaktif.

## Fitur

- 🧠 **Natural Language Processing (NLP)**: Bisa memahami bahasa manusia, tanpa command ribet. (contoh: "beli sabun 20rb", "gaji 2 juta", "stok handuk 5 unit").
- 💰 **Manajemen Keuangan**: Mencatat pemasukan dan pengeluaran secara otomatis.
- 📦 **Manajemen Stok Barang**: Mencatat stok inventaris dan perubahannya.
- 📊 **Laporan Bulanan & Web Dashboard**: Melihat ringkasan pemasukan dan pengeluaran secara real-time melalui tampilan antarmuka web yang lengkap, diurutkan bedasar riwayat terbaru.
- 🗑️ **Manajemen Data Lanjutan**: Terdapat tombol hapus data transaksi di Dashboard Web.
- 🗄️ **MySQL Database**: Tersimpan aman dan efisien menggunakan local MySQL (Laragon/XAMPP).

## Tech Stack

- Python 3.10+
- `google-genai` (Gemini API)
- `google-genai` (Gemini API)
- `pyTelegramBotAPI` (Telebot)
- `mysql-connector-python` (Database)
- `Flask` & HTML/Tailwind CSS (Web Dashboard)
- `python-dotenv`

## Struktur Folder

```
finance_bot_project/
├── .env                  # File konfigurasi yang berisi API Keys (perlu dibuat terlebih dahulu)
├── .env.example          # Contoh file konfigurasi API Keys
├── ai_brain.py           # Logika AI untuk menghubungi Gemini API
├── bot.py                # Core sistem Telegram Bot
├── dashboard.py          # Framework web (Flask) untuk melihat laporan UI
├── database.py           # Pengaturan dan operasi Database MySQL
├── templates/
│   └── index.html        # View UI Dashboard Laporan Tailwnd
└── README.md             # Dokumentasi proyek
```

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
   pip install pyTelegramBotAPI google-genai python-dotenv
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

