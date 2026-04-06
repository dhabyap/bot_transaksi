from . import basic
from . import report
from . import management
from . import export
from . import nlp_message

def register_all_handlers(bot):
    """
    Mendaftarkan seluruh handler bot dari berbagai modul (clean architecture).
    Urutan pendaftaran penting: handler string spesifik di atas (commands), 
    handler pesan text generic di bawah.
    """
    basic.register_handlers(bot)
    report.register_handlers(bot)
    management.register_handlers(bot)
    export.register_handlers(bot)
    nlp_message.register_handlers(bot)
