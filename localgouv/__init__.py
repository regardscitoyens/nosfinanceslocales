"""Main entry point
"""
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
    )

def main(global_config, **settings):
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    # for dev purpose
    config.add_static_view('static', 'client_app/static', cache_max_age=3600)
    config.add_static_view('templates', 'client_app/templates', cache_max_age=3600)
    config.add_view('localgouv.views.index', route_name='index')
    config.add_route('index', '/')
    config.include("cornice")
    config.scan("localgouv.views")
    return config.make_wsgi_app()
