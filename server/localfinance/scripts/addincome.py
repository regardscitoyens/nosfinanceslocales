# -*- coding: utf-8 -*-

import os
import sys
import transaction

import pandas as pd

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    AdminZone,
    AdminZoneFinance,
    )

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> <dirpath>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def get_income_per_year(year, dirpath):
    short_year = str(year)[-2:]
    columns = ['RFPQ1%s'%short_year, 'RFPQ2%s'%short_year, 'RFPQ3%s'%short_year, 'RFPIQ%s'%short_year, 'RFPET%s'%short_year, 'RFPMO%s'%short_year]
    xls = pd.ExcelFile(os.path.join(dirpath, 'RFDP%sCOM.xls'%year))
    com = xls.parse('D_P', skiprows=6)[['COM'] + columns]
    com.set_index('COM', inplace=True)
    return com

def main(argv=sys.argv):
    if len(argv) < 3:
        usage(argv)
    config_uri = argv[1]
    dirpath = argv[2]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    az_id = pd.DataFrame(
            (DBSession.query(AdminZone.code_insee, AdminZone.id).all()),
            columns=['COM', 'AZ_ID'],
        )
    az_id.set_index('COM', inplace=True)
    for year in range(2001, 2012):
        joined_data = get_income_per_year(year, dirpath).join(az_id)
        joined_data = joined_data[joined_data.AZ_ID.notnull()].reindex()
        with transaction.manager:
            for _, item in joined_data.iterrows():
                dico = item.to_dict()
                az_id = dico.pop('AZ_ID')
                income = dico.pop('RFPQ2%s'%str(year)[-2:])
                store = AdminZoneFinance.data
                DBSession.query(AdminZoneFinance)\
                    .filter(AdminZoneFinance.adminzone_id==az_id)\
                    .update({store: store + {'revenu-par-personne': str(income)}},
                            synchronize_session=False)


if __name__ == '__main__':
    main()


