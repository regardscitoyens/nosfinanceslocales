# -*- coding: utf-8 -*-

import os
from pyramid.view import view_config
from pyramid.response import FileResponse
from cornice import Service
from cornice.resource import resource, view
from .models import AdminZoneFinance, DBSession, AdminZone
from .maps import map_registry, MAPS_CONFIG

city_search = Service(name='search_city', path='/search_city', description="city search")

@city_search.get()
def get_info(request):
    term = self.request.matchdict['term']
    result = DBSession.query(AdminZone.id, AdminZone.name, AdminZone.code_insee).filter()

@resource(collection_path='/timemaps', path='/timemap/{id}')
class TimeMap(object):
    def __init__(self, request):
        self.request = request
    def get(self):
        id = self.request.matchdict['id']
        return {'results': {'var_name': id, 'maps': [m.info for m in map_registry[id]]}}
    def collection_get(self):
        return {'results': [{'var_name': key, 'maps': [m.info for m in map_registry[key]]} for key in MAPS_CONFIG.keys()]}

@resource(collection_path='/finance', path='/finance/{id}')
class AZFinance(object):
    def __init__(self, request):
        self.request = request
    def get(self):
        id = self.request.matchdict['id']
        res = DBSession.query(AdminZone.name, AdminZone.code_insee, AdminZone.code_dep, AdminZoneFinance.year, AdminZoneFinance.data).join(AdminZone, AdminZone.id==AdminZoneFinance.adminzone_id).filter(AdminZone.id==id).order_by('year').all()
        return {'results': res}


# view for development purpose
from pyramid.response import FileResponse
def index(request):
    here = os.path.dirname(__file__)
    html_file = os.path.join(here, 'client_app', 'index.html')
    return FileResponse(html_file)
