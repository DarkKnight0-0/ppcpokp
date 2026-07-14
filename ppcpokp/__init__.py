import os

from flask import Flask
from .config import Config
from . import filters

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),  # 从环境变量获取，默认为 'dev'（仅用于开发）
        DATABASE=os.path.join(app.instance_path, 'ppcpokp.db'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 注册所有过滤器
    app.jinja_env.filters.update({
        'remove_parentheses': filters.remove_parentheses,
        'remove_all_brackets': filters.remove_all_brackets,
        'strip_brackets': filters.strip_brackets,
        'capitalize_first': filters.capitalize_first,
    })

    from . import db
    db.init_app(app)

    from . import browse
    app.register_blueprint(browse.bp)

    from . import search
    app.register_blueprint(search.bp)

    from . import help
    app.register_blueprint(help.bp)

    from . import index
    app.register_blueprint(index.bp)

    from . import chart
    app.register_blueprint(chart.bp)

    from . import tool
    app.register_blueprint(tool.bp)

    from . import submit
    app.register_blueprint(submit.bp)

    from ppcpokp.download import bp as download_bp
    app.register_blueprint(download_bp, url_prefix='/download')

    from ppcpokp.about import bp as about_bp
    app.register_blueprint(about_bp, url_prefix='/about')

    return app