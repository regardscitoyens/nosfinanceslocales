
import os
import numpy as np
import brewer2mpl
from sqlalchemy import func, cast, Float, select, alias

from .models import DBSession, AdminZone, AdminZoneFinance, SRID

POP_VAR = cast(AdminZoneFinance.data['population'], Float)

MAP_VARIABLES = {
    'debt_per_person': cast(AdminZoneFinance.data['debt_annual_costs'], Float)/POP_VAR
}

MAP_VARIABLES_FILTER = {
    'debt_per_person': POP_VAR > 0
}


def get_extent():
    return ','.join(map(str, DBSession.query(
        func.xMin(AdminZone.geometry),
        func.yMin(AdminZone.geometry),
        func.xMax(AdminZone.geometry),
        func.yMax(AdminZone.geometry)
    ).first()))

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
    return (comp.string.encode(enc) % params).decode(enc)

def france_layer(layer_id, query):
    fullquery = compile_query(query)
    datasource = {
        'table': "(%s) as map_table" % fullquery,
        'geometry_field': 'geometry',
        'extent': get_extent(),
    }

    engine = DBSession.get_bind()
    datasource.update({
        'type': 'postgis',
        'id': layer_id,
        "key_field": "adminzone_id",
        'user': engine.url.username,
        'host': engine.url.host,
        'dbname': engine.url.database,
        'srid': SRID,
    })
    layer = {
        'name':layer_id,
        'id': layer_id,
        'geometry': 'polygon',
        'srs': '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs',
        'Datasource': datasource,
    }
    return layer

def map_query(year, variable, variable_filter):
    q = DBSession.query(AdminZoneFinance.year, variable, AdminZone.geometry, AdminZone.name, AdminZone.code_insee.label('code_insee'))
    return q.filter(AdminZoneFinance.year==year).filter(variable_filter).join(AdminZone, AdminZone.id==AdminZoneFinance.adminzone_id)

def values_query(year, variable, variable_filter):
    return select([variable]).where(AdminZoneFinance.year==year).where(variable_filter)

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
    def __init__(self, year, name, mss_dir):
        try:
            os.makedirs(mss_dir)
        except:
            pass
        variable = MAP_VARIABLES[name].label(name)
        variable_filter = MAP_VARIABLES_FILTER.get(name)
        query = map_query(year, variable, variable_filter)
        layer = "layer_%s"%name
        config = {
            'minzoom': 5,
            'maxzoom': 12,
            'srs': "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs",
            'name': name,
            'description': '',
            'Layer': [france_layer(layer, query)],
        }

        # style

        # build a quantile scale
        size = 9
        values = zip(*DBSession.query(alias(values_query(year, variable, variable_filter))).all())[0]
        variable_range = np.percentile(values, list(np.linspace(0, 100, size+1)))
        colors = brewer2mpl.get_map('YlGnBu', 'Sequential', size).hex_colors
        config['Stylesheet'] = [{'id': 'scale.mss', 'data': scale_mss(layer, name, variable_range, colors)}]

        self.config = config
        self.colors = colors
        self.variable_range = variable_range

    def toJSON(self):
        return self.config

    @property
    def legend(self):
        return {
            'colors': self.colors,
            'variable_range': self.variable_range
        }


class MapRegistry(dict):
    def __missing__(self, key):
        pass
