import os
import urllib.parse
from dotenv import load_dotenv
import pandas as pd
from bs4 import BeautifulSoup
from zenrows import ZenRowsClient
import requests
import easygui as gui
from difflib import SequenceMatcher

load_dotenv()

# Sentence Tokenization methods:
def split_sentence(sentence):
    ticker = []
    url = []
    remaining_sentence = sentence

    # Split based on $
    if '$' in sentence:
        parts = sentence.split()
        for word in parts:
            if '$' in word:
                ticker.append(word.strip('$'))
                remaining_sentence = remaining_sentence.replace(word, '').strip()

    # Split based on http
    if 'http' in remaining_sentence:
        parts = remaining_sentence.split()
        for word in parts:
            if 'http' in word:
                url.append(word)
                remaining_sentence = remaining_sentence.replace(word, '').strip()

    return ticker, remaining_sentence, url


# Classification methods:
def extract_classification(text, classification_prompt):
    print("Extracting classification for", text)
    api_key = os.getenv('OPENAI_API_KEY')
    api_url = os.getenv('OPENAI_API_URL')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    payload = {
        'model': 'text-davinci-003',
        'prompt': f'"\n\n{text} {classification_prompt}"',
        'temperature': 0.5,
        'max_tokens': 60,
        'top_p': 1.0,
        'frequency_penalty': 0.8,
        'presence_penalty': 0.0,
    }

    print("Sending request to", api_url, "with payload", payload)

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        json_data = response.json()
        classification_response = json_data['choices'][0]['text'].strip()
        print("Classification response:", classification_response)
        return classification_response
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

# Scraping methods:
def url_encode_string(input_string):
    encoded_string = urllib.parse.quote(input_string)
    return encoded_string

def similarity_score(a, b):
    return SequenceMatcher(None, a, b).ratio()

def scrape_bloomberg(subject):
    client = ZenRowsClient("6026db40fdbc3db28235753087be6225f047542f")
    params = {"premium_proxy": "true", "proxy_country": "us"}
    url_encoded_subject = url_encode_string(subject)

    full_url = 'https://www.bloomberg.com/search?query=' + url_encoded_subject + '&sort=relevance:asc&startTime=2015-04-01T01:01:01.001Z&' + '&page=' + str(
        1)
    print("Trying url " + full_url)
    response = client.get(full_url, params=params)
    print("Response code: " + str(response.status_code))
    soup = BeautifulSoup(response.content, 'html.parser')
    links = [a['href'] for a in soup.select('a[class^="headline_"]') if 'href' in a.attrs]
    print("Found " + str(len(links)) + " links", "these are: " + str(links))
    return links



