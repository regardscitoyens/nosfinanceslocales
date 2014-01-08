import os
import sys
import transaction
import json

import pandas as pd

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
    AdminZoneFinance,
    Base,
    )

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> <filepath> [var=value]\n'
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
    if len(argv) < 3:
        usage(argv)
    config_uri = argv[1]
    filename = argv[2]
    options = parse_vars(argv[3:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    code_az_id = dict(DBSession.query(AdminZone.code_insee, AdminZone.id).all())
    df = pd.read_csv(filename, encoding='utf-8')
    import pdb
    pdb.set_trace()
    df.insee_code = df.insee_code.astype('unicode')
    df['az_id'] = df.insee_code.apply(lambda c: code_az_id.get(c, None))
    df = df[df.az_id.notnull()].reindex()
    size = df.shape[0]
    for i in range(11):
        imin = i*size/10
        imax = min((i+1)*size/10, size)
        with transaction.manager:
            for _, item in df[imin:imax].iterrows():
                dico = item.to_dict()
                az_id = dico.pop('az_id')
                year = dico.pop('year')
                data = dict([(k, unicode(v)) for k, v in dico.items()])
                DBSession.add(AdminZoneFinance(adminzone_id=az_id,year=year,data=data))


if __name__ == '__main__':
    main()

