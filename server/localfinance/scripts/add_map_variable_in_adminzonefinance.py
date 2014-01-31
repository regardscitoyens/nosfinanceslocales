import os
import sys
import transaction

from sqlalchemy import engine_from_config, cast, String
from sqlalchemy.dialects.postgresql import hstore

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
    print('usage: %s <config_uri> map_id\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    map_id = argv[2]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    # fill AdminZoneFinance with new variable set in MAPS_CONFIG
    map_ids = [MAPS_CONFIG.keys()] if map_id == 'ALL' else [map_id]

    for map_id in map_ids:
        config = MAPS_CONFIG[map_id]
        q = DBSession.query(AdminZoneFinance.data).filter(config['sql_filter'])
        store = AdminZoneFinance.data
        q.update(
                {store: store + hstore(map_id, cast(config['sql_variable'], String))},
                synchronize_session=False
            )
        transaction.commit()

if __name__ == '__main__':
    main()