def scrape_reuters(subject):
    client = ZenRowsClient("6026db40fdbc3db28235753087be6225f047542f")
    params = {"premium_proxy": "true", "proxy_country": "us"}
    url_encoded_subject = url_encode_string(subject)

    full_url = 'https://www.reuters.com/search/news?blob=' + url_encoded_subject
    print("Trying url " + full_url)
    response = requests.get(full_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    link_elements = soup.select('h3.search-result-title > a')
    links = [link['href'] for link in link_elements]
    print("Found " + str(len(links)))

    for link in links:
        full_link = "https://www.reuters.com" + link
        print("Link:", full_link)

        response = requests.get(full_link)
        soup = BeautifulSoup(response.content, 'html.parser')

        news_format = "type_1" # https://www.reuters.com/article/idUSKCN20K2SM
        try:
            headline_element = soup.select_one('h1[class^="Headline-headline-"]')
            headline_text = headline_element.text.strip()
            print("Headline:", headline_text)
        except AttributeError:
            headline_element = soup.select_one('h1[class^="text__text__"]')
            headline_text = headline_element.text.strip()
            print("Headline:", headline_text)
            news_format = "type_2" # https://www.reuters.com/article/idUSKBN2KT0BX

        similarity = similarity_score(subject, headline_text)
        if similarity > 0.8:
            if news_format == "type_1":
                print("Relevant")
                paragraph_elements = soup.select('p[class^="Paragraph-paragraph-"]')
                paragraph_text = ' '.join([p.text.strip() for p in paragraph_elements])
                print("Text:", paragraph_text)
                return full_link, subject + ". With full context: " + paragraph_text
            elif news_format == "type_2":
                print("Relevant")
                paragraph_elements = soup.select('p[class^="text__text__"]')
                paragraph_text = ' '.join([p.text.strip() for p in paragraph_elements])
                print("Text:", paragraph_text)
                return full_link, subject + ". With full context: " + paragraph_text
        else:
            print("Not relevant")

    print("Context not found in Reuters")
    return "N/A", subject

def scrape_wsj(subject):
    client = ZenRowsClient("6026db40fdbc3db28235753087be6225f047542f")
    params = {"premium_proxy": "true", "proxy_country": "us"}
    url_encoded_subject = url_encode_string(subject)

    full_url = 'https://www.wsj.com/search?query=' + url_encoded_subject + '&operator=OR&sort=relevance&duration=1y&startDate=2015%2F01%2F01&endDate=2016%2F01%2F01'
    print("Trying url " + full_url)
    response = requests.get(full_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    link_elements = soup.select('h3[class^="WSJTheme--headline"] a')
    links = [link['href'] for link in link_elements]
    print("Found " + str(len(links)))

    for link in links:
        full_link = link
        print("Link:", full_link)

        response = requests.get(full_link)
        soup = BeautifulSoup(response.content, 'html.parser')

        news_format = "type_1" # https://www.reuters.com/article/idUSKCN20K2SM
        # try:
        headline_element = soup.select_one('h1[class*="StyledHeadline"]')
        headline_text = headline_element.text.strip()
        print("Headline:", headline_text)
        # except AttributeError:
        #     headline_element = soup.select_one('h1[class^="text__text__"]')
        #     headline_text = headline_element.text.strip()
        #     print("Headline:", headline_text)
        #     news_format = "type_2" # https://www.reuters.com/article/idUSKBN2KT0BX

        similarity = similarity_score(subject, headline_text)
        if similarity > 0.8:
            # if news_format == "type_1":
            print("Relevant")
            paragraph_elements = soup.select('p[class^="Paragraph-paragraph-"]')
            paragraph_text = ' '.join([p.text.strip() for p in paragraph_elements])
            print("Text:", paragraph_text)
            return full_link, subject + ". With full context: " + paragraph_text
            # elif news_format == "type_2":
            #     print("Relevant")
            #     paragraph_elements = soup.select('p[class^="text__text__"]')
            #     paragraph_text = ' '.join([p.text.strip() for p in paragraph_elements])
            #     print("Text:", paragraph_text)
            #     return full_link, subject + ". With full context: " + paragraph_text
        else:
            print("Not relevant")

    print("Context not found in WSJ")
    return "N/A", subject

def scrape_seeking_alpha(subject):
    client = ZenRowsClient("6026db40fdbc3db28235753087be6225f047542f")
    params = {"js_render":"true","antibot":"true"}
    url_encoded_subject = url_encode_string(subject)

    full_url = 'https://seekingalpha.com/search?q=' + url_encoded_subject + '&tab=headlines'
    print("Trying url " + full_url)
    response = requests.get(full_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    print("Trying to find post list div", soup.text)

    post_list_div = soup.find('div', {'data-test-id': 'post-list'})
    if post_list_div:
        article_elements = post_list_div.find_all('article')
        links = [a['href'] for article in article_elements for a in article.select('a')]
        print("Found " + str(len(links)) + " links")
    else:
        print("Post list div not found")

    for link in links:
        full_link = "https://seekingalpha.com/" + link
        print("Link:", full_link)

        response = requests.get(full_link)
        soup = BeautifulSoup(response.content, 'html.parser')

        news_format = "type_1" # https://www.reuters.com/article/idUSKCN20K2SM
        # try:
        headline_element = soup.select_one('h1[data-test-id="post-title"]')
        headline_text = headline_element.text.strip()
        print("Headline:", headline_text)
        # except AttributeError:
        #     headline_element = soup.select_one('h1[class^="text__text__"]')
        #     headline_text = headline_element.text.strip()
        #     print("Headline:", headline_text)
        #     news_format = "type_2" # https://www.reuters.com/article/idUSKBN2KT0BX

        similarity = similarity_score(subject, headline_text)
        if similarity > 0.8:
            # if news_format == "type_1":
            print("Relevant")
            paragraph_elements = soup.select('p[class^="Paragraph-paragraph-"]')
            paragraph_text = ' '.join([p.text.strip() for p in paragraph_elements])
            print("Text:", paragraph_text)
            return full_link, subject + ". With full context: " + paragraph_text
            # elif news_format == "type_2":
            #     print("Relevant")
            #     paragraph_elements = soup.select('p[class^="text__text__"]')
            #     paragraph_text = ' '.join([p.text.strip() for p in paragraph_elements])
            #     print("Text:", paragraph_text)
            #     return full_link, subject + ". With full context: " + paragraph_text
        else:
            print("Not relevant")

    print("Context not found in Seeking Alpha")
    return "N/A", subject

def scrape_yahoo(subject):
    client = ZenRowsClient("6026db40fdbc3db28235753087be6225f047542f")
    params = {"premium_proxy": "true", "proxy_country": "us"}
    url_encoded_subject = url_encode_string(subject)

    full_url = 'https://seekingalpha.com/search?q=' + url_encoded_subject + '&tab=headlines'
    print("Trying url " + full_url)
    response = requests.get(full_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    link_elements = soup.select('a[data-test-id="post-list-item-title"]')
    links = [link['href'] for link in link_elements]
    print("Found " + str(len(links)))

    for link in links:
        full_link = "https://seekingalpha.com/" + link
        print("Link:", full_link)

        response = requests.get(full_link)
        soup = BeautifulSoup(response.content, 'html.parser')

        news_format = "type_1" # https://www.reuters.com/article/idUSKCN20K2SM
        # try:
        headline_element = soup.select_one('h1[data-test-id="post-title"]')
        headline_text = headline_element.text.strip()
        print("Headline:", headline_text)
        # except AttributeError:
        #     headline_element = soup.select_one('h1[class^="text__text__"]')
        #     headline_text = headline_element.text.strip()
        #     print("Headline:", headline_text)
        #     news_format = "type_2" # https://www.reuters.com/article/idUSKBN2KT0BX

        similarity = similarity_score(subject, headline_text)
        if similarity > 0.8:
            # if news_format == "type_1":
            print("Relevant")
            paragraph_elements = soup.select('p[class^="Paragraph-paragraph-"]')
            paragraph_text = ' '.join([p.text.strip() for p in paragraph_elements])
            print("Text:", paragraph_text)
            return full_link, subject + ". With full context: " + paragraph_text
            # elif news_format == "type_2":
            #     print("Relevant")
            #     paragraph_elements = soup.select('p[class^="text__text__"]')
            #     paragraph_text = ' '.join([p.text.strip() for p in paragraph_elements])
            #     print("Text:", paragraph_text)
            #     return full_link, subject + ". With full context: " + paragraph_text
        else:
            print("Not relevant")

    print("Context not found in Seeking Alpha")
    return "N/A", subject


def select_column_and_classify():
    try:
        # Classify sentences
        classification_choice = gui.ynbox("Do you want to classify the news?", "Classification")

        if classification_choice:
            # Read CSV file
            file_path = gui.fileopenbox("Select CSV file", filetypes=["*.csv"])
            df = pd.read_csv(file_path)
            column_names = df.columns.tolist()

            selected_column = gui.buttonbox("Column Selection",
                                            "Select the column of sentence for classification:",
                                            choices=column_names)
            if not selected_column:
                raise ValueError("Invalid column selection")

            df["classification"] = ""  # Create a new column named "classification"
            default_classification_prompt = ". For news above, determine its origin. Only print \"Twitter\" or \"Seeking Alpha\" or \"Reuters\" or \"WSJ\""
            classification_prompt = gui.enterbox("Modify the classification prompt:", "Custom Classification Prompt",
                                                 default_classification_prompt)

            if not classification_prompt:
                classification_prompt = default_classification_prompt

            for row_index, row in df.iloc[1:].iterrows():
                target_sentence = row[selected_column]
                classification_response = extract_classification(target_sentence, classification_prompt)
                df.at[row_index, "classification"] = classification_response  # Assign classification response to the new column

            output_file_path = os.path.splitext(file_path)[0] + "_classified.csv"
            df.to_csv(output_file_path, index=False)
            gui.msgbox("Classification Complete")

        # Research contexts for sentences
        context_choice = gui.ynbox("Do you want to research the context for this news?", "Context Research")
        if context_choice:
            file_path = gui.fileopenbox("Select the CSV file containing news for context research",
                                       filetypes=["*.csv"])
            df = pd.read_csv(file_path)
            column_names = df.columns.tolist()
            df["link"] = ""  # Create a new column named "link"
            df["contextualized_sentence"] = ""  # Create a new column named "contextualized sentence"

            if file_path:
                selected_column = gui.buttonbox("Column Selection",
                                               "Select the column for target sentence in the CSV:",
                                               choices=column_names)
                if not selected_column:
                    raise ValueError("Invalid context selected selection")
                classification_column = gui.buttonbox("Column Selection",
                                                      "Select the column for classification in the CSV:",
                                                      choices=column_names)
                if not classification_column:
                    raise ValueError("Invalid context classification column selection")

                for row_index, row in df.iloc[1:].iterrows():
                    target_sentence = row[selected_column]
                    ticker, remaining_sentence, link = split_sentence(target_sentence)

                    # Perform scraping based on classification_response
                    if row[classification_column] == "Twitter":
                        # Perform Twitter scraping
                        df.at[row_index, "link"] = "N/A"  # Put "N/A" under "link"
                        df.at[row_index, "contextualized_sentence"] = remaining_sentence  # Copy "target_sentence"

                    elif row[classification_column] == "Reuters":
                        # Perform Reuters scraping
                        url, contextualized_sentence = scrape_reuters(remaining_sentence)
                        df.at[row_index, "link"] = url
                        df.at[row_index, "contextualized_sentence"] = contextualized_sentence
                    elif row[classification_column] == "WSJ":
                        # Perform WSJ scraping
                        url, contextualized_sentence = scrape_wsj(remaining_sentence)
                        df.at[row_index, "link"] = url
                        df.at[row_index, "contextualized_sentence"] = contextualized_sentence
                    elif row[classification_column] == "Seeking Alpha":
                        # Perform Seeking Alpha scraping
                        url, contextualized_sentence = scrape_seeking_alpha(remaining_sentence)
                        df.at[row_index, "link"] = url
                        df.at[row_index, "contextualized_sentence"] = contextualized_sentence
                    else:
                        df.at[row_index, "link"] = "N/A"  # Put "N/A" under "link"
                        df.at[row_index, "contextualized_sentence"] = remaining_sentence  # Copy "target_sentence"

            output_file_path = os.path.splitext(file_path)[0] + "_contextualized.csv"
            df.to_csv(output_file_path, index=False)
            gui.msgbox("Scraping Complete")
    except Exception as e:
        gui.exceptionbox(str(e))



def browse_csv_file():
    select_column_and_classify()


if __name__ == '__main__':
    browse_csv_file()
