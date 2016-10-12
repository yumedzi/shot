from functools import wraps
import sys
import datetime
import re
import sys
import os
import time
import traceback
from ast import literal_eval as eval
from collections import OrderedDict as odict
from operator import eq, gt, lt, contains

from shot.exc import ShotException, RouteNotFoundError, process_generic_exc, TemplateSyntaxError
from shot.templater import Templater

HEADERS = [
    ('Content-Type', 'text/html'),
    #('Server', str(sys.version.split(maxsplit=1)[0]))
]
settings = dict(
    DEBUG=True,
    ENCODING='utf-8', 
    TEMPLATES_DIR='templates',
    BASE_DIR=os.getcwd())
ASSETS_DIR = os.path.dirname(__file__) + '/assets/'
APP_ROUTES = odict()
ROUTES_TO_ADD = []

def route(url='', status_code="200 OK"):
    def deco(view_function):
        view_function.url = url
        view_function.status_code = status_code
        APP_ROUTES[url] = (status_code, view_function)
        return view_function
    return deco

def render(template, context=None):
    'Simple wrapper for Templater'
    return Templater(template, context).render()

def process_routes():
    APP_ROUTES.update({ obj.url: (obj.status_code, obj) \
                      for obj in globals().values() \
                        if callable(obj) and hasattr(obj, "url")})

def application(environ, start_response):
    try:
        t1 = time.time()
        headers = HEADERS
        process_routes()
        try:
            try:
                status_code, view_function = APP_ROUTES[environ['PATH_INFO']]
                environ['VIEW_FUNCTION'] = view_function.__name__
            except KeyError: raise RouteNotFoundError(environ['PATH_INFO'])
            start_response(status_code, headers)
            data = view_function(environ)
            if isinstance(data, str):
                return [data.encode(settings.get('ENCODING', 'utf-8'))]
            return [data]
        except ShotException as err:
            return err.render(environ)
        except Exception as err:
            return process_generic_exc(err, environ)
    finally:
        print(">>> %s: %s ms" % (environ['PATH_INFO'], round(time.time() - t1, 5)*1000))
