import os
import sys

from django.conf import settings
from django.core.wsgi import get_wsgi_application

from unipath import Path

def app_with_config(config):
    site_path = Path(config['location'])
    allowed_hosts = os.environ.get('ALLOWED_HOSTS', ['localhost','127.0.0.1'])

    if config.get('django_project'):
        sys.path.append(config['django_project'])
        settings.DEBUG = config['debug']
        settings.ALLOWED_HOSTS = allowed_hosts
        settings.TEMPLATES = [{
            'BACKEND': 'django.template.backends.jinja2.Jinja2',
            'OPTIONS':{
                        'environment':'sheerlike.environment'                                   
                    }                                                                           
                }
            ]

        return get_wsgi_application()

    settings.configure(
        DEBUG=config['debug'],
        SECRET_KEY='thisisthesecretkey',
        ROOT_URLCONF='sheer.django_urls',
        MIDDLEWARE_CLASSES=(
            'sheerlike.middleware.GlobalRequestMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ),
        INSTALLED_APPS = ['sheerlike', 'django.contrib.staticfiles'],
        ALLOWED_HOSTS =  allowed_hosts,
        SHEER_ELASTICSEARCH_SERVER = config['elasticsearch'],
        SHEER_ELASTICSEARCH_INDEX = config['index'],
        SHEER_SITES = [site_path],
        STATIC_URL = '/static/',
        TEMPLATES = [{
            'BACKEND': 'django.template.backends.jinja2.Jinja2',
            'OPTIONS':{
                        'environment':'sheerlike.environment'                                   
                    }                                                                           
                }
            ]
        )
        
    return get_wsgi_application()
