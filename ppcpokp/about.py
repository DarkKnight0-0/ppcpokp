from flask import Blueprint, render_template

bp = Blueprint('about', __name__)

@bp.route('/')
def index():
    """显示关于页面"""
    return render_template('about/index.html')