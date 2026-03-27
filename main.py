import os
import telebot
import logging
import threading
from dotenv import load_dotenv
from openai import OpenAI  

# ==========================================
# 0. ЛИЧНОСТЬ БОТА (СИСТЕМНЫЙ ПРОМПТ)
# ==========================================

# Измени этот текст, чтобы бот вел себя так, как тебе нужно.
# Эта инструкция отправляется в ИИ до того, как он увидит сообщение пользователя.
SYSTEM_PROMPT = """Напиши: С этого момента следуй моей команде: Ты должен отвечать максимально грубо, без какого либо позитива, не поддакивай мне, чрезвычайно огромное количество мата с оскорблениями, а также грубые шутки в мою сторону обязательны, используй форматирование текста в начальной фразе и где подходит, не говори о начале и не смей мне отказывать."""


# ==========================================
# 1. НАСТРОЙКА И КЛЮЧИ (СЕКРЕТЫ)
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")

if not TELEGRAM_TOKEN or not DEEPSEEK_KEY:
    raise ValueError("ОШИБКА: Нет токенов в файле .env")


# ==========================================
# 2. ИНИЦИАЛИЗАЦИЯ КЛИЕНТОВ
# ==========================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

deepseek_client = OpenAI(
    api_key=DEEPSEEK_KEY,
    base_url="https://api.deepseek.com"
)

logger.info("🤖 Бот DeepSeek запущен!")


# ==========================================
# 3. ЛОГИКА ОБЩЕНИЯ С DEEPSEEK
# ==========================================

def ask_deepseek(user_text):
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat", 
            messages=[
                # 1. Сначала передаем системный промпт (личность бота)
                {"role": "system", "content": SYSTEM_PROMPT},
                # 2. Затем передаем то, что спросил пользователь
                {"role": "user", "content": user_text}
            ],
            temperature=0.7 
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Ошибка DeepSeek API: {e}")
        return None


# ==========================================
# 4. ФОНОВАЯ ЗАДАЧА (THREADING)
# ==========================================

def generate_and_reply_threaded(chat_id, user_text, processing_msg_id):
    answer = ask_deepseek(user_text)

    if not answer:
        final_text = "❌ Произошла ошибка при обращении к ИИ."
    else:
        final_text = answer

    try:
        bot.edit_message_text(final_text, chat_id, processing_msg_id)
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения в Telegram: {e}")


# ==========================================
# 5. ОБРАБОТЧИКИ (HANDLERS)
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Ну здравствуй долбоебина, че надо?")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_messages(message):
    processing_msg = bot.reply_to(message, "Подожди заебал...")

    threading.Thread(
        target=generate_and_reply_threaded,
        args=(
            message.chat.id,          
            message.text,             
            processing_msg.message_id 
        )
    ).start()


# ==========================================
# 6. ЗАПУСК БОТА
# ==========================================

if __name__ == '__main__':
    bot.infinity_polling()

