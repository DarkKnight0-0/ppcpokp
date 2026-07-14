from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from ppcpokp.db import get_db

bp = Blueprint('help', __name__)

@bp.route('/help')
def index():
    return render_template('help/index.html')
