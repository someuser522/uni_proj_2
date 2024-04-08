import requests
import re
import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

base_url = "http://ukr-mova.in.ua/"

params = {  "route": "examples", }
headers = {   'User-Agent': 'Mozilla/4.0 (compatible; IBM PC XT; MS-DOS 5.0) VintageBrowser/1.0'    }
DB_CONFIG = {
    'host': 'localhost', #'#os.getenv('db_host'),
    'user': os.getenv('db_user'),
    'password': os.getenv('db_password'),
    'db': os.getenv('db_database'),
}


def remove_html_tags(text):
    clean_text = re.sub('<[^<]+?>', '', text)
    return clean_text


def add_records_from_api_to_db(records):
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    try:
        cursor.executemany("""
                INSERT INTO api_data (title, content, uri, image) VALUES (%s, %s, %s, %s)
            """, (records))
        connection.commit()
    except mysql.connector.Error as error:
        print(error)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fetch_api_data_in_database():
    try:
        response = requests.get(base_url+"api-new", params=params, headers=headers)

        if response.status_code == 200:
            examples = response.json()
            records = []
            for example in examples:
                record = (example['title'], remove_html_tags(example['content']), example['uri'], example['image'])
                records.append(record)
                add_records_from_api_to_db(records)
            
        else:
            return "Помилка при отриманні даних з API."
    except Exception as e:
        return "Виникла помилка при зверненні до API."


def fulltext_search_by_title(query):
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)  # Set dictionary=True to get results as dictionaries
    try:
        # Perform full-text search
        cursor.execute("""
            SELECT *, MATCH(title) AGAINST (%s IN NATURAL LANGUAGE MODE) AS relevance
            FROM api_data
            WHERE MATCH(title) AGAINST (%s IN NATURAL LANGUAGE MODE)
            ORDER BY MATCH(title) AGAINST (%s IN NATURAL LANGUAGE MODE) DESC
            LIMIT 1;

        """, (query, query, query, ))

        # Fetch results
        results = cursor.fetchall()
        if len(results):
            results = {key: value for key, value in  results[0].items() if key != 'relevance'}
            results['uri'] = base_url + results['uri']
            results['image'] = base_url + results['image']

        return results

    except mysql.connector.Error as error:
        print("Error: {}".format(error))

    finally:
        # Close cursor and connection
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == '__main__':                  #for test/example purposes only
    search_query = "викладач"
    matching_records = fulltext_search_by_title(search_query)
    print(matching_records)