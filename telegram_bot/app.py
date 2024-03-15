import telebot
import logging
import os
import asyncio
import aiomysql
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('API_KEY')
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_db_connection():
    conn = await aiomysql.connect(
        host=os.getenv('db_host'),
        user=os.getenv('db_user'),
        password=os.getenv('db_password'),
        db=os.getenv('db_database'),
        loop=asyncio.get_event_loop()
    )
    return conn

async def add_update_user_to_db(user_id, username, first_name, last_name):
    conn = await create_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("""
                            INSERT INTO bot_users (user_id, username, first_name, last_name) 
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                username = VALUES(username),
                                first_name = VALUES(first_name), 
                                last_name = VALUES(last_name)
                            """,
                            (user_id, username, first_name, last_name))
        await conn.commit()
    conn.close()

async def update_query_stats(query_txt):
    """general query stats"""
    conn = await create_db_connection()
    async with conn.cursor() as cursor:
        # Check if the query exists and get its ID
        await cursor.execute("""
            SELECT query_id, times_used FROM query_stats WHERE query_txt = %s
        """, (query_txt,))
        query_info = await cursor.fetchone()
        if query_info:
            # If the query exists, update times_used
            query_id, times_used = query_info
            await cursor.execute("""
                UPDATE query_stats SET times_used = %s WHERE query_id = %s
            """, (times_used + 1, query_id))
        else:
            # If not, insert a new record
            await cursor.execute("""
                INSERT INTO query_stats (query_txt, times_used) VALUES (%s, 1)
            """, (query_txt,))
            query_id = cursor.lastrowid
        
        await conn.commit()
    conn.close()
    return query_id

async def update_user_query_stats(user_id, query_id):
    """usage of particular query by exect user"""
    conn = await create_db_connection()
    async with conn.cursor() as cursor:
        # Check if the user_query exists
        await cursor.execute("""
            SELECT query_count FROM user_query_stats WHERE user_id = %s AND query_id = %s
        """, (user_id, query_id))
        query_count_info = await cursor.fetchone()
        
        if query_count_info:
            # If exists, update query_count
            query_count = query_count_info[0]
            await cursor.execute("""
                UPDATE user_query_stats SET query_count = %s WHERE user_id = %s AND query_id = %s
            """, (query_count + 1, user_id, query_id))
        else:
            # If not, insert a new record
            await cursor.execute("""
                INSERT INTO user_query_stats (user_id, query_id, query_count) VALUES (%s, %s, 1)
            """, (user_id, query_id))
        
        await conn.commit()
    conn.close()

def stats_handler(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    #query_txt = message.text
    query = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else ''
    
    asyncio.run(add_update_user_to_db(user_id, username, first_name, last_name))
    if query:
        query_id = asyncio.run(update_query_stats(query))
        asyncio.run(update_user_query_stats(user_id, query_id))

# Command handler for search grammar
@bot.message_handler(commands=['search'])
def search_grammar(message):
    stats_handler(message)
    query = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else ''
    if not query:
        bot.reply_to(message, "Please send a query along with the command, for example: /search smth")
        return
    grammar_rule = f"Search result for '{query}': ..."  # Placeholder
    bot.reply_to(message, grammar_rule)

# Command handler for rule of the day
@bot.message_handler(commands=['ruleofday'])
def rule_of_the_day(message):
    stats_handler(message)
    rule = "Rule of the day: ..."  # Placeholder
    bot.reply_to(message, rule)

# Handler for all other messages
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    stats_handler(message)
    bot.reply_to(message, "Write /search <query> to search for a rule or /ruleofday to get the rule of the day.")


# Start polling
if __name__ == '__main__':
    try:
        print('Bot started!')
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(e)
