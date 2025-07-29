from flask import Blueprint, request
from services.article_service import get_sites, get_authors, search_articles, update_articles, search_resources, get_article_list
import sqlite3
import globals

bp = Blueprint('articles', __name__)


DB_PATH = "D:/Websites/AgWaterAPI/sqliteDBs/agWater.db"


@bp.route("/articles/list")
def get_articles_list_route():
    globals.articles_logger.info("Fetching article list")
    try:
        articles = get_article_list()
        return {'success': True, 'articles': articles}
    except Exception as e:
        globals.articles_logger.error(f"Error fetching article list: {e}")
        return {'success': False, 'message': f"Error fetching article list: {str(e)}"}, 500



@bp.route("/ArticleSites")
def get_sites_route():
    return get_sites()

@bp.route("/ArticleAuthors")
def get_authors_route():
    return get_authors()

@bp.route("/UpdateArticles")
def update_articles_route():   # not correct
    articles = request.args.get('articles', '')
    return update_articles(articles)

@bp.route("/SearchArticles")
def search_articles_route():
    search_str = request.args.get('keywords', '').lower()
    results  = search_articles(search_str)
    return { 'success': True, 'results': results } if results else {'success': False, 'message': 'No articles found.'}

@bp.route("/SearchResources")
def search_resources_route():
    search_str = request.args.get('keywords', '').lower()
    results  = search_resources(search_str)
    return { 'success': True, 'results': results } if results else {'success': False, 'message': 'No articles found.'}

@bp.route("/articles/submit", methods=["POST"])
def submit_article_route():
    article_data = request.get_json()
    if not article_data:
        return {'success': False, 'message': 'No article data provided.'}, 400
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Assuming article_data is a dict with keys matching the Articles table columns
        columns = ', '.join(article_data.keys())
        placeholders = ', '.join(['?'] * len(article_data))
        values = tuple(article_data.values())

        globals.articles_logger.info(f"INSERT INTO ArticlesTest ({columns}) VALUES ({placeholders})")
        globals.articles_logger.info(f"Values: {values}")
        #cursor.execute(f"INSERT INTO Articles ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        conn.close()
        return {'success': True, 'message': 'Article submitted successfully.'}
    except Exception as e:
        return {'success': False, 'message': f'Article submission failed: {str(e)}'}, 500
