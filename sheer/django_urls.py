import json
import os
import codecs

from django.conf.urls import url
from django.conf import settings

from sheerlike.views.generic import SheerTemplateView
from sheerlike import register_permalink

urlpatterns = [
    url(r'^$', SheerTemplateView.as_view()),
    url(r'^.+(/|.html)$', SheerTemplateView.as_view()),
]


for site in settings.SHEER_SITES:
    lookups_json_path = site.child('_settings').child('lookups.json')
    if os.path.exists(lookups_json_path):
        with codecs.open(lookups_json_path, encoding='utf8') as lookups_file:
            lookups = json.loads(lookups_file.read())
            for name, config in lookups.iteritems():
                regex  = r'^' + config['url'][1:] + r'$'
                regex = regex.replace('<id>', r'(?P<doc_id>[\w-]+)')
                pattern = url(regex, SheerTemplateView.as_view(doc_type=config['type'],
                    local_name = name,
                    default_template = config['url'].replace('<id>/', '_single.html')
                    ),
                    name = name + '_detail'
                    )
                urlpatterns.insert(0, pattern)
                if config.get('permalink', False):
                    register_permalink(config['type'], name + '_detail')
