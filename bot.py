import telebot
from config import BOT_TOKEN
import database
from handlers import register_all_handlers

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize database
database.init_db()

# Register all handlers from the modular architecture
register_all_handlers(bot)

if __name__ == "__main__":
    # Setup auto-suggest / menu perintah di Telegram
    bot.set_my_commands([
        telebot.types.BotCommand("/start", "Menjalankan ulang bot"),
        telebot.types.BotCommand("/help", "Info cara penggunaan bot"),
        telebot.types.BotCommand("/profile", "Melihat profil dan statistik Anda"),
        telebot.types.BotCommand("/laporan", "Melihat ringkasan keuangan"),
        telebot.types.BotCommand("/riwayat", "Melihat riwayat transaksi & stok")
    ])
    print("Bot is running...")
    bot.infinity_polling()
