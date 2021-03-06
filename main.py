from bottle import Bottle, ServerAdapter
from bottle import run, debug, route, error, static_file, template, request
import tempmail
import os
import requests
from faker import Faker

fake = Faker()


class WSGIServer(ServerAdapter):
    server = None
    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        self.server = make_server(self.host, self.port, handler, **self.options)
        self.server.serve_forever()


    def stop(self):
        import threading
        threading.Thread(target=self.server.shutdown).start()
        self.server.server_close()


@route('/__exit', method=['GET','HEAD'])
def __exit():
    global server
    server.stop()


@route('/favicon.ico')
def get_favicon():
    return static_file('favicon.ico', root='./templates/')


@route('/')
def home():
    return template('templates/home.html', address="@" + tempmail.domains()[0]["domain"], password='Password')


@route('/inbox', method='POST')
def inbox():
    address = request.forms.get('email')

    if '@' in address:
        return '<script>alert("Input only username"); window.location.replace("/")</script>'
    
    address = address + "@" + tempmail.domains()[0]["domain"]
    if len(address.split('@')[0]) == 0:
        address = fake.user_name() + "@" + tempmail.domains()[0]["domain"]

    password = request.forms.get('password')
    if len(password) == 0:
        password = fake.password()

    my_mail = tempmail.TempMail(address, password)
    account = my_mail.generate()
    inbox_mail = my_mail.get_messages()

    if len(inbox_mail) == 0:
        inbox_msg = "<center><br><p>Waiting for new messages.</p></center>"

    else:
        inbox_msg = str()
        header = ({"Authorization": "bearer " + my_mail._token})

        for x in range(len(inbox_mail)):
            _id = inbox_mail[x]["id"]
            html = requests.get("https://api.mail.tm/messages/" + _id, headers=header).json()["html"][0]
            open('templates/' + _id + '.html', 'w').write(html)
            inbox_msg = inbox_msg + f'''<p><br><b>From:</b> {inbox_mail[x]["from"]["address"]}
<br><b>Subject:</b> {inbox_mail[x]["subject"]}
<br><b>Message:</b> {inbox_mail[x]["intro"]}</p>
<center><a target="blank" href="full/{_id}">[See Full Message]</a></center>'''

    return template('templates/inbox.html', inbox_messages=inbox_msg, address=address, msg_num=len(inbox_mail), password=password)


@route('/full/<id>', method='GET')
def full_message(id):
    return template('templates/' + id + '.html')


@route('/inbox', method='GET')
def redirect():
    return '<script>window.location.replace("/")</script>'


app = Bottle()
app.route('/', method='GET')(home)
app.route('/inbox', method='POST')(inbox)
app.route('/inbox', method='GET')(redirect)
app.route('/__exit', method=['GET','HEAD'])(__exit)
app.route('/favicon.ico', method='GET')(get_favicon)
app.route('/full/<id>', method='GET')(full_message)

try:
    server = WSGIServer(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    app.run(server=server,reloader=False)
except Exception as ex:
    errs = "Exception: %s" % repr(ex)
    print(errs)
