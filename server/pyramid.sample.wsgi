from pyramid.paster import get_app, setup_logging
ini_path = 'path/to/production.apache.ini'
setup_logging(ini_path)
application = get_app(ini_path, 'main')
