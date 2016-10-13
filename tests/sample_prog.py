from shot import application, route, render


@route('/')
def main(request):
    body = '''

<body>
<p>LINKS:</p>
<ul>
<li><a href="/name">Simple var</a></li>
<li><a href="/hello">Test templates</a></li>
<li><a href="/debug">DEBUG ERROR page</a></li>
<li><a href="/404">404 ERROR page</a></li>
<li><a href="/500">500 ERROR page</a></li>
<li><a href="/post">Testing POST/GET forms</a></li>
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
    template = 'test.html'
    return render(template, {'date': datetime.datetime.utcnow().strftime("%a, %d %b %Y %X"), "enemies": [1,2,"3"],  "surname": "Boobin", "name": "Alexey", "friends": ["John", "Vasta", "Boobaoom"]})


@route("/debug")
def error_page(request):
    template = """
    {% if 11 x %}
    """
    return render(template)

@route("/500")
def view_500(request):
    return 1/0

@route("/post")
def view_post(request):
    t = '''<html><body>
    <form method='post' action="/post" enctype="multipart/form-data">
        <input name="input_1" type="input" value="111"/><br/>
        <input name="input_1" type="input" value="222"/><br/>
        <input name="name1" type="input" value="asdasd"/><br/>
        <input name="name2" type="hidden" value="3132123"/>
        <input name="password" type="password" value="AAAAVBBVCXSD"/><br/>
        <input name="some_file" type="file"/><br/>
        <button type="submit">SUBMIT</button>
</form></body></html>
    '''
    print(">>> METHOD:", request.method)
    print(">>> FILES:", request.FILES)
    print(">>> POST:", request.POST)
    print(">>> GET:", request.GET)

    for file_ in request.FILES:
        f = request.FILES[file_]
        print("Found file:", dir(f))
        print("------")
        print(f.read())


    return render(t)