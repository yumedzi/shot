from functools import wraps
import sys
import datetime
import re
import sys
import os
import time
import traceback
import cgitb
import cgi
from wsgiref.simple_server import make_server
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
    SHOW_TIMER=False,
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

class HTTPRequest:
    def __init__(self, environ=None, view_function=None):
        self.method = 'GET'
        self.GET = {}
        self.POST = {}
        self.FILES = {}
        mapping = dict(
            route='PATH_INFO',
            uri='RAW_URI',
            method='REQUEST_METHOD',
            server='SERVER_NAME',
            referer='HTTP_REFERER',
            agent='HTTP_USER_AGENT',
            accept='HTTP_ACCEPT',
            language='HTTP_ACCEPT_LANGUAGE',
            content_length='CONTENT_LENGTH',
        )
        # print("ENV:", environ)
        if environ:
            for x, y in mapping.items(): setattr(self, x, environ.get(y, ''))
            try:
                if self.method == 'GET' and environ.get('QUERY_STRING', ''):
                    self.GET.update(dict([x.split("=") for x in environ.get('QUERY_STRING', '').split("&")]))
                elif self.method == 'POST':
                    post = cgi.FieldStorage(
                        fp=environ['wsgi.input'],
                        environ=environ,
                        keep_blank_values=True
                    )
                    self._post = post

                    for field in post:
                        if getattr(post[field], "filename", None):
                            self.FILES[field] = post[field].file
                        elif isinstance(post[field], list):
                            self.FILES[field], self.POST[field] = [], []
                            for item in post[field]:
                                if getattr(item, "filename", None): self.FILES[field].append(item.file)
                                else: self.POST[field].append(item.value)
                            for dict_ in (self.FILES, self.POST):
                                if len(dict_[field]) == 1: dict_[field] = dict_[field][0]
                                if not dict_[field]: del dict_[field]
                        else:
                            self.POST[field] = post.getvalue(field)
            except:
                pass
        if view_function:
            self.view_function = view_function

def _show_timer(app):
    'Simple timer decorator - show URL and time spent on it after rendering response'
    @wraps(app)
    def wrapper(environ, *args, **kwargs):
        if settings['SHOW_TIMER']:
            try:
                t1 = time.time()
                return app(environ, *args, **kwargs)
            finally:
                time_data = dict(method=environ['REQUEST_METHOD'], 
                                route=environ['PATH_INFO'], 
                                time=(time.time() - t1)*1000,
                                host=environ['REMOTE_ADDR'])
                print(">>> {host} - {method} {route}: {time:5.3f} ms".format(**time_data))
        else:
            return app(environ, *args, **kwargs)
    return wrapper

@_show_timer
def application(environ, start_response):
    if settings['DEBUG']: cgitb.enable()
    request = HTTPRequest(environ)
    response_started = False
    headers = HEADERS
    process_routes()
    try:
        try:
            status_code, view_function = APP_ROUTES[environ['PATH_INFO']]
            request.view_function = view_function.__name__
        except KeyError: raise RouteNotFoundError(request.route)
        
        # Eval view function
        data = view_function(request)
        headers = [
            ('Content-type', 'text/html; charset=%s' % settings['ENCODING']),
            ('Content-Length', str(len(data))),
        ]
        start_response(status_code, headers)
        response_started = True
        if isinstance(data, str):
            return [data.encode(settings.get('ENCODING', 'utf-8'))]
        return [data]
    except ShotException as err:
        if not response_started: 
            start_response('500 Internal Server Error', headers)
            response_started = True
        return err.render(request)
    except Exception as err:
        if not response_started: start_response('500 Internal Server Error', headers)
        return process_generic_exc(err, request)


def run(host='', port=8000, app=application):
    print("*** Running SHOT dev server on {host}:{port} ***".format(port=port, host=host if host else 'localhost'))
    httpd = make_server(host, port, app)
    httpd.serve_forever()
