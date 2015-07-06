import os.path
import os
import mimetypes
import logging

from django.core.servers import basehttp
from django.core.management import call_command

from .wsgi import app_with_config


def serve_wsgi_app_with_cli_args(args, config):

        application = app_with_config(config)
        call_command('runserver', '%s:%s' % (args.addr,args.port))
        #basehttp.run(args.addr, int(args.port), application)
