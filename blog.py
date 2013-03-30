import webapp2, jinja2, time, json, os, re, hashlib, random, string

from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__),"templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),autoescape = True)



class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

    def render_str(self,template,**params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))


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


def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))


def make_pw_hash(name, pw):
    salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s|%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h[h.find('|') + 1:]
    return hashlib.sha256(name + pw + salt).hexdigest() == h[:h.find('|')]


class Entry(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

class PermalinkHandler(Handler):
    def get(self, post_id):
	entry = Entry.get_by_id(int(post_id))
	self.render("blog2.html", entries = [entry])


class BlogHandler(Handler):
    def get(self):
	entries = db.GqlQuery("select * from Entry order by created desc")
	self.render("blog2.html", entries = entries)
	


class NewPostHandler(Handler):
    def render_front(self, subject = "", content = "", error = ""):
	self.render("newpost2.html", subject = subject, content = content, error = error)
    def get(self):
	self.render_front()
    def post(self):
	subject = self.request.get("subject")
	content = self.request.get("content")

	if subject and content:
	    toput = Entry(subject = subject, content = content)
	    toput.put()
	    pageid = str(toput.key().id())
	    self.redirect("/Unit5/blog/%s" % pageid)
	else:
	    error = "SUBJECT and CONTENT, please."
	    self.render_front(subject, content, error)
	    


class BlogJson(Handler):
    def get(self):
	self.response.headers['Content-Type'] = 'application/json'
	entries = db.GqlQuery("select * from Entry order by created desc")
	j = []
	for entry in entries.fetch(100):
	    ct = entry.created.timetuple()
	    lmt = entry.last_modified.timetuple()
	    j.append({"subject": entry.subject, "content": entry.content, "created": time.asctime(ct), "last_modified": time.asctime(lmt)})
	self.write(json.dumps(j))


class PermalinkJson(Handler):
    def get(self, post_id):
	self.response.headers['Content-Type'] = 'application/json'
	entry = Entry.get_by_id(int(post_id))
	ct = entry.created.timetuple()
	lmt = entry.last_modified.timetuple()
	self.write(json.dumps({"subject": entry.subject, "content": entry.content, "created": time.asctime(ct), "last_modified": time.asctime(lmt)}))



class Users(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    email = db.StringProperty()



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
	elif db.GqlQuery("select * from Users where username='%s'" % name).fetch(1):
	    errors['ername'] = "That user already exists."
	    errors['name'] = ""
	    self.render("signup.html", **errors)
	    return
	else:
	    passw = make_pw_hash(name, pw)
	    account = Users(username = name, password = passw, email = email)
	    account.put()
	    cookie = str(account.key().id()) + '|' + passw[:passw.find('|')]
	    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % cookie)
	    self.redirect('/Unit5/blog/welcome')
	    	    


class Login(Handler):
    def get(self):
	self.render('login.html')
    def post(self):
	name = self.request.get('username')
	pw = self.request.get('password')
	usr = db.GqlQuery("select * from Users where username = '%s'" % name).fetch(1)
	if usr:
	    if valid_pw(name, pw, usr[0].password):
		cookie = str(usr[0].key().id()) + '|' + usr[0].password[:usr[0].password.find('|')]
		self.response.headers.add_header('Set-Cookie', "user_id=%s; Path=/" % str(cookie))
		self.redirect('/Unit5/blog/welcome')
	    else:
		self.render('login.html', erlogin = "Invalid login")
	else:
	    self.render('login.html', erlogin = "Invalid login")




class Logout(Handler):
    def get(self):
	self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
	self.redirect("/Unit5/blog/signup")




class Welcome(Handler):
    def get(self):
	cookie = self.request.cookies.get("user_id")
	if not cookie or '|' not in cookie:
	    self.redirect('/Unit5/blog/signup')
	    return
	entity = Users.get_by_id(int(cookie[:cookie.find('|')]))
	if entity:
	    if entity.password[:entity.password.find('|')] == cookie[cookie.find('|') + 1:]:
		self.render('welcome.html', name = entity.username)
	    else:
		self.redirect('/Unit5/blog/signup')
	else:
	    self.redirect('/Unit5/blog/signup')







app = webapp2.WSGIApplication([("/Unit5/blog/signup", Signup), ("/Unit5/blog/welcome", Welcome), ("/Unit5/blog/login", Login), ("/Unit5/blog/logout", Logout), ("/Unit5/blog", BlogHandler), ("/Unit5/blog/.json", BlogJson), ("/Unit5/blog/(\d+)", PermalinkHandler), ("/Unit5/blog/(\d+).json", PermalinkJson), ("/Unit5/blog/newpost", NewPostHandler)], debug = True)
