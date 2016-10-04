from wtforms.widgets import TextInput
from wtforms.widgets import html_params, HTMLString

class CurrencyInput(TextInput):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        html = ['<label %s>%s</label>' % (html_params(_for=field.id, **kwargs), field.label.text)]
        html.append('<div class="input-type input-type--currency" data-type="£">')
        html.append('<input />')
        return HTMLString(u''.join(html))
