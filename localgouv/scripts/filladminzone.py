import os
import sys
import transaction
import json

from fiona import collection
from shapely.geometry import shape, MultiPolygon

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars

from ..models import (
    DBSession,
    AdminZone,
    Base,
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
    return {'name': properties['NOM_COMM'],
            'code_department': properties['CODE_DEPT'],
            'code_city': properties['CODE_COMM'],
            'admin_level': 5,
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

if __name__ == '__main__':
    main()
