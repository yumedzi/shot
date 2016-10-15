import traceback
from abc import ABCMeta, abstractclassmethod


class ShotException(BaseException, metaclass=ABCMeta):
    'Base class for all frameworks exceptions'
    @abstractclassmethod
    def __str__(self):
        pass

class RouteFormatError(ShotException):
    def __init__(self, route, msg="Wrong route format"):
        self.route = route
        self.msg = msg

    def __str__(self):
        return "RouteFormatError: %s in %s" % (self.msg, self.route)

class RouteNotFoundError(ShotException):
    def __init__(self, route, msg="Route was not defined"):
        self.route = route
        self.msg = msg

    def __str__(self):
        return "RouteNotFoundError: %s: %s" % (self.msg, self.route)

    def render(self, request):
        from shot import APP_ROUTES, settings, ASSETS_DIR, render

        return [render(ASSETS_DIR + '404.html', {'route': self.route, 'routes': APP_ROUTES if settings['DEBUG'] else None})]

class TemplateSyntaxError(ShotException):
    def __init__(self, msg="Template Syntax error", block=None, line_num=None):
        self.msg = msg
        self.block = block
        self.line_num = line_num

    def __str__(self):
        data = dict(msg=self.msg, block=self.block, line=self.line_num)
        return "TemplateSyntaxError: {msg}, block: {block}, line: #{line}".format(**data)

    def render(self, request):
        from shot import settings, ASSETS_DIR, render
        if settings['DEBUG']:
            return [render(ASSETS_DIR +'exc.html', {'err': self, 'url': request.route, 'view': request.view_function})]
        else:
            return [render(ASSETS_DIR +'500.html')]


def process_generic_exc(err, request):
    from shot import settings, render, ASSETS_DIR
    if settings['DEBUG']:
        trace_as_html = traceback.format_exc().replace("\n", '<br/>')
        debug_context = {'err': err, 'traceback': trace_as_html, 'url': request.route, 'view': request.view_function}
        return [render(ASSETS_DIR + '500.html', debug_context)]
    else:
        return [render(ASSETS_DIR + '500.html', {'err': err})]