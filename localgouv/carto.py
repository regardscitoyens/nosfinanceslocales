
import json
import subprocess
from tempfile import NamedTemporaryFile

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
