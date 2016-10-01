from flask import Flask, request, jsonify, render_template, g
from flask_sqlalchemy import SQLAlchemy
import settings
import logging
from structlog import wrap_logger
import os
import json
import form
from database import init_db, db_session
from models import QuestionnaireData

app = Flask(__name__)
init_db()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))

def load_schema_file(schema_filename):
    schema_file = open(schema_filename, encoding="utf8")
    return json.load(schema_file)

def get_block_json(survey_id, block_id):
    survey_json = load_schema_file(survey_id + '.json')
    for block in survey_json['groups'][0]['blocks']:
        if block['id'] == block_id:
            return block

def store_data(user_id, block_id, form_data):
    s = json.dumps(form_data)
    q_data = QuestionnaireData(user_id, s)
    db_session.add(q_data)
    db_session.commit()

def load_data(user_id, block_id):
    data = g.get('questionnaire_data', None)
    if data is None:
        data = QuestionnaireData.query.filter_by(user_id=user_id).first()
        g.questionnaire_data = data.data
    return json.loads(data.data)

@app.route('/survey/<survey_id>', methods=['GET'])
def survey(survey_id):
    survey_json = load_schema_file(survey_id + '.json')
    return jsonify(survey_json)

@app.route('/survey/<survey_id>/<block_id>', methods=['GET', 'POST'])
def block(survey_id, block_id):
    user_id = 1
    data = load_data(user_id, block_id)
    block_json = get_block_json(survey_id, block_id)
    f = form.generate_form(block_json, data)
    if f.validate_on_submit():
        store_data(user_id, block_id, f.data)
        return render_template('thank-you.html')
    return render_template('survey.html', form=f)

if __name__ == '__main__':
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
