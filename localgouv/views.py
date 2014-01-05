""" Cornice services.
"""
from pyramid.view import view_config
from pyramid.response import FileResponse
from cornice import Service
from cornice.resource import resource, view
from .models import AdminZoneFinance, DBSession, AdminZone
from .maps import MapRegistry

city_search = Service(name='city_search', path='/search_city', description="city search")

@city_search.get()
def get_info(request):
    term = self.request.matchdict['term']
    result = DBSession.query(AdminZone.id, AdminZone.name, AdminZone.code_insee).filter()

@resource(collection_path='/maps', path='/map/{id}')
class Maps(object):
    def __init__(self, request):
        self.request = request
    def get(self):
        id = self.request.matchdict['id']
        return {'results': res}

@resource(collection_path='/finance', path='/finance/{id}')
class AZFinance(object):
    def __init__(self, request):
        self.request = request
    @view(renderer='json')
    def get(self):
        id = self.request.matchdict['id']
        res = DBSession.query(AdminZone.name, AdminZone.code_insee, AdminZone.code_dep, AdminZoneFinance.year, AdminZoneFinance.data).join(AdminZone, AdminZone.id==AdminZoneFinance.adminzone_id).filter(AdminZone.id==id).order_by('year').all()
        return {'results': res}

@view_config(route_name='index')
def index(request):
    response = FileResponse(
        'localgouv/static/templates/index.html',
        request=request,
        content_type='text/html'
        )
    return response
