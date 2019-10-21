# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import (DateField, IntegerField, RadioField, SelectField,
                     StringField, SubmitField)
from wtforms.validators import InputRequired, Length, Optional
from wtforms.widgets import TextArea, html5

from ..models.civil_states import CivilState
from ..models.ethnicities import Ethnicity
from ..utils.forms import SearchField

COLUMNS = [('name', 'Nome'), ('age', 'Idade'),
           ('birth_date', 'Data de Nascimento'),
           ('death_datetime', 'Data de Falecimento'), ('gender', 'Genero'),
           ('cause', 'Causa da Morte'), ('registration', 'Matrícula do Óbito'),
           ('number', 'Numero'), ('complement', 'Complemento'),
           ('birthplace', 'Local de Nascimento'),
           ('civil_state', 'Estado Civil'),
           ('home_address', 'Endereço da Casa'),
           ('death_address', 'Local do falecimento'), ('doctor', 'Medico'),
           ('ethnicity', 'Etnia'), ('grave', 'Tumulo'),
           ('registry', 'Cartorio'), ('filiations', 'Filiação')]
ORDERS = [('asc', 'Ascendente'), ('desc', 'Descente')]


class DeceasedForm(FlaskForm):
    name = StringField('Nome', [Optional(), Length(1, 255)])
    age = IntegerField('Idade', [Optional()], widget=html5.NumberInput(min=0))
    birth_date = DateField('Data de Nascimento', [Optional()],
                           format='%d/%m/%Y')
    death_datetime = DateField('Data de Falecimento', [
        InputRequired(message='Insira a Data de Falecimento!'),
    ],
                               format='%d/%m/%Y %H:%M')
    gender = RadioField('Genêro', [InputRequired(message='Insira o Genêro!')],
                        choices=[(0, 'Masculino'), (1, 'Feminino')])
    cause = StringField(
        'Causa da Morte',
        [InputRequired(message='Insira a Causa da Morte!'),
         Length(1, 1500)],
        widget=TextArea())
    registration = StringField(
        'Matrícula do Óbito',
        [InputRequired(message='Insira a Matrícula!'),
         Length(1, 40)])
    birthplace_id = SelectField('Local de Nascimento', [Optional()],
                                choices=(),
                                coerce=int)
    civil_state_id = SelectField('Estado Civil', [Optional()],
                                 choices=(),
                                 coerce=int)
    home_address_id = SelectField('Endereço Residencial', [Optional()],
                                  choices=(),
                                  coerce=int)
    home_address_number = StringField('Número', [Optional(), Length(1, 5)])
    home_address_complement = StringField(
        'Complemento', [Optional(), Length(1, 255)])
    death_address_id = SelectField(
        'Endereço de Falecimento',
        [InputRequired('Selecione o Endereço de Falecimento')],
        choices=(),
        coerce=int)
    death_address_number = StringField('Número', [Optional(), Length(1, 5)])
    death_address_complement = StringField(
        'Complemento', [Optional(), Length(1, 255)])
    doctor_id = SelectField(
        'Médico', [InputRequired(message='Insira o nome do Médico!')],
        choices=(),
        coerce=int)
    ethnicity_id = SelectField('Etnia',
                               [InputRequired(message='Insira a Etnia!')],
                               choices=(),
                               coerce=int)
    grave_id = SelectField('Tumulo',
                           [InputRequired(message='Insira o Tumulo!')],
                           choices=(),
                           coerce=int)
    registry_id = SelectField('Cartório',
                              [InputRequired(message='Insira o Cartório!')],
                              choices=(),
                              coerce=int)
    filiations = StringField('Filiação', [Optional(), Length(1, 255)])
    submit = SubmitField('Salvar')

    def __init__(self, *args, **kwargs):
        super(DeceasedForm, self).__init__(*args, **kwargs)
        self.ethnicity_id.choices = [(e.id, e.description)
                                     for e in Ethnicity.query.order_by(
                                         Ethnicity.description.asc()).all()]
        self.ethnicity_id.choices.insert(0, (0, ''))
        self.civil_state_id.choices = [(e.id, e.description)
                                       for e in CivilState.query.order_by(
                                           CivilState.description.asc()).all()]
        self.civil_state_id.choices.insert(0, (0, ''))


class DeceasedSearchForm(FlaskForm):
    page = IntegerField('Página', default=1)
    search = SearchField('Buscar falecido ...')
    criteria = SelectField('Filtrar por', choices=COLUMNS, default='name')
    order = SelectField('Ordem', choices=ORDERS, default='asc')