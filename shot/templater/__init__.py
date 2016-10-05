import re
import os
import sys
from collections import Iterable
from operator import eq, gt, lt, contains, is_not, is_

from shot.exc import TemplateSyntaxError

CONDITIONS_OPERATORS = {"=":eq, "==":eq, ">":gt, "<":lt, "is_not": is_not, "is": is_}

def _get_item(expr, item, call=False):
    try:
        if item.isdigit():
            expr = expr[int(item)]
        else:
            expr = getattr(expr, item)
    except AttributeError:
        expr = expr[item]
    if call:
        if not callable(expr):
            raise TemplateSyntaxError("Wrong pipe (not callable): %s" % item)
        expr = expr()
    elif callable(expr):
        raise TemplateSyntaxError("Wrong attribute (it is callable): %s" % item)
    return expr

def _calc_expression(expr, context):
    pipes_parts = expr.split('|')
    expr = pipes_parts.pop(0)
    dot_parts = expr.split('.')
    expr = context.get(dot_parts.pop(0), None)
    for part in dot_parts: expr = _get_item(expr, part)
    for part in pipes_parts: expr = _get_item(expr, part, call=True)
    return expr

class StaticNode:
    def __init__(self, text):
        self.contents = text

    def __str__(self):
        return str(self.contents)

    def render(self, context=None):
        return str(self)

class VariableNode:
    def __init__(self, name):
        if not name and not re.match(r'\w+(?:\.\w+)*(?:|\s*\w+\s*)*', name):
            raise TemplateSyntaxError("Wrong syntax for {{ %s }}" % name)
        self.name = name

    def __str__(self):
        return "<VARIABLE %s>" % self.name

    def render(self, context):
        return str(_calc_expression(self.name, context))

class IfNode:
    def __init__(self, block, parent):
        self.parent = parent
        condition_items = block.split()
        if len(condition_items) not in (2, 4):
            raise TemplateSyntaxError("Wrong IF syntax: {%% %s %%}" % block)
        try:
            _, self.left, self.condition, self.right = condition_items
        except ValueError:
            self.left, self.condition, self.right = condition_items[1], "is_not", "None"
        if self.condition not in CONDITIONS_OPERATORS:
            raise TemplateSyntaxError("Wrong condition: {%% %s %%}" % block)

        self.true_stack, self.false_stack = [], []
        self.stack = self.true_stack

    def add(self, node):
        self.stack.append(node)

    def process_else(self, block):
        if block != "else": raise TemplateSyntaxError("Wrong {%% else %%} syntax: %s" % block)
        self.stack = self.false_stack

    def render(self, context):
        result = []
        if CONDITIONS_OPERATORS[self.condition](_calc_expression(self.left, context), eval(self.right)):
            stack = self.true_stack
        else:
            stack = self.false_stack

        for node in stack: result.append(node.render(context))
        return ''.join(result)

    def __str__(self):
        return "<IF %s>" % self.left

class ForNode:
    def __init__(self, block, parent):
        self.parent = parent
        for_items = block.split()
        if len(for_items) != 4 or for_items[2] != 'in': raise TemplateSyntaxError("Wrong {%% for x in y %%} syntax: %s" % block)
        self.loop_stack, self.empty_stack, self.loop_var, self.loop_source = [], [], for_items[1], for_items[3]
        self.stack = self.loop_stack

    def add(self, node):
        self.stack.append(node)

    def process_empty(self, block):
        if block != "empty": raise TemplateSyntaxError("Wrong {%% empty %%} syntax: %s" % block)
        self.stack = self.empty_stack

    def render(self, context):
        result = []
        loop_source = _calc_expression(self.loop_source, context)
        try:
            stack = self.empty_stack
            if loop_source and len(loop_source):
                stack = self.loop_stack
        except TypeError:
            raise TemplateSyntaxError("Not iterable in {%% for %%}: ", self.loop_source)

        counter = 0
        if loop_source:
            for loop_variable in loop_source:
                for node in stack:
                    updated_context = dict(context)
                    updated_context.update({
                        'counter0': counter,
                        'counter': counter + 1,
                        self.loop_var: loop_variable,
                    })
                    result.append(node.render(updated_context))
                counter += 1
        return ''.join(result)

    def __str__(self):
        return "<FOR %s IN %s>" % (self.loop_var, self.loop_source) 

class Templater:
    def __init__(self, template, context=None):
        from shot import settings
        # check is file path passed
        if template.endswith(".html") or template.endswith(".htm"):
            template_candidates = []
            if os.sep in template:
                template_candidates.append(os.path.join(settings['BASE_DIR'], template))
            template_candidates.append(os.path.join(settings.get('TEMPLATES', 'templates'), template))
            for candidate in template_candidates:
                if os.path.exists(candidate):
                    try:
                        template = open(candidate).read()
                        break
                    except OSError:
                        pass
        self.stack = []
        self.parent = self
        self.current_section = self
        self.parts = re.split(r'({{.*?}}|{%.*?%}|{#.*?#})', template)
        if context: self.context = context
        else: self.context = {}

    def add(self, node):
        self.stack.append(node)

    def process(self):
        for part in self.parts:
            if part == "" or part.startswith('{#'):
                continue
            elif part.startswith('{{'):
                new_node = VariableNode(part[2:-2].strip())
                self.current_section.add(new_node)
            elif part.startswith('{%'):
                block = part[2:-2].strip()
                if block.startswith('if'):
                    new_node = IfNode(block, self.current_section)
                    self.current_section.add(new_node)
                    self.current_section = new_node
                elif block.startswith("else"):
                    try:
                        self.current_section.process_else(block)
                    except AttributeError:
                        raise TemplateSyntaxError("Wrong {%% else %%} placement")
                elif block.startswith("endif"):
                    if block != "endif":
                        raise TemplateSyntaxError("Wrong {%% endif %%} syntax: %s" % block)
                    if not isinstance(self.current_section, IfNode):
                        raise TemplateSyntaxError("Wrong {%% endif %%} placement")
                    self.current_section = self.current_section.parent
                elif block.startswith("for"):
                    new_node = ForNode(block, self.current_section)
                    self.current_section.add(new_node)
                    self.current_section = new_node
                elif block.startswith("empty"):
                    try:
                        self.current_section.process_empty(block)
                    except AttributeError:
                        raise TemplateSyntaxError("Wrong {%% empty %%} placement")
                elif block.startswith("endfor"):
                    if block != "endfor":
                        raise TemplateSyntaxError("Wrong {%% endfor %%} syntax: %s" % block)
                    if not isinstance(self.current_section, ForNode):
                        raise TemplateSyntaxError("Wrong {%% endfor %%} placement")
                    self.current_section = self.current_section.parent
            else:
                self.current_section.add(StaticNode(part))
        return ""

    def render(self, context=None):
        from shot import settings
        self.process()
        if not context:
            context = self.context
        if not self.current_section is self:
            raise TemplateSyntaxError("Wrong ending of template, %s is not closed" % self.current_section)
        result = []
        for node in self.stack:
            result.append(node.render(context))
        return ''.join(result).encode(settings.get('ENCODING', 'utf-8'))

