# download.py
from flask import Blueprint, render_template, send_from_directory, abort, request, jsonify
import os

from ppcpokp.db import get_db, ensure_download_clicks_table

bp = Blueprint('download', __name__)

# 假设 CSV/PDF 文件存放在项目根目录下的 downloads 文件夹中
DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'downloads')

# 确保下载目录存在
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# 文件信息字典：包含显示名称、描述和所属分组
FILE_INFO = {
    # Basic Information 组
    'Model Development.xlsx': {
        'name': 'Model Development',
        'description': 'Collection of model development study information.',
        'group': 'basic'
    },
    'Model Validation.xlsx': {
        'name': 'Model Validation',
        'description': 'Collection of model validation study information.',
        'group': 'basic'
    },
    'Model Comparison.xlsx': {
        'name': 'Model Comparison',
        'description': 'Collection of model comparison study information.',
        'group': 'basic'
    },
    # Supplementary Information 组
    'Model Type.xlsx': {
        'name': 'Model Type',
        'description': 'Classification of model types.',
        'group': 'supplementary'
    },
    'Model Variable.pdf': {
        'name': 'Model Variable',
        'description': 'Classification of model variables.',
        'group': 'supplementary'
    },
    'Population Category.pdf': {
        'name': 'Population Category',
        'description': 'Classification of target population categories.',
        'group': 'supplementary'
    },
    'Surgical Specialty Category.pdf': {
        'name': 'Surgical Specialty Category',
        'description': 'Classification of surgical specialty categories.',
        'group': 'supplementary'
    },
    'Clinical Application Modality.pdf': {
        'name': 'Clinical Application Modality',
        'description': 'Classification of clinical application modalities.',
        'group': 'supplementary'
    },
    'Model Score System.xlsx': {
        'name': 'Model Score System',
        'description': 'Utility of prediction model score system.',
        'group': 'supplementary'
    }
}

# 定义 Basic Information 文件的显示顺序
BASIC_FILE_ORDER = [
    'Model Development.xlsx',
    'Model Validation.xlsx',
    'Model Comparison.xlsx'
]

# 定义 Supplementary Information 文件的显示顺序
SUPPLEMENTARY_FILE_ORDER = [
    'Model Type.xlsx',
    'Model Variable.pdf',
    'Population Category.pdf',
    'Surgical Specialty Category.pdf',
    'Clinical Application Modality.pdf',
    'Model Score System.xlsx'
]

@bp.route('/')
def index():
    """显示下载页面，分为 Basic Information 和 Supplementary Information 两组表格"""
    basic_files = []
    for filename in BASIC_FILE_ORDER:
        if filename in FILE_INFO:
            info = FILE_INFO[filename]
            basic_files.append({
                'filename': filename,
                'name': info['name'],
                'description': info['description'],
                'file_type': 'pdf' if filename.endswith('.pdf') else 'xlsx'
            })

    supplementary_files = []
    for filename in SUPPLEMENTARY_FILE_ORDER:
        if filename in FILE_INFO:
            info = FILE_INFO[filename]
            supplementary_files.append({
                'filename': filename,
                'name': info['name'],
                'description': info['description'],
                'file_type': 'pdf' if filename.endswith('.pdf') else 'xlsx'
            })

    return render_template('download/index.html', 
                         basic_files=basic_files, 
                         supplementary_files=supplementary_files)

@bp.route('/download/<filename>')
def download_file(filename):
    """处理文件下载，仅允许预定义的文件名"""
    if filename not in FILE_INFO:
        abort(404)  # 文件不存在或不允许下载
    try:
        return send_from_directory(
            DOWNLOADS_DIR,
            filename,
            as_attachment=True,
            download_name=filename  # Flask 2.0+ 使用 download_name
        )
    except FileNotFoundError:
        abort(404)


@bp.route('/track-click', methods=['POST'])
def track_click():
    """记录下载按钮点击次数。"""
    payload = request.get_json(silent=True) or {}
    filename = payload.get('filename')

    if not filename or filename not in FILE_INFO:
        return jsonify({'error': 'Invalid filename'}), 400

    db = get_db()
    try:
        ensure_download_clicks_table(db)
        db.execute(
            '''
            INSERT INTO download_clicks (filename, click_count)
            VALUES (?, 1)
            ON CONFLICT(filename)
            DO UPDATE SET click_count = click_count + 1
            ''',
            (filename,)
        )
        db.commit()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': f'Database Error: {str(e)}'}), 500


@bp.route('/total-clicks', methods=['GET'])
def total_clicks():
    """返回所有下载按钮点击总次数。"""
    db = get_db()
    try:
        ensure_download_clicks_table(db)
        row = db.execute('SELECT COALESCE(SUM(click_count), 0) AS total FROM download_clicks').fetchone()
        total = int(row['total']) if row and row['total'] is not None else 0
        return jsonify({'total_downloads': total})
    except Exception as e:
        return jsonify({'error': f'Database Error: {str(e)}'}), 500