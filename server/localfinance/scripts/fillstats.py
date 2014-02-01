import os
import sys
import transaction
import json

from sqlalchemy import engine_from_config, func

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )


from ..models import (
    DBSession,
    AdminZoneFinance,
    Stats,
    )

from ..maps import MAPS_CONFIG, quantile_scale


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> map_id\n'
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

    map_ids = MAPS_CONFIG.keys() if map_ids[0] == 'ALL' else map_ids

    # Delete stats
    with transaction.manager:
        DBSession.query(Stats).filter(Stats.name.in_(map_ids)).delete(synchronize_session=False)

    # compute some stats for variables used for maps
    for map_id in map_ids:
        config = MAPS_CONFIG[map_id]
        # scale
        scale_size = 9
        scale = quantile_scale(config['sql_variable'], config['sql_filter'], scale_size)
        # mean by year
        mean_by_year = DBSession.query(AdminZoneFinance.year,
                                       func.avg(config['sql_variable']))\
                            .filter(config['sql_filter'])\
                            .group_by(AdminZoneFinance.year)\
                            .order_by(AdminZoneFinance.year).all()
        data = {
            'scale': json.dumps(scale),
            'mean_by_year': json.dumps(mean_by_year),
        }
        with transaction.manager:
            DBSession.add(Stats(name=map_id, data=data))

if __name__ == '__main__':
    main()

