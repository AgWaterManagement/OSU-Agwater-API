from flask import Blueprint, request
from services.article_service import get_articles, get_sites, get_authors, search_articles, update_articles

bp = Blueprint('articles', __name__)

@bp.route("/ArticleList")
def get_articles_route():
    return get_articles()

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
    return search_articles(search_str)
