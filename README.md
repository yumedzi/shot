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
* wrapping REQUEST (GET/POST, form multipart data) - YES
* template engine - YES
* dev server - YES
* reloading dev server in DEBUG - NO
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
from shot import application, route, render, run

@route('/')
def main(request):
    return "Hello World"

@route('/name')
def example(request):
    return render('example.html', {'name': 'John Stark', 'brothers': ['Rickon', 'Bran', 'Robb']})

if __name__ == '__main__':
    run()
```
* Template `'templates/example.html'`:

```html
{% extends 'main.html' %}

{% block contents %}
<p>Hello, {{ name|capitalize }}

Your brothers:
<ul>
{% for brother in brothers %}
<li>Brother number {{ loopcounter }}: {{ brother }} </li>
{% empty %}
... sorry, you don't have any left.
{% endfor %}
</ul>
{% endblock %}
```
* Running:

```sh
python prog.py
```
or
```sh
gunicorn prog
```

* The web app will be hosted at `http://127.0.0.1:8000/`

### Dev plan ###
1. Dev server ---> 0.5
2. Extended routing rules ---> 0.6
3. ORM  ---> 0.7
4. REST --- 0.8


### Documentation ###

... Will be here soon ...

# Contacts #

* [vityok@gmail.com](mailto:vityok@gmail.com)
