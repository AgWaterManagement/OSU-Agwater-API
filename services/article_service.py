import os
import json
import xml.etree.ElementTree as ET
from utils.helpers import sort_list_of_dicts

def get_article_list():
    folder_path = 'd:/Websites/AgWaterReact/public/articles'
    articles = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".xml"):
            file_path = os.path.join(folder_path, filename)
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                article = {e: root.find(f".//{e}").text or '' for e in [
                    'keywords', 'title', 'subtitle', 'lead_author', 'additional_authors',
                    'site', 'avatar', 'pub_date', 'link', 'cover_image', 'body_html'
                ]}
                articles.append(article)
            except ET.ParseError:
                return f"Error parsing {file_path}"

    articles = sort_list_of_dicts(articles, key="pub_date")
    return json.dumps(articles)

def search_articles(search_str):
    folder_path = 'd:/Websites/AgWaterReact/public/articles'
    search_strs = search_str.replace(',', ' ').replace(';', ' ').split()
    matching_files, matching_articles = [], []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".xml"):
            file_path = os.path.join(folder_path, filename)
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                for element in root.iter():
                    if element.text and any(s in element.text.lower() for s in search_strs):
                        matching_files.append(filename)
                        matching_articles.append(root.find('title').text)
                        break

            except ET.ParseError:
                pass

    return {'article_files': matching_files, 'article_titles': matching_articles}

def update_articles(articles):
    folder_path = 'd:/Websites/AgWaterReact/public/articles'
    articles = json.loads(articles)

    return json.dumps(updated_articles)