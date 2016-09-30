from flask_wtf import Form
from wtforms import SelectField, IntegerField, DateField, SelectMultipleField, TextAreaField
from wtforms.widgets import TextArea, TextInput, RadioInput, CheckboxInput, ListWidget
from wtforms import validators

def generate_form(block_json):
    class QuestionnaireForm(Form):
        pass

    for section in block_json['sections']:
        for question in section['questions']:
            for answer in question['answers']:
                name = answer['label'] if answer['label'] else question['title']
                setattr(QuestionnaireForm, answer['id'], get_field(answer, name))

    form = QuestionnaireForm(csrf_enabled=False)
    return form

def get_field(answer, label):
    if answer['type'] == 'Radio':
        field = SelectField(label=label, description=answer['guidance'], choices=build_choices(answer['options']), widget=ListWidget(), option_widget=RadioInput())
    if answer['type'] == 'Checkbox':
        field = SelectMultipleField(label=label, description=answer.guidance, choices=build_choices(answer['options']), widget=ListWidget(), option_widget=CheckboxInput())
    if answer['type'] == 'Date':
        field = DateField(label=label, description=answer['guidance'], widget=TextInput(), validators=[validators.optional()])
    if answer['type'] == 'Currency' or answer['type'] == 'PositiveInteger' or answer['type'] == 'Integer':
        field = IntegerField(label=label, description=answer['guidance'], widget=TextInput())
    if answer['type'] == 'Textarea':
        field = TextAreaField(label=label, description=answer['guidance'], widget=TextArea())

    return field


def build_choices(options):
    choices = []
    for option in options:
        choices.append((option['label'], option['value']))
    return choices