from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from urllib.parse import urlparse

from ppcpokp.db import get_db

bp = Blueprint('search', __name__)


@bp.route('/search')
def index():
    return render_template('search/index.html')

@bp.route('/search/batch')
def batch():
    return render_template('search/batch.html')

@bp.route('/search/development')
def development():
    return render_template('search/development.html', search_type=search_type())

@bp.route('/search/validation')
def validation():
    return render_template('search/validation.html', search_type=search_type())

@bp.route('/search/comparison')
def comparison():
    return render_template('search/comparison.html', search_type=search_type())

def search_type():
    referrer = request.referrer
    if referrer:
        parsed = urlparse(referrer)
        # 判断来源路径
        if parsed.path == '/search/batch':
            return f'<a href="{referrer}">Batch Search</a>'
        else:
            return f'<a href="{referrer}">Advanced Search</a>'