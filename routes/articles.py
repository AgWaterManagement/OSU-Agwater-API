from flask import Blueprint, request
from services.article_service import get_article_list, search_articles, update_articles

bp = Blueprint('articles', __name__)

@bp.route("/GetArticleList")
def get_article_list_route():
    return get_article_list()

@bp.route("/Update")
def update_articles_route():
    articles = request.args.get('articles', '')
    return update_articles(articles)


@bp.route("/Search")
def search_articles_route():
    search_str = request.args.get('search', '').lower()
    return search_articles(search_str)
