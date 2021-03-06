# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import (
    FormField, IntegerField, SelectField, StringField, SubmitField
)
from wtforms.validators import InputRequired, Length, Optional

from ..utils.forms import ORDERS, get_fields


class ZoneForm(FlaskForm):
    description = StringField(
        'Descrição',
        [InputRequired(message='Insira o nome da região!'),
         Length(1, 255)]
    )
    complement = StringField('Complemento', [Optional(), Length(1, 20)])
    submit = SubmitField('Salvar')


class ZoneHeadersForm(FlaskForm):
    description = StringField('Descrição')
    complement = StringField('Complemento')


class ZoneSearchForm(FlaskForm):
    page = IntegerField('Página', default=1)
    filters = FormField(ZoneHeadersForm)
    criteria = SelectField(
        'Ordenar por',
        choices=get_fields(ZoneHeadersForm),
        default='description'
    )
    order = SelectField('Ordem', choices=ORDERS, default='asc')
