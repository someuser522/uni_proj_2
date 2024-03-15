import telebot
import logging
import os
import asyncio
import aiomysql

from dotenv import load_dotenv
from api_integration import search_examples

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

async def fetch_global_stats():
    """get stats overall usage of queries"""
    conn = await create_db_connection()
    stats = []
    async with conn.cursor() as cursor:
        await cursor.execute("""
            SELECT query_txt, SUM(times_used) as total_usage
            FROM query_stats
            GROUP BY query_txt
            ORDER BY total_usage DESC
            LIMIT 5
        """)
        stats = await cursor.fetchall()
    conn.close()
    return stats

async def send_global_stats(message):
    """print stats overall usage of queries"""
    stats = await fetch_global_stats()
    reply = "Top 5 Queries Overall:\n" + "\n".join([f"{i+1}. {row[0]} - {row[1]} times" for i, row in enumerate(stats)])
    bot.reply_to(message, reply)

async def get_user_stats_by_username(username):
    conn = await create_db_connection()
    
    # Find the user_id for the given username
    user_id = None
    async with conn.cursor() as cursor:
        await cursor.execute("""
            SELECT user_id FROM bot_users WHERE username = %s
        """, (username,))
        user_result = await cursor.fetchone()
        if user_result:
            user_id = user_result[0]
        else:
            return f"No stats found for username: {username}"
    
    # Fetch the top 5 queries made by this user
    if user_id:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT qs.query_txt, uqs.query_count
                FROM user_query_stats uqs
                JOIN query_stats qs ON uqs.query_id = qs.query_id
                WHERE uqs.user_id = %s
                ORDER BY uqs.query_count DESC
                LIMIT 5
            """, (user_id,))
            queries = await cursor.fetchall()
            
            if queries:
                stats_message = f"Top queries for {username}:\n"
                for i, (query_txt, query_count) in enumerate(queries, start=1):
                    stats_message += f"{i}. {query_txt} - {query_count} times\n"
                return stats_message
            else:
                return f"No queries found for user: {username}"
    else:
        return "User not found."

    conn.close()

async def show_user_stats(message, username):
    stats_message = await get_user_stats_by_username(username)
    bot.reply_to(message, stats_message)


# Command handler for search grammar
@bot.message_handler(commands=['search'])
def search_grammar(message):
    stats_handler(message)
    query = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else ''
    if not query:
        bot.reply_to(message, "Please send a query along with the command, for example: /search smth")
        return
    
    result = search_examples(query)
    if result:
        if isinstance(result, str):
            bot.reply_to(message, result)  # error alert
        else:
            bot.send_photo(message.chat.id, result['image_url'], caption=result['content'])
    else:
        bot.reply_to(message, "Немає результатів за вашим запитом.")

# Command handler for rule of the day
@bot.message_handler(commands=['ruleofday'])
def rule_of_the_day(message):
    stats_handler(message)
    rule = "Rule of the day: ..."  # to do later...
    bot.reply_to(message, rule)

@bot.message_handler(commands=['stats'])
def stats_command(message):
    username = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else ''
    if username:
        # Fetch and send user-specific stats
        asyncio.run(show_user_stats(message, username))
    else:
        # Fetch and send global stats
        asyncio.run(send_global_stats(message))

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
Команди, які я розумію:
/help - отримати це повідомлення з інструкціями.
/search <запит> - шукати інформацію за вашим запитом.
/stats <username> - показати статистику запитів для конкретного користувача.
/stats - показати статистику запитів загалом.

Просто надішліть мені команду, і я постараюся допомогти!
"""
    bot.reply_to(message, help_text)

# Handler for all other messages
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    stats_handler(message)
    bot.reply_to(message, "Write /search <query> to search for a rule or /ruleofday to get the rule of the day.")


if __name__ == '__main__':
    try:
        print('Bot started!')
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(e)
