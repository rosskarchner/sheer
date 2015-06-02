import os
import os.path

import elasticsearch

from shortstack.extensions.api import Extension
from flask.config import Config
import flask

from sheer.query import QueryFinder
from sheer.utility import parse_es_hosts

ext=Extension()
ss_root = os.environ['SS_ROOT_DIR']

defaults = dict(ELASTICSEARCH_SERVERS = 'localhost',
                ELASTICSEARCH_INDEX = 'content')


config = Config(ss_root)
config.update(defaults)

if 'SHEER_SETTINGS' in os.environ:
    config.from_envvar('SHEER_SETTINGS')

@ext.extendcontext_always
def sheer_template_functions():
    es_hosts = parse_es_hosts(config['ELASTICSEARCH_SERVERS'])
    
    es = elasticsearch.Elasticsearch(es_hosts)
    es_index = config['ELASTICSEARCH_INDEX']
    queries_dir= os.path.join(ss_root,'_queries')
    queryfinder = QueryFinder(es, es_index,queries_dir)
    return {'queries':queryfinder}
