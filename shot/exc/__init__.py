class RouteNotFound(BaseException):
    def __init__(self, route, msg="Route was not defined"):
        self.route = route
        self.msg = msg

    def __str__(self):
        return "RouteNotFound: %s: %s" % (self.msg, self.route)


class TemplateSyntaxError(BaseException):
    def __init__(self, msg="Template Syntax error"):
        self.msg = msg

    def __str__(self):
        return "Template Syntax Error: %s" % self.msg