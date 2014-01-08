
import transaction
import json
import os, sys
import mapnik

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
    AdminZone,
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

def create_thumbnail(xmlmap, filepath):
    shape = (140, 140)
    m = mapnik.Map(*shape)
    mapnik.load_map_from_string(m, xmlmap)
    box2d = m.layers[0].envelope()
    m.zoom_to_box(box2d)
    im = mapnik.Image(*shape)
    mapnik.render(m, im)
    im.save(filepath)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    years = zip(*DBSession.query(AdminZoneFinance.year).distinct().all())[0]

    for var_name in MAPS_CONFIG.keys():
        for year in years:
            m = Map(year, var_name)
            extent = m.info['extent']
            xmlmap = carto_convert(m.mapnik_config)
            map_tile_dir = os.path.join(settings['base_tile_dir'], m.info['id']) + '/'
            try:
                os.makedirs(map_tile_dir)
            except OSError:
                pass
            render_tiles(extent, xmlmap, map_tile_dir, m.info['minzoom'], m.info['maxzoom'], name=m.info['name'])

            # XXX: move this elsewhere...
            # create thumbnail of the map
            thumbnail_filepath = os.path.join(settings['static_app_dir'], 'thumbnail', m.info['id'])
            try:
                os.makedirs(thumbnail_filepath)
            except OSError:
                pass
            create_thumbnail(xmlmap, thumbnail_filepath)

if __name__ == '__main__':
    main()
