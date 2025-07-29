from flask import current_app
import os
import json
import xml.etree.ElementTree as ET
#from utils.helpers import sort_list_of_dicts

import PyPDF2 as pypdf
import sqlite3


def get_articleInfo(info_type):
    if info_type not in ['articles', 'sites', 'authors']:
        return json.dumps({'error': 'Invalid article type'})
    
    path = current_app.config.get('AG_WATER_DB_PATH', '/Websites/AgWaterAPI/sqlitedbs/agWater.db')
    info=None
    if not os.path.exists(path):
        return json.dumps({'error': 'articles.json not found'})
    with open(path, 'r', encoding="utf-8") as f:
        data = json.load(f)
        info = data.get(info_type, [])
    if not info:
        return json.dumps({'error': f'No {info_type} found'})
    
    return info

#def get_articles():
#    articles = get_articleInfo('articles')

    # Sort articles by pub_date
#    articles = sort_list_of_dicts(articles, key="pub_date")
#    return json.dumps(articles)

def get_sites():
    articles = get_articleInfo('sites')
    return json.dumps(articles)

def get_authors():
    articles = get_articleInfo('authors')
    return json.dumps(articles)


def search_articles(keywords):
    articles = get_articleInfo('articles')
    matching_articles = []

    search_strs = keywords.lower().split()

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
            #matching_articles.append(article['title'])
            matching_articles.append(article)

    return {'articles': matching_articles}

def search_resources(keywords):
    # this function scans filenames in the resources directory for keywords
    resources_path = 'd:/AgWaterLLM/source_materials'
    if not os.path.exists(resources_path):
        return json.dumps({'error': 'Resources directory not found'})
    matching_files = []
    search_strs = keywords.lower().split()

    # iterate through PDF files in this folder, opening each file
    # and calling extract_text_from_pdf to extract the text

    for file in os.listdir(resources_path):
        file_path = os.path.join(resources_path, file)
        if not os.path.isfile(file_path):
            continue  # Skip directories or non-file items
        if file.lower().endswith('.pdf'):
            # Check if any of the search strings are in the filename
            # If so, add the file to the matching_files list
            if any(search_str in file.lower() for search_str in search_strs):
                matching_files.append(file)

            # If not, extract the text from the PDF and check if any of the search strings are in the text
            elif any(search_str in extract_text_from_pdf(file_path).lower() for search_str in search_strs):
                matching_files.append(file)

    if not matching_files:
        return json.dumps({'error': 'No matching resources found'})
    return json.dumps({'matching_files': matching_files})


def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as file:
        reader = pypdf.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text


def extract_metadata_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as file:
        reader = pypdf.PdfReader(file)

        metadata = reader.metadata
        return metadata
        #print(f"Author: {metadata.author}")
        #print(f"Title: {metadata.title}")
        #print(f"Creation Date: {metadata.creation_date}")

def update_articles(articles):

    articles = get_articleInfo('articles')
    sites = get_articleInfo('sites')
    authors = get_articleInfo('authors')
    return json.dumps(articles)


def get_article_list():
    path = current_app.config.get('AG_WATER_DB_PATH', '/Websites/AgWaterAPI/sqlitedbs/agWater.db')

    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, tags, validated, title, subtitle, lead_author, additional_authors, avatar, 
               lead_site, additional_sites, pub_date, url, cover_image, abstract, body_html
        FROM Articles
        WHERE validated = 1
        ORDER BY pub_date DESC
    """)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    articles = []
    for row in rows:
        article = dict(zip(columns, row))
        # Convert JSON fields back to Python objects
        for field in ['tags', 'additional_authors', 'additional_sites']:
            if article[field]:
                try:
                    article[field] = json.loads(article[field])
                except Exception:
                    article[field] = []
            else:
                article[field] = []
        articles.append(article)
    conn.close()
    return articles


if __name__ == "__main__":
    # Example usage
    print(get_article_list())
    # print(get_sites())
    # print(get_authors())
    # print(search_articles("water"))
    # print(search_resources("water"))
    # print(extract_text_from_pdf("path_to_pdf.pdf"))
    # print(extract_metadata_from_pdf("path_to_pdf.pdf"))