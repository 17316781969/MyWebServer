"""WebServer
Usage:
  WebServer [<HOST>] [<PORT>]
  WebServer (-h | --help)
  WebServer (-v | --version)
Options:
  --help                Show this help.
  -v --version          Show version.
  # -p --port           Change port [default: 5030]
  # -h --host           Change host [default: 127.0.0.1]
"""
import os
import sys
import inspect

import docopt

__dir__ = os.path.dirname(os.path.abspath(__file__))
__root__ = os.path.dirname(__dir__)
if __dir__ not in sys.path:
    sys.path.append(__dir__)
if __root__ not in sys.path:
    sys.path.append(__root__)

from MyWebServer.v2 import app

DEBUG = inspect.stack()[-1][1].endswith('/pydevd.py')

if __name__ == '__main__':
    arguments = docopt.docopt(__doc__, version='MyProxy 0.1')

    arguments['<HOST>'] = arguments['<HOST>'] if arguments['<HOST>'] else '0.0.0.0'
    arguments['<PORT>'] = arguments['<PORT>'] if arguments['<PORT>'] else '5000' if app.debug else '5030'

    app.run(host=arguments['<HOST>'], port=arguments['<PORT>'], debug=DEBUG)

# export FLASK_ENV=development
