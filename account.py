import webapp2, jinja2, os, hashlib, random, string, re

from google.appengine.ext import db



template_dir = os.path.join(os.path.dirname(__file__),"templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),autoescape = True)


def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))


def make_pw_hash(name, pw):
    salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s|%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h[h.find('|') + 1:]
    return hashlib.sha256(name + pw + salt).hexdigest() == h[:h.find('|')]


def valid_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return USER_RE.match(username)

def valid_password(password):
    USER_RE = re.compile(r"^.{3,20}$")
    return USER_RE.match(password)

def verify_password(password, verify):
    return password == verify

def valid_email(email):
    USER_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
    return USER_RE.match(email) or email == ""




class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

    def render_str(self,template,**params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))



class UserDB(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    email = db.StringProperty()


class Account(Handler):
    def get(self):
	self.render("account.html")

class Signup(Handler):
    def get(self):
	self.render("signup.html")
	self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def post(self):
	name = self.request.get("username")
	pw = self.request.get("password")
	ver = self.request.get("verify")
	email = self.request.get("email")
	errors = {}
	if not valid_username(name):
	    errors['ername'] = "That's not a valid username."
	errors['name'] = name
	if valid_password(pw):
	    if not verify_password(pw, ver):
		errors['verpassword'] = "Your passwords didn't match."
	else:
	    errors['erpassword'] = "That wasn't a valid password."
	if not valid_email(email):
	    errors['eremail'] = "That's not a valid email."
	errors['email'] = email
	if 'ername' in errors or 'erpassword' in errors or 'verpassword' in errors or 'eremail' in errors:
	    self.render("signup.html", **errors)
	    return
	elif db.GqlQuery("select * from UserDB where username='%s'" % name).fetch(1):
	    errors['ername'] = "That user already exists."
	    errors['name'] = ""
	    self.render("signup.html", **errors)
	    return
	else:
	    passw = make_pw_hash(name, pw)
	    account = UserDB(username = name, password = passw, email = email)
	    account.put()
	    cookie = str(account.key().id()) + '|' + passw[:passw.find('|')]
	    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % cookie)
	    self.redirect('/Unit4/welcome')
	    	    


class Login(Handler):
    def get(self):
	self.render('login.html')
    def post(self):
	name = self.request.get('username')
	pw = self.request.get('password')
	usr = db.GqlQuery("select * from UserDB where username = '%s'" % name).fetch(1)
	if usr:
	    if valid_pw(name, pw, usr[0].password):
		cookie = str(usr[0].key().id()) + '|' + usr[0].password[:usr[0].password.find('|')]
		self.response.headers.add_header('Set-Cookie', "user_id=%s; Path=/" % str(cookie))
		self.redirect('/Unit4/welcome')
	    else:
		self.render('login.html', erlogin = "Invalid login")
	else:
	    self.render('login.html', erlogin = "Invalid login")




class Logout(Handler):
    def get(self):
	self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
	self.redirect("/Unit4/signup")




class Welcome(Handler):
    def get(self):
	cookie = self.request.cookies.get("user_id")
	if not cookie or '|' not in cookie:
	    self.redirect('/Unit4/signup')
	    return
	entity = UserDB.get_by_id(int(cookie[:cookie.find('|')]))
	if entity:
	    if entity.password[:entity.password.find('|')] == cookie[cookie.find('|') + 1:]:
		self.render('welcome.html', name = entity.username)
	    else:
		self.redirect('/Unit4/signup')
	else:
	    self.redirect('/Unit4/signup')





app = webapp2.WSGIApplication([("/Unit4/account", Account), ("/Unit4/signup", Signup), ("/Unit4/welcome", Welcome), ("/Unit4/login", Login), ("/Unit4/logout", Logout)], debug = True)
