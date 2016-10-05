from flask import Flask, request, redirect, jsonify, render_template, g, url_for
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

def get_block_json(survey_id, group_id, block_id):
    survey_json = load_schema_file(survey_id + '.json')

    repetition_index = 0
    if "_" in group_id:
        group_id, repetition_index = group_id.split("_")

    for group in survey_json['groups']:
        if group['id'] == group_id:
            for block in group['blocks']:
                if block['id'] == block_id:
                    return block

def get_first_block_id_in_group(survey_id, group_id):
    survey_json = load_schema_file(survey_id + '.json')

    repetition_index = 0
    if "_" in group_id:
        group_id, repetition_index = group_id.split("_")

    for group in survey_json['groups']:
        if group['id'] == group_id:
            return group['blocks'][0]['id']

def get_next_ids(answers, group_id, block_id):
    survey_json = g.schema

    repetition_index = 0
    if "_" in group_id:
        group_id, repetition_index = group_id.split("_")

    group_ids = [group['id'] for group in survey_json['groups']]
    current_group_id_index = group_ids.index(group_id)
    is_last_group = (current_group_id_index + 1) == len(group_ids)
    group_json = survey_json['groups'][current_group_id_index]

    block_ids = [block['id'] for block in survey_json['groups'][current_group_id_index]['blocks']]
    current_block_id_index = block_ids.index(block_id)
    is_last_block_in_group = (current_block_id_index + 1) == len(block_ids)

    if not is_last_block_in_group:
        return group_id + "_" + str(repetition_index), block_ids[current_block_id_index + 1]

    # Must be last block in group!
    if 'routing_rules' in group_json and group_json['routing_rules'][0]['repeat']:
        answer_id = group_json['routing_rules'][0]['repeat']['answer_id']
        answer = int(answers[answer_id])
        if (int(repetition_index) + 1) <= answer:
            # Here we go again..
            # Redirect to first block in repeating group
            return group_id + '_' + str(int(repetition_index) + 1), None
        else:
            # Last block in group and last repetition_index
            # Redirect to next group
            if not is_last_group:
                return group_ids[current_group_id_index + 1], None

    # Last block and no routing rules - go to next group
    return group_ids[current_group_id_index + 1], None

    return None, None

def store_data(user_id, block_id, form_data):
    existing_data = QuestionnaireData.query.filter_by(user_id=user_id).first()
    if existing_data:
        data = json.loads(existing_data.data)
        answers = data['answers']
        answers.update(form_data)
        data['answers'] = answers
        existing_data.data = json.dumps(data)
        db_session.add(existing_data)
    else:
        data = {}
        data['answers'] = {form_data}
        q_data = QuestionnaireData(user_id, json.dumps(data))
        db_session.add(q_data)
    db_session.commit()

def load_data(user_id):
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

@app.route('/survey/<survey_id>/answers', methods=['GET'])
def answers(survey_id):
    user_id = 1
    data = load_data(user_id)
    return jsonify(data)

@app.route('/survey/<survey_id>/<group_id>', defaults={'block_id': None}, methods=['GET', 'POST'])
@app.route('/survey/<survey_id>/<group_id>/<block_id>', methods=['GET', 'POST'])
def block(survey_id, group_id, block_id):
    user_id = 1
    data = load_data(user_id)

    if block_id is None:
        block_id = get_first_block_id_in_group(survey_id, group_id)
        return redirect(url_for('block', survey_id=survey_id, group_id=group_id, block_id=block_id))

    if data and block_id in data['answers']:
        answers = data['answers']
    else:
        answers = None
    block_json = get_block_json(survey_id, group_id, block_id)
    f = form.generate_form(block_json, answers)
    if f.validate_on_submit():
        store_data(user_id, block_id, f.data)
        next_group_id, next_block_id = get_next_ids(data['answers'], group_id, block_id)
        return redirect(url_for('block', survey_id=survey_id, group_id=next_group_id, block_id=next_block_id))
    return render_template('survey.html', form=f, schema=block_json)

if __name__ == '__main__':
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
