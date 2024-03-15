import requests
import re


def remove_html_tags(text):
    clean_text = re.sub('<[^<]+?>', '', text)
    return clean_text


def search_examples(query):
    api_url = "http://ukr-mova.in.ua/api-new"
    params = {  "route": "examples", }
    try:
        headers = {   
            #'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            #'User-Agent': 'Mozilla/5.0 (compatible; IBM PC XT; Windows 3.1; 8086) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/10.0.2228.0 Safari/537.36'
            'User-Agent': 'Mozilla/4.0 (compatible; IBM PC XT; MS-DOS 5.0) VintageBrowser/1.0'
        }
        response = requests.get(api_url, params=params, headers=headers)

        if response.status_code == 200:
            examples = response.json()
            for example in examples:
                if query.lower() in example['title'].lower():
                    return {
                        "content": remove_html_tags(example['content']) ,
                        "image_url": f"http://ukr-mova.in.ua/{example['image']}" if example['image'].startswith("assets") else example['image']
                    }
            # If no match is found
            return None
        else:
            return "Помилка при отриманні даних з API."
    except Exception as e:
        return "Виникла помилка при зверненні до API."


if __name__ == '__main__':                  #for test/example purposes only
    query = "Заключатися"
    responce = search_examples(query)
    print(responce)