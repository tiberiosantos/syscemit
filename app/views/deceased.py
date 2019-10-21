# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import current_user, login_required

from ..decorators import permission_required
from ..forms.deceased import DeceasedForm, DeceasedSearchForm
from ..models.addresses import Address
from ..models.cities import City
from ..models.deceased import Deceased
from ..models.doctors import Doctor
from ..models.graves import Grave
from ..models.registries import Registry

bp = Blueprint('deceased', __name__, url_prefix='/falecidos')


@bp.route('/')
@login_required
def index():
    form = DeceasedSearchForm(request.args)
    search = form.search.data
    search = form.search.data
    criteria = form.criteria.data
    order = form.order.data

    pagination = Deceased.fetch(search, criteria, order, form.page.data)
    deceased = pagination.items
    headers = [('name', 'Nome'), ('city', 'Cidade'),
               ('death_datetime', 'Data de Falecimento'), ('grave', 'Túmulo')]

    return render_template('deceased/index.html',
                           icon='fa-coffin',
                           title='Falecidos',
                           clean_url=url_for('deceased.index'),
                           create_url=url_for('deceased.create'),
                           form=form,
                           search=search,
                           criteria=criteria,
                           order=order,
                           pagination=pagination,
                           headers=headers,
                           deceased=deceased)


@bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def create():
    form = DeceasedForm()
    form.gender.data = bool(form.gender.data)

    if form.birthplace_id.data:
        city = City.get_or_404(form.birthplace_id.data)
        form.birthplace_id.choices = [(city.id,
                                       f'{city.name} - {city.state.name}')]

    if form.home_address_id.data:
        address = Address.get_or_404(form.home_address_id.data)
        form.home_address_id.choices = [
            (address.id, ('{a.street} - {a.district}, {a.city.name} - '
                          '{a.city.state.name}, {a.cep}').format(a=address))]

    if form.death_address_id.data:
        address = Address.get_or_404(form.death_address_id.data)
        form.death_address_id.choices = [
            (address.id, ('{a.street} - {a.district}, {a.city.name} - '
                          '{a.city.state.name}, {a.cep}').format(a=address))]

    if form.doctor_id.data:
        doctor = Doctor.get_or_404(form.doctor_id.data)
        form.doctor_id.choices = [(doctor.id, f'{doctor.name} - {doctor.crm}')]

    if form.grave_id.data:
        grave = Grave.get_or_404(form.grave_id.data)
        form.grave_id.choices = [
            (grave.id, ('{g.street} - {g.number}, {g.zone.description} - '
                        '{g.zone.complement}').format(g=grave))]

    if form.registry_id.data:
        registry = Registry.get_or_404(form.registry_id.data)
        form.registry_id.choices = [
            (registry.id, f'{registry.name} - {registry.city.name}')
        ]

    if form.validate() and request.method == 'POST':
        deceased = Deceased()
        form.populate_obj(deceased)
        deceased.save()
        return jsonify({'redirect': url_for('deceased.index')})

    return render_template('deceased/view.html',
                           icon='fa-coffin',
                           title='Adicionar Falecido',
                           form=form,
                           method='post',
                           color='success')


@bp.route('/<int:id>', methods=['GET', 'PUT'])
@login_required
def edit(id):
    deceased = Deceased.get_or_404(id)
    form = DeceasedForm(request.form, obj=deceased)

    if form.birthplace_id.data:
        city = City.get_or_404(form.birthplace_id.data)
        form.birthplace_id.choices = [(city.id,
                                       f'{city.name} - {city.state.name}')]

    if form.home_address_id.data:
        address = Address.get_or_404(form.home_address_id.data)
        form.home_address_id.choices = [
            (address.id, ('{a.street} - {a.district}, {a.city.name} - '
                          '{a.city.state.name}, {a.cep}').format(a=address))]

    if form.death_address_id.data:
        address = Address.get_or_404(form.death_address_id.data)
        form.death_address_id.choices = [
            (address.id, ('{a.street} - {a.district}, {a.city.name} - '
                          '{a.city.state.name}, {a.cep}').format(a=address))]

    if form.doctor_id.data:
        doctor = Doctor.get_or_404(form.doctor_id.data)
        form.doctor_id.choices = [(doctor.id, f'{doctor.name} - {doctor.crm}')]

    if form.grave_id.data:
        grave = Grave.get_or_404(form.grave_id.data)
        form.grave_id.choices = [
            (grave.id, ('{g.street} - {g.number}, {g.zone.description} - '
                        '{g.zone.complement}').format(g=grave))]

    if form.registry_id.data:
        registry = Registry.get_or_404(form.registry_id.data)
        form.registry_id.choices = [
            (registry.id, f'{registry.name} - {registry.city.name}')
        ]

    if request.args.get('format', '', type=str) == 'view':
        return render_template('deceased/view.html',
                               icon='fa-coffin',
                               title='Falecido',
                               form=form,
                               view=True)

    if form.validate() and current_user.is_admin and request.method == 'PUT':
        form.populate_obj(deceased)
        deceased.update()
        return jsonify({'redirect': url_for('deceased.index')})

    return render_template('deceased/view.html',
                           icon='fa-coffin',
                           title='Editar Falecido',
                           form=form,
                           method='put',
                           color='warning')


@bp.route('/<int:id>', methods=['DELETE'])
@login_required
@permission_required('admin')
def delete(id):
    Deceased.get_or_404(id).delete()
    return '', 204
