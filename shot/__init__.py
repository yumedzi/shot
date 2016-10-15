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
from collections import OrderedDict as odict
from operator import eq, gt, lt, contains

from shot.exc import RouteFormatError, RouteNotFoundError, process_generic_exc, TemplateSyntaxError, ShotException
from shot.templater import Templater

HEADERS = [
    ('Content-Type', 'text/html'),
]
settings = dict(
    DEBUG=True,
    SHOW_TIMER=False,
    ENCODING='utf-8', 
    TEMPLATES_DIR='templates',
    BASE_DIR=os.getcwd())
ASSETS_DIR = os.path.dirname(__file__) + '/assets/'
# APP_ROUTES = odict()
APP_ROUTES = []
ROUTES_TO_ADD = []
ROUTE_TYPES = dict(
    str='\w+',
    int='\d+',
    float='[\d\.]+',
    path='[\w_\-\./]+',
)

class Route:
    def __init__(self, url, status_code, function):
        self.url = url
        self.status_code = status_code
        self.function = function
        self.params = []
        params_vars = []
        for s in re.finditer(r'<\s*(?:(?P<type>str|int|float|path):)?\s*(?P<param>\w+)>\s*', url):
            if s:
                if s.group('param') in params_vars:
                    raise RouteFormatError(url, 'Wrong route - repeated parameter')
                type_ = s.group('type') or 'str'
                if type_ not in ROUTE_TYPES:
                    raise RouteFormatError(url, 'Wrong parameter type')
                self.params.append((type_, s.group('param')))
                params_vars.append(s.group('param'))
        self.regexp = "^" + url
        self.regexp += '?$' if self.regexp.endswith('/') else '/?$'
        for t, p in self.params:
            self.regexp = re.sub('<(?:{}:)?{}>'.format(t, p), '(?P<{}>{})'.format(p, ROUTE_TYPES[t]), self.regexp)

    def __str__(self):
        return self.url

    def __call__(self, url):
        match, kwargs = re.match(self.regexp, url), {}
        if match:
            for type_, param in self.params:
                kwargs[param] = eval(type_ if not type_ == 'path' else 'str')(match.group(param))
            return self.status_code, self.function, kwargs


def route(url='', status_code="200 OK"):
    def deco(view_function):
        new_route = Route(url, status_code, view_function)
        APP_ROUTES.append(new_route)
        return view_function
    return deco

def render(template, context=None):
    'Simple wrapper for Templater'
    return Templater(template, context).render()


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
    try:
        for route in APP_ROUTES:
            result = route(environ['PATH_INFO'])
            if result:
                status_code, view_function, data_kwargs = result
                break
        else:
            raise RouteNotFoundError(request.route)
        request.view_function = view_function.__name__
        
        data = view_function(request, **data_kwargs)
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
