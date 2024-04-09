import logging.handlers
import logging
import telebot
import asyncio
import os
import sys
import mysql.connector

from api_integration import fetch_api_data_in_database, fulltext_search_by_title
from dotenv import load_dotenv
load_dotenv()

bot = telebot.TeleBot(os.getenv('API_KEY'))
log_file_path = os.getenv('log_file_path') 

DB_CONFIG = {
    'host': os.getenv('db_host'),
    'user': os.getenv('db_user'),
    'password': os.getenv('db_password'),
    'db': os.getenv('db_database'),
}


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if os.path.exists(os.path.dirname(log_file_path)):
        handler = logging.FileHandler(log_file_path)
    else:
        print(f"[!] Warning: Could not open {log_file_path} for logging. Falling back to console output.")
        handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    return handler


def update_stats_in_db(query):
    logging.info("update_stats_in_db")
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

         # Check if the query exists and get its ID
        cursor.execute("""
            SELECT query_id, times_used FROM query_stats WHERE query_txt = %s
        """, (query,))

        query_info = cursor.fetchone()
        if query_info: # If the query exists, update times_used
            query_id, times_used = query_info
            cursor.execute("""
                UPDATE query_stats SET times_used = %s WHERE query_id = %s
            """, (times_used + 1, query_id))
        else:   # If not, insert a new record
            cursor.execute("""
                INSERT INTO query_stats (query_txt, times_used) VALUES (%s, 1)
            """, (query,))
            query_id = cursor.lastrowid
        
        connection.commit()
        logging.info("Stats updated successfully")
    except mysql.connector.Error as error:
        logging.error(f"Failed to update stats in MySQL database: {error}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_stats():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        cursor.execute("""     
            SELECT query_txt, SUM(times_used) as total_usage
            FROM query_stats
            GROUP BY query_txt
            ORDER BY total_usage DESC
            LIMIT 5
        """)
        
        stats = cursor.fetchall()
    except mysql.connector.Error as error:
        logging.error(f"Failed to get stats in MySQL database: {error}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
        return stats


def extract_query_and_param(message):
    logging.info("extract_query_and_param...")
    command = message.text.split()[0]
    query_param = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    return (command, query_param)


# Command handler for search grammar hints/rules...
@bot.message_handler(commands=['search'])
def search_grammar(message):
    query_command, query_param = extract_query_and_param(message)
    if query_param is None: # nothing to query, quit.
        bot.reply_to(message, "Please send a query along with the command, for example: /search smth")
        return
    else: 
        update_stats_in_db(query_param)
        response = fulltext_search_by_title(query_param)
        if len(response):
            bot.send_photo(message.chat.id, response['image'], caption=response['content'])
        else:
            bot.reply_to(message, "На жаль не маю що відповісти =(")


@bot.message_handler(commands=['stats'])
def stats_command(message):
    stats = get_stats()
    reply = (
        'Top 5 request Overall:\n'+
        ''.join([f"{i+1}. {row[0]} - {row[1]} times\n" for i, row in enumerate(stats)])
    )
    bot.reply_to(message, reply)


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        'Команди, які я розумію:\n'
        '/help - отримати це повідомлення з інструкціями.\n'
        '/search <запит> - шукати інформацію за вашим запитом.\n'
        '/stats - показати статистику запитів загалом.\n'
        'Просто надішліть мені команду, і я постараюся допомогти!\n'
    )
    bot.reply_to(message, help_text)


def get_record_count():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
     
        query = "SELECT COUNT(*) FROM api_data"
        cursor.execute(query)
        record_count = cursor.fetchone()[0]
        return record_count

    except mysql.connector.Error as error:
        logging.info("Error while connecting to MySQL", error)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


async def main():
    setup_logging()
    try:
        data_size = get_record_count()
        if data_size is None:
            logging.info("calling fetch_api_data_in_database...")
            fetch_api_data_in_database()
        else:
            logging.info("data exist, there is no necessity to download it again...")

        logging.info("Bot is polling...")
        await bot.polling(none_stop=True)
    except Exception as e:
        logging.error(e)


if __name__ == '__main__':
    asyncio.run(main())
