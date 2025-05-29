import os
import json
import xml.etree.ElementTree as ET
from utils.helpers import sort_list_of_dicts

''' deprecated '''
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
    folder_path = '/Websites/AgWaterWebsite/public/articles/'

    search_strs = search_str.replace(',', ' ').replace(';', ' ').split()
    matching_articles = []

    # load articles.json to get the list of articles
    articles_file_path = os.path.join(folder_path, 'articles.json')
    if not os.path.exists(articles_file_path):
        return json.dumps({'article_titles': []})
    
    with open(articles_file_path, 'r') as f:
        articles_data = json.load(f)

        # iterate through articles json and check if any of the search strings are in the title, abstract, tags, authors, sites or body_html
        for article in articles_data:
            title = article.get('title', '').lower()
            abstract = article.get('abstract', '').lower()
            tags = [tag.lower() for tag in article.get('tags', [])]
            authors = [article.get('lead_author', '').lower()] + [a.lower() for a in article.get('additional_authors', [])]
            sites = [article.get('lead_site', '').lower()] + [s.lower() for s in article.get('additional_sites', [])]
            body_html = article.get('body_html', '').lower()

            if any(search_str in title for search_str in search_strs) or \
               any(search_str in abstract for search_str in search_strs) or \
               any(search_str in tag for tag in tags for search_str in search_strs) or \
               any(search_str in author for author in authors for search_str in search_strs) or \
               any(search_str in site for site in sites for search_str in search_strs) or \
               any(search_str in body_html for search_str in search_strs):
                matching_articles.append(article['title'])

    return {'article_titles': matching_articles}

def update_articles(articles):
    folder_path = 'd:/Websites/AgWaterReact/public/articles'
    articles = json.loads(articles)

    return json.dumps(updated_articles)