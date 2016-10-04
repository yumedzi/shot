# shot #

shot is Python super micro web framework. It is designed to be super fast and super easy to use for writing simple tasks. 

Features:

* builtin Jinja-like template engine
* dev web server
* batteries for creating simple REST API.
* injection of `request` object (WSGI request wrapper) into views like in Flask.
* it can be used with SQLAlchemy as ORM.
 
# Example #

```
#!python

from shot import application, route, run

@route('/')
def main():
    return "Hello World"

if __name__ == '__main__':
    run(application)
```


### Documentation ###

* [Docs]()

# Contacts #

* [vityok@gmail.com](mailto:vityok@gmail.com)