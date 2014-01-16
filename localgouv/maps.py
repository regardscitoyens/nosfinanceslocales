# -*- coding: utf-8 -*-

import re
import json
import os
import numpy as np
import brewer2mpl
from sqlalchemy import func, cast, Float, select, alias, and_
from sqlalchemy.sql import compiler
from psycopg2.extensions import adapt as sqlescape


from .models import DBSession, AdminZone, AdminZoneFinance, Stats, SRID

POP_VAR = cast(AdminZoneFinance.data['population'], Float)

MAPS_CONFIG = {
    'debt_per_person': {
        'description': u'Charges financières annuelles par commune par habitant (en €)',
        'sql_variable': cast(AdminZoneFinance.data['debt_annual_costs'], Float) / POP_VAR,
        'sql_filter': and_(POP_VAR > 0, AdminZoneFinance.data['debt_annual_costs'] <> 'nan'),
        'colors': lambda size: brewer2mpl.get_map('YlGnBu', 'Sequential', size)
    },
    'property_tax_rate': {
        'description': u'Taxe foncière par commune (en %)',
        'sql_variable': cast(AdminZoneFinance.data['property_tax_rate'], Float),
        'sql_filter': AdminZoneFinance.data['property_tax_rate'] <> 'nan',
        'colors': lambda size: brewer2mpl.get_map('YlOrRd', 'Sequential', size)
    },
    'home_tax_rate': {
        'description': u'Taxe d\'habitation par commune (en %)',
        'sql_variable': cast(AdminZoneFinance.data['home_tax_rate'], Float),
        'sql_filter': AdminZoneFinance.data['home_tax_rate'] <> 'nan',
        'colors': lambda size: brewer2mpl.get_map('PuRd', 'Sequential', size)
    },
    'property_tax_value_per_person': {
        'description': u'Taxe foncière par commune par habitant (en €)',
        'sql_variable': cast(AdminZoneFinance.data['property_tax_value'], Float) / POP_VAR,
        'sql_filter': and_(POP_VAR > 0, AdminZoneFinance.data['property_tax_value'] <> 'nan'),
        'colors': lambda size: brewer2mpl.get_map('OrRd', 'Sequential', size)
    },
    'home_tax_value_per_person': {
        'description': u'Taxe d\'habitation par commune par habitant (en €)',
        'sql_variable': cast(AdminZoneFinance.data['home_tax_value'], Float) / POP_VAR,
        'sql_filter': and_(POP_VAR > 0, AdminZoneFinance.data['home_tax_value'] <> 'nan'),
        'colors': lambda size: brewer2mpl.get_map('BuPu', 'Sequential', size)
    }
}

BORDERS_MSS = """
line-color: #eee;
  line-join: round;
  line-cap: round;
  polygon-gamma: 0.1;
  line-width: 0;
  [zoom>6][zoom<9] {
    line-width: 0.1;
  }
  [zoom=9] {
    line-width: 0.3;
  }
  [zoom=10] {
    line-width: 0.9;
  }
  [zoom=11] {
    line-width: 1.5;
  }
  [zoom>11] {
    line-width: 2.0;
  }
"""

def compile_query(query):
    """Hack function to get sql query with params"""
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
        func.max(func.ST_YMax(AdminZone.geometry)),
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
    def __init__(self, year, name):
        variables = MAPS_CONFIG.get(name)
        query = map_query(year, variables['sql_variable'].label(name), variables['sql_filter'])
        layer = "layer_%s"%name

        # style
        # build scale based on quantiles
        size = 9
        stats = DBSession.query(Stats).filter(Stats.name==name).first()
        scale_range = json.loads(stats.data['scale'])
        assert size + 1 == len(scale_range)

        colors = variables['colors'](size).hex_colors

        self.info = {
            'description': variables['description'],
            'year': year,
            'name': name,
            'id': "%s_%s"%(name, year),
            'minzoom': 5,
            'maxzoom': 7,
            'scale_colors': colors,
            'scale_range': scale_range,
            'extent': list(get_extent()), # XXX: cornice bug: if tuple, return {}
        }

        self.mapnik_config = {
            'srs': "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0.0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over",
            'Layer': [france_layer(layer, query)],
            'Stylesheet': [
                {'id': 'scale.mss', 'data': scale_mss(layer, name, scale_range, colors)},
                {'id': 'borders.mss', 'data': BORDERS_MSS},
            ],
        }

class MapRegistry(dict):
    def __missing__(self, key):
        self[key] = [Map(year, key) for year in range(2000, 2013)]
        return self[key]
map_registry = MapRegistry()
