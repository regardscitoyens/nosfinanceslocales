
import os, sys
import mapnik

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from sqlalchemy import engine_from_config

from ..maps import Map, MAPS_CONFIG
from ..carto import carto_convert

from ..models import (
    DBSession,
    AdminZoneFinance,
)

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def create_thumbnail(xmlmap, filepath):
    shape = (230, 200)
    m = mapnik.Map(*shape)
    mapnik.load_map_from_string(m, xmlmap)
    box = m.layers[0].envelope()
    prj = mapnik.Projection(m.srs)
    prj_box = box.forward(prj)
    m.zoom_to_box(prj_box)
    im = mapnik.Image(*shape)
    mapnik.render(m, im)
    im.save(filepath, 'png256')

def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    years = zip(*DBSession.query(AdminZoneFinance.year).distinct().order_by("year").all())[0]

    for var_name in MAPS_CONFIG.keys():
        for year in years:
            m = Map(year, var_name)
            xmlmap = carto_convert(m.mapnik_config)
            thumbnail_filepath = os.path.join(settings['static_app_dir'], 'thumbnails')
            try:
                os.makedirs(thumbnail_filepath)
            except OSError:
                pass
            create_thumbnail(xmlmap, os.path.join(thumbnail_filepath, m.info['id']) + '.png')

if __name__ == '__main__':
    main()

