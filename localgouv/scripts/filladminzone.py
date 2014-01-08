import os
import sys
import transaction
import json

from fiona import collection
from shapely.geometry import shape, MultiPolygon
from shapely.ops import cascaded_union
from shapely.wkt import loads

from sqlalchemy import engine_from_config, func

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars

from ..models import (
    DBSession,
    AdminZone,
    Base,
    ADMIN_LEVEL_CITY,
    ADMIN_LEVEL_CITY_ARR,
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def extract_adminzone_data(city):
    properties = city['properties']
    g = shape(city['geometry'])
    if g.type == 'Polygon':
        g = MultiPolygon([g])
    admin_level = ADMIN_LEVEL_CITY
    if '-ARRONDISSEMENT' in properties['NOM_COMM']:
        admin_level = ADMIN_LEVEL_CITY_ARR
    return {'name': properties['NOM_COMM'],
            'code_department': properties['CODE_DEPT'],
            'code_city': properties['CODE_COMM'],
            'admin_level': admin_level,
            'geometry': "SRID=4326;" + g.wkt}

def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    geofla_filepath = 'data/COMMUNES/COMMUNE_4326.SHP'
    with transaction.manager:
        # script
        with collection(geofla_filepath) as cities:
            for city in cities:
                data = extract_adminzone_data(city)
                az = AdminZone(**data)
                DBSession.add(az)

    cities_with_arr = [
        {'name': 'PARIS',
         'code_city': '056',
         'code_department': '75'},
        {'name': 'MARSEILLE',
         'code_city': '055',
         'code_department': '13'},
        {'name': 'LYON',
         'code_city': '123',
         'code_department': '69'}
    ]
    import pdb
    pdb.set_trace()
    with transaction.manager:
        for city in cities_with_arr:
            wkt_geoms = zip(*DBSession.query(func.ST_AsText(AdminZone.geometry))\
                .filter(AdminZone.name.contains(city['name']))\
                .filter(AdminZone.admin_level==ADMIN_LEVEL_CITY)\
                .all())[0]
            city_geom = cascaded_union([loads(wkt_geom) for wkt_geom in wkt_geoms])
            if city_geom.type == 'Polygon':
                city_geom = MultiPolygon([city_geom])
            az = AdminZone(**city)
            az.geometry = city_geom.wkt
            az.admin_level = ADMIN_LEVEL_CITY
            DBSession.add(az)

if __name__ == '__main__':
    main()
