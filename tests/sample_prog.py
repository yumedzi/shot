from shot import application, route, render_template_str


@route('/')
def main(request):
    body = '''

<body>
<a href="/hello">Test templates</a>
</body>


'''
    return "Hello, it's a test of brand new micro web framework :)" + body

@route('/name')
def view_name(request):
    return "My name is John Stark"

@route('/hello')
def hello():
    template = """
    <h1>Hello to you!</h1>

    Today is {{ date }}
    <br/>
    {% if name == "Alexey" %}Hello dearest friend Alexey! {%endif%}
    <br/>

    {% if name == "vasya" %}Hello Vasya!{% else %}Hello: {{ name }}{% endif %}

    {% block content %}hehehee{% endblock %}

    """
    return render_template_str(template, {'date': datetime.datetime.utcnow().strftime("%a, %d %b %Y %X"), "name": "Alexey"})
