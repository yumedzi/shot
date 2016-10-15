from shot import application, route, render, run


@route('/')
def main(request):
    body = '''

<body>
<p>LINKS:</p>
<ul>
<li><a href="/name">Simple var</a></li>
<li><a href="/test_me/Johnny">Parametrized route - should output "Johnny"</a></li>
<li><a href="/test_me_2/Sarah/3434/45.4/hehe">Cmplex Parametrized</a></li>
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
    context = {'date': datetime.datetime.utcnow().strftime("%a, %d %b %Y %X"), 
               "enemies": [1,2,"3"],  "surname": "Boobin", "name": "Alexey", 
               "friends": ["John", "Vasta", "Boobaoom"],
               "empty_var": (), "empty_list": [], 'test_dict': {x:1 for x in "ABC"}
    }

    return render(template, context)


@route("/debug")
def error_page(request):
    template = """
    {% if 11 x %}
    """
    return render(template)

@route("/500")
def view_500(request):
    return 1/0

@route("/test_me/<name>")
def view_parametrized(request, name):
    return render('Your name is {{ name }}', {'name': name})


@route("/test_me_2/<name>/<int:age>/<float:money>/<path:path>")
def view_parametrized_complex(request, name, age, money, path):
    tmpl = '''
    <p>Name is {{name}}</p>
    <p>Age is {{age}}</p>
    <p>Money is {{money}}</p>
    <p>Path is {{path}}</p>
    '''

    return render(tmpl, {'name': name, 'age': age, 'money': money, 'path': path})


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
        <input name="some_file" type="file"/><br/>
        <button type="submit">SUBMIT</button>
</form></body></html>
    '''
    print(">>> METHOD:", request.method)
    print(">>> FILES:", request.FILES)
    print(">>> POST:", request.POST)
    print(">>> GET:", request.GET)

    for files_ in request.FILES:
        for f in request.FILES[files_]:
            print("------")
            print(f.read())


    return render(t)

if __name__ == '__main__':
    run('', 9999)