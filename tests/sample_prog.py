from shot import application, route, render


@route('/')
def main(request):
    body = '''

<body>
<p>LINKS:</p>
<ul>
<li><a href="/hello">Test templates</a></li>
<li><a href="/nice">Nice page / BS4</a></li>
<li><a href="/debug">DEBUG ERROR page</a></li>
<li><a href="/404">404 ERROR page</a></li>
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
    <h1>Hello to you!</h1>

    {% block title %}
    <p>TITLE BEFORE</p>
    {% endblock %}

    Today is {{ date }}
    <br/>
    Hello friend: {{ name }}!<br/>
    Name in upper: {{ name|upper }}<br/>
    Name in upper/lower: {{ name|upper|lower }}<br/>

    {% if name == "Alexey" %}Hello dearest friend {{ name }}! {% endif %}
    <br/>

    {% if name == "vasya" %}ddddd{%endif %}<br/>
    <ul>
        {% for friend in friends %}
        <li>FRIEND: {{ friend }}</li>
            {% for e in enemies %}
                <li>SUB item: {{ e}}</li>
                {% if e == "3" %}
                <li>LUCKY NUMBER 3!!!!!!!</li>
                {%endif%}
            {% endfor %}
        {% endfor %}      
    </ul>

    {% if name == "Alexey" %}<p>YOU SEE THIS?<br/> {% if surname == "Boobin" %}NESTED: {{ surname|upper }}{%endif%}{% endif %}

    {% block title %}
    changing title afterwards!!!
    {% endblock %}

    """
    return render(template, {'date': datetime.datetime.utcnow().strftime("%a, %d %b %Y %X"), "enemies": [1,2,3],  "surname": "Boobin", "name": "Alexey", "friends": ["John", "Vasta", "Boobaoom"]})

@route("/nice")
def nice(request):
    return render('shot/assets/exc.html')


@route("/debug")
def error_page(request):
    template = """
    {% if x y %}
    """
    return render(template)