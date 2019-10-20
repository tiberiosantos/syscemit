# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import current_user, login_required

from ..decorators import permission_required
from ..forms.zones import COLUMNS, ZoneForm, ZoneSearchForm
from ..models import Zone

bp = Blueprint('zones', __name__, url_prefix='/regioes')


@bp.route('/')
@login_required
def index():
    form = ZoneSearchForm(request.args)
    grid = request.args.get('grid', 0, type=bool)
    search = form.search.data
    criteria = form.criteria.data
    order = form.order.data

    pagination = Zone.fetch(search, criteria, order, form.page.data)
    zones = pagination.items
    if request.is_xhr and not grid:
        return jsonify({
            'result': [{
                'id': z.id,
                'name': f'{z.description} - {z.complement}'
            } for z in zones]
        })

    return render_template('zones/index.html',
                           icon='fa-map-marked-alt',
                           title='Regiões',
                           clean_url=url_for('zones.index'),
                           create_url=url_for('zones.create'),
                           form=form,
                           search=search,
                           criteria=criteria,
                           order=order,
                           pagination=pagination,
                           headers=COLUMNS,
                           zones=zones)


@bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def create():
    form = ZoneForm()

    if form.validate() and request.method == 'POST':
        doctor = Zone()
        form.populate_obj(doctor)
        doctor.save()
        return jsonify({'redirect': url_for('zones.index')})

    return render_template('zones/view.html',
                           icon='fa-map-marked-alt',
                           title='Adicionar Região',
                           form=form,
                           method='post',
                           color='success')


@bp.route('/<int:id>', methods=['GET', 'PUT'])
@login_required
def edit(id):
    doctor = Zone.get_or_404(id)
    form = ZoneForm(request.form, obj=doctor)

    if request.args.get('format', '', type=str) == 'view':
        return render_template('zones/view.html',
                               icon='fa-map-marked-alt',
                               title='Região',
                               form=form,
                               view=True)

    if form.validate() and current_user.is_admin and request.method == 'PUT':
        form.populate_obj(doctor)
        doctor.update()
        return jsonify({'redirect': url_for('zones.index')})

    return render_template('zones/view.html',
                           icon='fa-map-marked-alt',
                           title='Editar Região',
                           form=form,
                           method='put',
                           color='warning')


@bp.route('/<int:id>', methods=['DELETE'])
@login_required
@permission_required('admin')
def delete(id):
    Zone.get_or_404(id).delete()
    return '', 204
