
import logging
import os
from logging.handlers import RotatingFileHandler

# Configurar logs con rotación automática
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_file = "logs/bot.log"
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

logger.info("Bot iniciado con sistema de logs avanzados.")
