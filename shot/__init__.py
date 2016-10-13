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

class HTTPRequest:
    def __init__(self, environ=None, view_function=None):
        self.method = 'GET'
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
            self.GET = {}
            self.POST = {}
            self.FILES = {}
            try:
                if self.method == 'GET' and environ.get('QUERY_STRING', ''):
                    self.GET.update(dict([x.split("=") for x in environ.get('QUERY_STRING', '').split("&")]))
                elif self.method == 'POST':
                    post = cgi.FieldStorage(
                        fp=environ['wsgi.input'],
                        environ=environ,
                        keep_blank_values=True
                    )
                    print(dir(post))
                    print(post)

                    self._post = post

                    for field in post:
                        if getattr(post[field], "filename", None):
                            print("%s is FILE" % field, post[field].filename)
                            print("That file is closed?: ", post[field].file.closed)
                            self.FILES[field] = post[field].file #TODO multiple files! 
                        else:
                            val = post.getvalue(field)
                            self.POST[field] = val
            except ZeroDivisionError:
                pass
            # try:
            #     f = environ['wsgi.input'].read()
            #     print("FILE:", f)
            # except:
            #     pass
        if view_function:
            self.view_function = view_function

def application(environ, start_response):
    if settings['DEBUG']: cgitb.enable()
    request = HTTPRequest(environ)
    try:
        t1 = time.time()
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
            if isinstance(data, str):
                return [data.encode(settings.get('ENCODING', 'utf-8'))]
            return [data]
        except ShotException as err:
            return err.render(request)
        except Exception as err:
            return process_generic_exc(err, request)
    finally:
        print(">>> %s: %s ms" % (environ['PATH_INFO'], round(time.time() - t1, 5)*1000))
