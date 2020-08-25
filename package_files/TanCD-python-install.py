import tanium,zipfile
from os import path,name as osname
from shutil import rmtree

##
# installation script for TanCD python modules
#

if path.exists(tanium.client.common.get_client_dir() + '/Tools/TanCD/py'):
    rmtree(tanium.client.common.get_client_dir() + '/Tools/TanCD/py', ignore_errors=True, onerror=None)

if osname == 'nt':
    package='TanCD-python-windows.zip'
else:
    package='TanCD-python-linux.zip'

with zipfile.ZipFile(package, 'r') as zip_ref:
    zip_ref.extractall(tanium.client.common.get_client_dir() + '/Tools/TanCD')
