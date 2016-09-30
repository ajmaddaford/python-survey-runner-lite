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

@app.route('/survey/<survey_id>', methods=['GET'])
def survey(survey_id):
    survey_json = load_schema_file(survey_id + '.json')
    return jsonify(survey_json)

if __name__ == '__main__':
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
