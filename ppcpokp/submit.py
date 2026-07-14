from flask import Blueprint, render_template, request, flash, redirect, url_for
from ppcpokp.db import get_db

bp = Blueprint('submit', __name__)

@bp.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        # Retrieve form data
        model_name = request.form.get('model_name', '').strip()
        target_outcome = request.form.get('target_outcome', '').strip()  # 单选按钮的值
        pmid = request.form.get('pmid', '').strip()
        title = request.form.get('title', '').strip()
        your_name = request.form.get('your_name', '').strip()
        email = request.form.get('email', '').strip()
        note = request.form.get('note', '').strip()

        # Basic validation
        if not model_name:
            flash('Model Name is required.', 'danger')
            return redirect(url_for('submit.submit'))
        if not target_outcome:
            flash('Please select a Target Outcome.', 'danger')
            return redirect(url_for('submit.submit'))

        # Insert into database
        db = get_db()
        db.execute(
            'INSERT INTO submission (model_name, target_outcome, pmid, title, your_name, email, note)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?)',
            (model_name, target_outcome, pmid, title, your_name, email, note)
        )
        db.commit()

        flash('Submitted successfully. We will examine it and add it to our database. Thank you for your contribution!', 'success')
        return redirect(url_for('submit.submit'))

    # GET request: simply render the form
    return render_template('submit/submit.html')