from shot import application, route, render


@route('/')
def main(request):
    body = '''

<body>
<p>LINKS:</p>
<ul>
<li><a href="/hello">Test templates</a></li>
<li><a href="/debug">DEBUG ERROR page</a></li>
<li><a href="/404">404 ERROR page</a></li>
<li><a href="/500">500 ERROR page</a></li>
</ul>
</body>

'''
    return "Hello, it's a test of brand new micro web framework :)" + body

@route('/name')
def view_name(request):
    return "My name is John Stark"

@route('/hello')
def hello(request):
    import datetime
    template = """
    {% extends "basis.html" %}

    {% block content %}
    <h1>Hello to you!</h1>

    Today is {{ date }}
    <br/>
    Hello friend: {{ name }}!<br/>
    name|upper: {{ name|upper }}<br/>
    name|upper|lower: {{ name|upper|lower }}<br/>

    {% if name == "Alexey" %}Hello {{ name }} (IF worked!){% endif %}
    <br/>

    {% if name == "vasya" %}ddddd{%endif %}<br/>
    <ul>
        {% for friend in friends %}
        <li>FRIEND: {{ friend }}</li>
            {% for e in enemies %}
                <li>SUB item: {{ e }} (nested FOR)</li>
                {% if e == "3" %}
                <li style="margin-left: 20px;">LUCKY NUMBER 3 (nested IF in FOR is working)</li>
                {%endif%}
            {% endfor %}
        {% endfor %}      
    </ul>

    {% if name == "Alexey" %}<p>YOU SEE THIS?<br/> {% if surname == "Boobin" %}NESTED: {{ surname|upper }}{%endif%}{% endif %}
    {% endblock %}

    {% block title %}
    Block Title was changed OK!
    {% endblock %}
    """
    return render(template, {'date': datetime.datetime.utcnow().strftime("%a, %d %b %Y %X"), "enemies": [1,2,"3"],  "surname": "Boobin", "name": "Alexey", "friends": ["John", "Vasta", "Boobaoom"]})


@route("/debug")
def error_page(request):
    template = """
    {% if x y %}
    """
    return render(template)

@route("/500")
def view_500(request):
    return 1/0