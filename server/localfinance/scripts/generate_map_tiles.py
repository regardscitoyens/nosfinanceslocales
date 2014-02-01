
import os, sys

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from sqlalchemy import engine_from_config

from ..maps import Map, MAPS_CONFIG
from ..mapnik_render import render_tiles
from ..carto import carto_convert

from ..models import (
    DBSession,
    AdminZoneFinance,
)

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> map_ids\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    map_ids = argv[2].split(',')
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    years = zip(*DBSession.query(AdminZoneFinance.year).distinct().order_by("year").all())[0]

    map_ids = MAPS_CONFIG.keys() if map_ids[0] == 'ALL' else map_ids
    for map_id in map_ids:
        for year in years:
            m = Map(year, map_id)
            extent = m.info['extent']
            xmlmap = carto_convert(m.mapnik_config)
            map_tile_dir = os.path.join(settings['base_tile_dir'], m.info['id']) + '/'
            try:
                os.makedirs(map_tile_dir)
            except OSError:
                pass
            render_tiles(extent, xmlmap, map_tile_dir, m.info['minzoom'], m.info['maxzoom'], name=m.info['name'], fields=[map_id, 'name', 'code_insee', 'id', 'year'], layer_id=0)


if __name__ == '__main__':
    main()
