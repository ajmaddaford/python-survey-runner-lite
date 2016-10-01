from flask import Flask, request, redirect, jsonify, render_template, g
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
    schema = g.get('schema', None)
    if schema is None:
        schema_file = open(schema_filename, encoding="utf8")
        schema_json = json.load(schema_file)
        g.schema = schema_json
    return g.schema

def get_block_json(survey_id, block_id):
    survey_json = load_schema_file(survey_id + '.json')
    for block in survey_json['groups'][0]['blocks']:
        if block['id'] == block_id:
            return block

def get_next_block_id(block_id):
    survey_json = g.schema
    next_block = False
    for block in survey_json['groups'][0]['blocks']:
        if next_block:
            return block['id']
        if block['id'] == block_id:
            next_block = True
    return None

def store_data(user_id, block_id, form_data):
    s = json.dumps(form_data)
    existing_data = QuestionnaireData.query.filter_by(user_id=user_id).first()
    if existing_data:
        existing_data.data = s
        db_session.add(existing_data)
    else:
        q_data = QuestionnaireData(user_id, s)
        db_session.add(q_data)
    db_session.commit()

def load_data(user_id, block_id):
    data = g.get('questionnaire_data', None)
    if data:
        return json.loads(data)

    questionnaire_data = QuestionnaireData.query.filter_by(user_id=user_id).first()
    if questionnaire_data:
        data = g.questionnaire_data = questionnaire_data.data
        return json.loads(data)

    return None

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
        next_block = get_next_block_id(block_id)
        return redirect('/survey/' + survey_id + '/' + next_block)
    return render_template('survey.html', form=f)

if __name__ == '__main__':
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
