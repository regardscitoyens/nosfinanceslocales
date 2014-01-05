
import transaction
import json
import os, sys


from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from tempfile import NamedTemporaryFile
import subprocess
from sqlalchemy import engine_from_config

from ..maps import Map, MAP_VARIABLES
from ..mapnik_render import render_tiles

from ..models import (
    DBSession,
    AdminZoneFinance,
)

def carto_convert(data):
    tmp = NamedTemporaryFile(suffix='.mml')
    json_data = json.dumps(data, indent=2)
    tmp.file.write(json_data)
    tmp.file.flush()
    xml = subprocess.Popen( "carto %s"%tmp.name,
                             stdout=subprocess.PIPE,
                             shell=True ).stdout.read()
    tmp.close()
    return xml

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    years = zip(*DBSession.query(AdminZoneFinance.year).distinct().all())[0]

    for key in MAP_VARIABLES.keys():
        for year in years:
            m = Map(year, key, settings['base_mss_dir'])
            extent = m.config['Layer'][0]['Datasource']['extent']
            open('test.mml', 'w').write(json.dumps(m.toJSON(), indent=2))
            xmlmap = carto_convert(m.toJSON())
            open('xmlmap.xml', 'w').write(xmlmap)
            map_tile_dir = os.path.join(settings['base_tile_dir'], str(year), key) + '/'
            render_tiles(extent, xmlmap, map_tile_dir, m.config['minzoom'], m.config['maxzoom'], name=m.config['name'])


if __name__ == '__main__':
    main()
