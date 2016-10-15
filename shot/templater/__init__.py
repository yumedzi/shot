import re
import os
import sys
from collections import Iterable, Mapping
from ast import literal_eval
from operator import eq, not_, gt, lt, contains, is_not, is_, and_, or_

from shot.exc import TemplateSyntaxError

CONDITIONS_OPERATORS = {"=": eq, "not": not_, "==": eq, ">": gt, "<": lt, "is_not": is_not, "is": is_,
                        "and": and_, "AND": and_, "&": and_, "or": or_, "OR": or_, "|": or_,
}

def _get_item(expr, item, call=False):
    try:
        if item.isdigit():
            expr = expr[int(item)]
        else:
            expr = getattr(expr, item)
    except AttributeError:
        try:
            expr = expr[item]
        except TypeError:
            raise TemplateSyntaxError("Can't evaluate expression", "%s.%s" % (expr, item))
    if call:
        if not callable(expr):
            raise TemplateSyntaxError("Wrong pipe (not callable)", expr)
        expr = expr()
    elif callable(expr):
        raise TemplateSyntaxError("Wrong attribute (it is callable)", "%s.%s" % (expr, item))
    return expr

def _calc_expression(expr, context):
    pipes_parts = expr.split('|')
    expr = pipes_parts.pop(0)
    dot_parts = expr.split('.')
    expr = context.get(dot_parts.pop(0), None)
    for part in dot_parts: expr = _get_item(expr, part)
    for part in pipes_parts: 
        if not part == 'safe':
            expr = _get_item(expr, part, call=True)
        else:
            expr = str(expr).replace('<', '&lt;').replace('>', '&gt;').replace(' ', '&nbsp;')
    return expr

class StaticNode:
    def __init__(self, text, line_num=None):
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
    def __init__(self, block, parent, line_num=None):
        self.parent = parent
        condition_items = block.split()
        if len(condition_items) == 3:
            if condition_items[1] != 'not':
                raise TemplateSyntaxError("Wrong IF syntax (only 1 or 2 condition arguments allowed)", "{%% %s %%}" %block, line_num)
            _, self.condition, self.left, self.right = *condition_items, None
        elif len(condition_items) not in (2, 4):
            raise TemplateSyntaxError("Wrong IF syntax (only 1 or 2 condition arguments allowed)", "{%% %s %%}" %block, line_num)
        else:
            try:
                _, self.left, self.condition, self.right = condition_items
            except ValueError:
                self.left, self.condition, self.right = condition_items[1], "is_not", "None"
            if self.condition not in CONDITIONS_OPERATORS:
                raise TemplateSyntaxError("Wrong condition: {%% %s %%}" % block, line_num)

        self.true_stack, self.false_stack = [], []
        self.stack = self.true_stack

    def add(self, node):
        self.stack.append(node)

    def process_else(self, block, line_num=None):
        if block != "else": raise TemplateSyntaxError("Wrong {%% else %%} syntax: %s", "{% {} %}".format(block), line_num)
        self.stack = self.false_stack

    def render(self, context):
        result = []
        if self.right is not None:
            bool_val = CONDITIONS_OPERATORS[self.condition](_calc_expression(self.left, context), eval(self.right))
        else:
            bool_val = CONDITIONS_OPERATORS[self.condition](_calc_expression(self.left, context))
             
        if bool_val:
            stack = self.true_stack
        else:
            stack = self.false_stack

        for node in stack: result.append(node.render(context))
        return ''.join(result)

    def __str__(self):
        return "<IF %s>" % self.left

class ForNode:
    def __init__(self, block, parent, line_num=None):
        self.parent = parent
        for_items = block.split()[1:]
        if ',' not in block:
            if len(for_items) != 3 or for_items[1] != 'in': raise TemplateSyntaxError("Wrong {%% for X in LIST %%} syntax: %s" % block, line_num)
            self.loop_var, self.loop_source= for_items[0], for_items[2]
            self.mode = 'list' 
        else:
            if not re.match(r"^for\s+[a-zA-Z]\w*\s*,\s*[a-zA-Z]\w*\s+in\s+[a-zA-Z]\w*(?:[\.|]items)?$", block):
                raise TemplateSyntaxError("Wrong {%% for X, Y in DICT %%} syntax: %s" % block, line_num)
            self.loop_source, _  = for_items.pop().replace('.items', '').replace('|items', ''), for_items.pop()
            self.loop_key, self.loop_value = ''.join(for_items).split(',')
            self.mode = 'dict'
        self.loop_stack, self.empty_stack = [], []
        self.stack = self.loop_stack

    def add(self, node):
        self.stack.append(node)

    def process_empty(self, block):
        if block != "empty": raise TemplateSyntaxError("Wrong {%% empty %%} syntax: %s" % block)
        self.stack = self.empty_stack

    def render(self, context):
        result = []
        loop_source = _calc_expression(self.loop_source, context)
        if not isinstance(loop_source, Iterable):
            raise TemplateSyntaxError("Loop source is not iterable in {%% for %%} block: ", self.loop_source)
        if self.mode == 'dict' and not isinstance(loop_source, Mapping):
            raise TemplateSyntaxError("Loop source is not mapping in {%% for x, y in dict.items %%} block: ", self.loop_source)
        if loop_source:
            counter = 0
            for loop_variable in loop_source:
                for node in self.loop_stack:
                    updated_context = dict(context)
                    updated_context.update({
                        'loopcounter0': counter,
                        'loopcounter': counter + 1,
                        'firstloop': True if counter == 0 else False,
                        'lastloop': True if counter == (len(loop_source) - 1) else False,
                    })
                    if self.mode == 'list': 
                        updated_context.update({
                            self.loop_var: loop_variable})
                    else:
                        updated_context.update({
                            self.loop_key: loop_variable,
                            self.loop_value: loop_source[loop_variable]})
                    result.append(node.render(updated_context))
                counter += 1
        else:
            for node in self.empty_stack:
                result.append(node.render(context))
        return ''.join(result)

    def __str__(self):
        return "<FOR %s IN %s>" % (self.loop_var, self.loop_source)

