from flask import Flask, request, jsonify, render_template
import settings
import logging
from structlog import wrap_logger
import os
import json
import form

app = Flask(__name__)

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

@app.route('/survey/<survey_id>', methods=['GET'])
def survey(survey_id):
    survey_json = load_schema_file(survey_id + '.json')
    return jsonify(survey_json)

@app.route('/survey/<survey_id>/<block_id>', methods=['GET', 'POST'])
def block(survey_id, block_id):
    block_json = get_block_json(survey_id, block_id)
    f = form.generate_form(block_json)
    if f.validate_on_submit():
        return render_template('thank-you.html')
    return render_template('survey.html', form=f)

if __name__ == '__main__':
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
