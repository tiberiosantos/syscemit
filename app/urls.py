# -*- coding: utf-8 -*-

from .utils.helpers import HandleError
from .views import (
    addresses, auth, cities, deceased, doctors, graves, main, registries, users,
    zones
)


def init_app(app):
    for blueprint in (
        addresses, auth, cities, deceased, doctors, graves, main, registries,
        users, zones
    ):
        app.register_blueprint(blueprint.bp)

    # errors
    errors = {
        403: u'Acesso Negado!',
        404: u'Página não Encontrada!',
        500: u'Erro Interno do Servidor!'
    }
    for code, message in errors.items():
        app.errorhandler(code)(HandleError('error.html', message))
