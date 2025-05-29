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


def get_articleInfo(info_type):
    if info_type not in ['articles', 'sites', 'authors']:
        return json.dumps({'error': 'Invalid article type'})
    
    path = '/Websites/AgWaterAPI/services/articles.json'
    info=None
    if not os.path.exists(path):
        return json.dumps({'error': 'articles.json not found'})
    with open(path, 'r') as f:
        data = json.load(f)
        info = data.get(info_type, [])
    if not info:
        return json.dumps({'error': f'No {info_type} found'})
    
    return info

def get_articles():
    articles = get_articleInfo('articles')

    # Sort articles by pub_date
    articles = sort_list_of_dicts(articles, key="pub_date")
    return json.dumps(articles)

def get_sites():
    articles = get_articleInfo('sites')
    return json.dumps(articles)

def get_authors():
    articles = get_articleInfo('authors')
    return json.dumps(articles)


def search_articles(search_str):
    articles = get_articleInfo('articles')
    matching_articles = []
    
    # iterate through articles json and check if any of the search strings are in the title, abstract, tags, authors, sites or body_html
    for article in articles:
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