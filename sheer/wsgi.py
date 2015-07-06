import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application

from unipath import Path

def app_with_config(config):
    site_path = Path(config['location'])
    settings.configure(
        DEBUG=config['debug'],
        SECRET_KEY='thisisthesecretkey',
        ROOT_URLCONF='sheer.django_urls',
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'sheerlike.middleware.GlobalRequestMiddleware',
        ),
        INSTALLED_APPS = ['sheerlike', 'django.contrib.staticfiles'],
        ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(','),
        SHEER_ELASTICSEARCH_SERVER = config['elasticsearch'],
        SHEER_ELASTICSEARCH_INDEX = config['index'],
        SHEER_SITES = [site_path],
        STATIC_URL = '/static/',
#        STATICFILES_DIRS = (site_path.child('static')),
        TEMPLATES = [{
            'BACKEND': 'django.template.backends.jinja2.Jinja2',
            'OPTIONS':{
                        'environment':'sheerlike.environment'                                   
                    }                                                                           
                }
            ]
        )
        
    return get_wsgi_application()
