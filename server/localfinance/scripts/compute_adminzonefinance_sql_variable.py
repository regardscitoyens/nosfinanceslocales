import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    AdminZoneFinance,
    )

from ..maps import MAPS_CONFIG


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
        ids, vals = zip(*subresults)
        if len(subresults) == 0:
            continue
        with transaction.manager:
            ids = zip(*subresults)[0]
            items = DBSession.query(AdminZoneFinance).filter(AdminZoneFinance.id.in_(ids)).order_by(AdminZoneFinance.id).all()
            for item, val in zip(items, vals):
                item.data[var_name] = unicode(val)

if __name__ == '__main__':
    main()


