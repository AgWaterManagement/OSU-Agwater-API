from flask import Blueprint, request
from services.article_service import get_articles, get_sites, get_authors, search_articles, update_articles

bp = Blueprint('articles', __name__)

@bp.route("/GetArticleList")
def get_articles_route():
    return get_articles()

@bp.route("/GetArticleSites")
def get_sites_route():
    return get_sites()

@bp.route("/GetArticleAuthors")
def get_authors_route():
    return get_authors()


@bp.route("/Update")
def update_articles_route():
    articles = request.args.get('articles', '')
    return update_articles(articles)


@bp.route("/Search")
def search_articles_route():
    search_str = request.args.get('search', '').lower()
    return search_articles(search_str)
