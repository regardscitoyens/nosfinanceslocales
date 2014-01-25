from pyramid.paster import get_app, setup_logging
ini_path = '/Users/nosfinanceslocales/src/nosfinanceslocales/src/server/development.ini'
setup_logging(ini_path)
application = get_app(ini_path, 'main')