class BlockNode:
    def __init__(self, name, line_num=None):
        self.name = name
        self.stack = []

    def add(self, node):
        self.stack.append(node)

    def process_rewrite(self):
        self.stack.clear()

    def render(self, context):
        return ''.join([node.render(context) for node in self.stack])

    def __str__(self):
        return "<BLOCK %s>" % self.name

class WithNode:
    def __init__(self, block, parent, line_num=None):
        with_items = block.split()
        if len(with_items) != 4 or with_items[2] != 'as': raise TemplateSyntaxError("Wrong {% with var as alias %} syntax", block, line_num)
        self.variable, self.alias, self.stack, self.parent = with_items[1], with_items[3], [], parent
        

    def add(self, node):
        self.stack.append(node)

    def render(self, context):
        fixed_context = dict(context)
        fixed_context.update({self.alias: self.variable})
        return ''.join([node.render(fixed_context) for node in self.stack])

    def __str__(self):
        return "<WITH %s>" % self.alias

class Templater:
    def __init__(self, template, context=None, from_file=False):
        from shot import settings
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
            else:
                if from_file:
                    raise TemplateSyntaxError("Template not found", template)
        self.stack = []
        self.parent = self
        self.current_section = self
        self.parts = re.split(r'({{.*?}}|{%.*?%}|{#.*?#})', template)
        if context: self.context = context
        else: self.context = {}

    def add(self, node):
        self.stack.append(node)

    def extend(self, new_template):
        new_template.process()
        self.stack.extend(new_template.stack)

    def process(self):
        line_num = 1
        for part in self.parts:
            line_num += part.count("\n") 
            if part == "" or part.startswith('{#'):
                continue
            elif part.startswith('{{'):
                new_node = VariableNode(part[2:-2].strip())
                self.current_section.add(new_node)
            elif part.startswith('{%'):
                block = part[2:-2].strip()
                if block.startswith('if '):
                    new_node = IfNode(block, self.current_section)
                    self.current_section.add(new_node)
                    self.current_section = new_node
                elif block == "else":
                    try:
                        self.current_section.process_else(block)
                    except AttributeError:
                        raise TemplateSyntaxError("Wrong {%% else %%} placement", part, line_num)
                elif block == "endif":
                    if not isinstance(self.current_section, IfNode):
                        raise TemplateSyntaxError("Wrong {%% endif %%} placement", part, line_num)
                    self.current_section = self.current_section.parent
                elif block.startswith("for "):
                    new_node = ForNode(block, self.current_section)
                    self.current_section.add(new_node)
                    self.current_section = new_node
                elif block == "empty":
                    try:
                        self.current_section.process_empty(block)
                    except AttributeError:
                        raise TemplateSyntaxError("Wrong {%% empty %%} placement", part, line_num)
                elif block.startswith("endfor"):
                    if block != "endfor":
                        raise TemplateSyntaxError("Wrong {%% endfor %%} syntax", part, line_num)
                    if not isinstance(self.current_section, ForNode):
                        raise TemplateSyntaxError("Wrong {%% endfor %%} placement", part, line_num)
                    self.current_section = self.current_section.parent
                elif block.startswith("block"):
                    if self.current_section != self:
                        raise TemplateSyntaxError("Wrong {% block ... %} placement - it can't be nested in other nodes", part, line_num)
                    block_items = block.split()
                    if block_items[0] != "block" or len(block_items) != 2:
                        raise TemplateSyntaxError("Wrong {% block ... %} syntax", part, line_num)
                    name = block_items[1]
                    for node in self.stack:
                        if isinstance(node, BlockNode) and node.name == name:
                            self.current_section = node
                            node.process_rewrite()
                            break
                    else:
                        new_node = BlockNode(name)
                        self.current_section.add(new_node)
                        self.current_section = new_node
                elif block.startswith("endblock"):
                    if block != "endblock":
                        raise TemplateSyntaxError("Wrong {% endblock %} syntax", part, line_num)
                    if not isinstance(self.current_section, BlockNode):
                        raise TemplateSyntaxError("Wrong {% endblock %} placement, you should close other nodes first", part, line_num)
                    self.current_section = self
                elif block.startswith("extends "):
                    if self.current_section != self:
                        raise TemplateSyntaxError("Wrong placement of {% extends ... %} - it can't be nested in other nodes", part, line_num)
                    ext_items = block.split()
                    if len(ext_items) != 2 or ext_items[0] != "extends":
                        raise TemplateSyntaxError("Wrong syntax for {% extends ... %}", part, line_num)
                    template_filename = ext_items[1].replace("'", '').replace('"', '')
                    self.extend(Templater(template_filename, {}, True))
                elif block.startswith("with "):
                    new_node = WithNode(block, self.current_section, line_num)
                    self.current_section.add(new_node)
                    self.current_section = new_node
                elif block.startswith("endwith"):
                    if block != "endwith":
                        raise TemplateSyntaxError("Wrong {% endwith %} syntax", part, line_num)
                    if not isinstance(self.current_section, WithNode):
                        raise TemplateSyntaxError("Wrong {% endwith %} placement", part, line_num)
                    self.current_section = self.current_section.parent
                else:
                    raise TemplateSyntaxError("Wrong or unsupported block", part, line_num)
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

