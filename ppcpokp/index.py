from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from ppcpokp.db import get_db

bp = Blueprint('index', __name__)

@bp.route('/')
def index():
    db = get_db()
    data = db.execute(
            'SELECT * FROM development ORDER BY publication_year DESC, pmid DESC LIMIT 4').fetchall()
    
    # 将 Row 对象转换为字典列表
    data_dict = []
    for row in data:
        data_dict.append(dict(row))
    return render_template('index/index.html', data=data_dict)