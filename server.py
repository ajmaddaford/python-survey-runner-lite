from flask import Flask, request, jsonify
import settings
import logging
from structlog import wrap_logger
import os
import json

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

@app.route('/survey/<survey_id>/<block_id>', methods=['GET'])
def block(survey_id, block_id):
    block_json = get_block_json(survey_id, block_id)
    return jsonify(block_json)

if __name__ == '__main__':
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
