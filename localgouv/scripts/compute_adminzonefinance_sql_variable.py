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
    AdminZoneFinance,
    Stats,
    )

from ..maps import MAPS_CONFIG, quantile_scale


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> <variable_name>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    var_name = argv[2]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    # fill AdminZoneFinance with new variable set in MAPS_CONFIG
    # this is not optimal as sql_variable can already be there... would be 
    # better to launch a script for one variable!
    config = MAPS_CONFIG[var_name]
    results = DBSession.query(AdminZoneFinance.id, config['sql_variable'])\
            .filter(config['sql_filter']).order_by(AdminZoneFinance.id).all()
    nb = len(results)
    nb_packets = 100
    # commit values by packets
    for i in range(nb_packets+1):
        print "packet : %i"%i
        istart = i*nb/nb_packets
        iend = min((i+1)*nb/nb_packets, nb)
        subresults = results[istart:iend]
        with transaction.manager:
            ids = zip(*subresults)[0]
            items = DBSession.query(AdminZoneFinance).filter(AdminZoneFinance.id.in_(ids)).order_by(AdminZoneFinance.id).all()
            for item, val in zip(items, zip(*subresults)[1]):
                setattr(item.data, var_name, str(val))

if __name__ == '__main__':
    main()


