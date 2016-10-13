# shot #

shot is Python super micro web framework. It is designed to be super fast and super easy to use for writing simple tasks. 

Features:

* builtin Jinja-like template engine
* dev web server
* batteries for creating simple REST API.
* injection of `request` object (WSGI request wrapper) into views like in Flask.
* it can be used with SQLAlchemy as ORM.

# Current status #

* routing - YES
* wrapping REQUEST (multiform, POST data) - YES
* template engine - YES
* dev server - NO
* parametrized routing - NO
* Docs - NO
* REST API batteries - NO
* ORM integration batteries - NO

# Example #

```sh
pip install shot, gunicorn
```

* Example "prog.py":

```python
#!python

from shot import application, route, render

@route('/')
def main(request):
    return "Hello World <br/> <a href='/name'>click me</a>"

@route('/name')
def example(request):
    return render('example.html', {'name': 'John Stark', 'brothers': ['Rickon', 'Bran', 'Robb']})
```
* Template:

```html
{% extends 'main.html' %}

{% block contents %}
<p>Hello, {{ name|capitalize }}

Your brothers:
<ul>
{% for brother in brothers %}
<li> {{ brother }} </li>
{% empty %}
... sorry, you don't have any left.
{% endfor %}
</ul>
{% endblock %}
```
* Running:

```sh
gunicorn prog
```

### Documentation ###

... Will be here soon ...

# Contacts #

* [vityok@gmail.com](mailto:vityok@gmail.com)
