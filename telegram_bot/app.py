import telebot
import logging
import os

from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('API_KEY')
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Grammar search command processing function
@bot.message_handler(commands=['search'])
def search_grammar(message):
    query = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else ''
    if not query:
        bot.reply_to(message, "Будь ласка, надішліть запит разом з командою, наприклад: /search часи")
        return
    # rule search logic by request
    grammar_rule = f"Результат пошуку для '{query}': ..." 
    bot.reply_to(message, grammar_rule)

# Function for processing the "rule of the day" command
@bot.message_handler(commands=['ruleofday'])
def rule_of_the_day(message):
    rule = "Правило дня: ..."  
    bot.reply_to(message, rule)

# Processing text messages that do not correspond to the same command
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Напишіть /search <запит> для пошуку правила або /ruleofday для отримання правила дня.")

if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(e)
