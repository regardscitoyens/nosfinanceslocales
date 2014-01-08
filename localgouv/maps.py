# -*- coding: utf-8 -*-

import re
import os
import numpy as np
import brewer2mpl
from sqlalchemy import func, cast, Float, select, alias, and_

from .models import DBSession, AdminZone, AdminZoneFinance, SRID

POP_VAR = cast(AdminZoneFinance.data['population'], Float)

MAPS_CONFIG = {
    'debt_per_person': {
        'description': u'Dette par commune par habitant en €',
        'sql_variable': cast(AdminZoneFinance.data['debt_annual_costs'], Float)/POP_VAR,
        'sql_filter': and_(POP_VAR > 0, AdminZoneFinance.data['debt_annual_costs'] <> 'nan'),
    }
}


from sqlalchemy.sql import compiler

from psycopg2.extensions import adapt as sqlescape
# or use the appropiate escape function from your db driver

def compile_query(query):
    dialect = query.session.bind.dialect
    statement = query.statement
    comp = compiler.SQLCompiler(dialect, statement)
    comp.compile()
    enc = dialect.encoding
    params = {}
    for k,v in comp.params.iteritems():
        if isinstance(v, unicode):
            v = v.encode(enc)
        params[k] = sqlescape(v)
    # XXX: hack to remove ST_AsBinary put by geoalchemy, it breaks mapnik query
    # :(((
    str_query = (comp.string.encode(enc) % params).decode(enc)
    m = re.search('ST_AsBinary\(([\w\.]*)\)', str_query)
    if len(m.groups()) > 1:
        # the trick does not handle this case
        raise
    return str_query.replace(m.group(), m.groups()[0])

def quantile_scale(sql_variable, sql_filter, size):
    values = zip(*DBSession.query(sql_variable).filter(sql_filter).all())[0]
    return np.percentile(values, list(np.linspace(0, 100, size+1)))

def get_extent():
    return DBSession.query(
        func.min(func.ST_XMin(AdminZone.geometry)),
        func.min(func.ST_YMin(AdminZone.geometry)),
        func.max(func.ST_XMax(AdminZone.geometry)),
        func.max(func.ST_XMax(AdminZone.geometry)),
    ).first()

def france_layer(layer_id, query):
    engine = DBSession.get_bind()
    datasource = {
        'type': 'postgis',
        'table': "(%s) as map_table" % query,
        'user': engine.url.username,
        'host': engine.url.host,
        'dbname': engine.url.database,
        'password': engine.url.password,
        'srid': SRID,
    }

    layer = {
        'name':layer_id, #useful ? keep name or id ?
        'id': layer_id,
        'geometry': 'polygon',
        'srs': '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs',
        'Datasource': datasource,
    }
    return layer

def map_query(year, variable, variable_filter):
    q = DBSession.query(AdminZone.id, AdminZone.geometry, AdminZone.name, AdminZone.code_insee.label('code_insee'), AdminZoneFinance.year, variable)
    return compile_query(q.filter(AdminZoneFinance.year==year).filter(variable_filter).join(AdminZoneFinance, AdminZone.id==AdminZoneFinance.adminzone_id))

def scale_mss(layer, var_name, x, colors):
    styles = []
    def price_style(x_min, x_max, color):
        template = "[%(var_name)s>%(min)s][%(var_name)s<=%(max)s] { polygon-fill: %(color)s; line-color: %(color)s; }"
        return template % { 'var_name': var_name,
                            'min': x_min,
                            'max': x_max,
                            'color': color }
    for x_min, x_max, color in zip(x[:-1], x[1:], colors):
        styles.append(price_style(x_min, x_max, color) )
    return "#%s::variable{\n%s\n}"%(layer, '\n'.join(styles))

class Map(object):
    # XXX: hack to store expensive scale query. Remove that crap later.
    _scale_cache = {}
    def __init__(self, year, name):
        variables = MAPS_CONFIG.get(name)
        query = map_query(year, variables['sql_variable'].label(name), variables['sql_filter'])
        layer = "layer_%s"%name

        # style
        # build scale based on quantiles
        size = 9
        if name not in self._scale_cache:
            self._scale_cache[name] = \
                quantile_scale(variables['sql_variable'],
                               variables['sql_filter'],
                               size)
        scale_range = self._scale_cache.get(name)
        colors = brewer2mpl.get_map('YlGnBu', 'Sequential', size).hex_colors

        self.info = {
            'description': variables['description'],
            'year': year,
            'name': name,
            'id': "%s_%s"%(name, year),
            'minzoom': 5,
            'maxzoom': 11,
            'scale_colors': colors,
            'scale_range': scale_range,
            'extent': get_extent(),
        }

        self.mapnik_config = {
            'srs': "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0.0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over",
            'Layer': [france_layer(layer, query)],
            'Stylesheet': [{'id': 'scale.mss', 'data': scale_mss(layer, name, scale_range, colors)}],
        }

class MapRegistry(dict):
    def __missing__(self, key):
        self[key] = [Map(year, key) for year in range(2000, 2012)]
        return self[key]
map_registry = MapRegistry()
