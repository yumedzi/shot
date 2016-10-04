from functools import wraps
import sys
import datetime
import re
from ast import literal_eval as eval
from collections import OrderedDict as odict

from shot.exc import RouteNotFound

HEADERS = [
    ('Content-Type', 'text/html'),
    #('Server', str(sys.version.split(maxsplit=1)[0]))

]

settings = {'DEBUG': True, 'ENCODING': 'utf-8'}

def default_view(*args):
    if settings['DEBUG']:
        return "Page is not found"

APP_ROUTES = {
    '?': ("404 Page not found", default_view),
}

ROUTES_TO_ADD = []

def route(url='', status_code="200 OK"):
    # print("Adding url to routes!")
    def deco(view_function):
        view_function.url = url
        view_function.status_code = status_code
        return view_function
    return deco

def process_routes():
    APP_ROUTES.update({ obj.url: (obj.status_code, obj) \
                      for obj in globals().values() \
                        if callable(obj) and hasattr(obj, "url")})


def render_template_str(template, data):
    blocks = {}

    RULES = odict()
    RULES.update((
        (r"(?s){% *if *(\w+) *== *([\'\"\w]+) *%}(.*?){% *else *%}(.*?){% *endif *%}",
            lambda x: x.group(3) if (data.get(x.group(1), '') == eval(x.group(2))) else x.group(4)),
        (r"(?s){% *if *(\w+) *== *([\'\"\w]+) *%}(.*?){% *endif *%}",
            lambda x: x.group(3) if (data.get(x.group(1), '') == eval(x.group(2))) else ''),
        (r"(?s){{ *(\w+?) *}}",
            lambda x: data.get(x.group(1), '')),
        # r"(?s){% block '?\"?(\w+)'?\"? %}(.*?){% endblock %}": \
            # lambda x: blocks.update({x.group(1): x.group(2)}),
    ))

    for rule in RULES:
        print("Looking for rule:", rule)
        rule_regexp = re.findall(rule, template)
        print("Found matches:", rule_regexp)
        for match in rule_regexp:
            print("Processing match: ", str(match))
            template = re.sub(rule, RULES[rule], template)

    print("DEBUG: blocks: %s" % blocks)
    return template


def application(environ, start_response):
    headers = HEADERS #+ \
        #[('Date', datetime.datetime.utcnow().strftime("%a, %d %b %Y %X"))]

    process_routes()
    # print(APP_ROUTES)
    status_code, view_function = APP_ROUTES.get(environ['PATH_INFO'], APP_ROUTES.get('?'))
    start_response(status_code, headers)

    try:
        data = view_function(environ)
    except TypeError:
        data = view_function()

    return [data.encode(settings['ENCODING'], "ignore")]