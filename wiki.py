import webapp2, jinja2, re, os, hashlib, random, string

from google.appengine.ext import db

from google.appengine.api import memcache

from collections import namedtuple

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
    if not h or '|' not in h:
	return False
    salt = h[h.find('|') + 1:]
    return hashlib.sha256(name + pw + salt).hexdigest() == h[:h.find('|')]


def valid_cookie(user_id):
    if not user_id or '|' not in user_id:
	return None
    dbid = int(user_id[:user_id.find('|')]) if user_id[:user_id.find('|')].isdigit() else None
    if dbid:
	if WikiUser.get_by_id(dbid):
	    usr = WikiUser.get_by_id(dbid)
	    pw = usr.password[:usr.password.find('|')]
	    if pw == user_id[user_id.find('|') + 1:]:
		return usr
	    else:
		return ''
	else:
	    return ''
    else:
	return ''



class WikiUser(db.Model):
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
	elif db.GqlQuery("select * from WikiUser where username='%s'" % name).fetch(1):
	    errors['ername'] = "That user already exists."
	    self.render("signup.html", **errors)
	    return
	else:
	    passw = make_pw_hash(name, pw)
	    account = WikiUser(username = name, password = passw, email = email)
	    account.put()
	    cookie = str(account.key().id()) + '|' + passw[:passw.find('|')]
	    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % cookie)
	    self.redirect('/Final/wiki/')


class Login(Handler):
    def get(self):
	self.render('login.html')
    def post(self):
	name = self.request.get('username')
	pw = self.request.get('password')
	usr = db.GqlQuery("select * from WikiUser where username = '%s'" % name).fetch(1)
	if usr:
	    if valid_pw(name, pw, usr[0].password):
		cookie = str(usr[0].key().id()) + '|' + usr[0].password[:usr[0].password.find('|')]
		self.response.headers.add_header('Set-Cookie', "user_id=%s; Path=/" % str(cookie))
		self.redirect('/Final/wiki/')
	    else:
		self.render('login.html', erlogin = "Invalid login")
	else:
	    self.render('login.html', erlogin = "Invalid login")




class Pages(db.Model):
    page = db.StringProperty(required = True)
    content = db.TextProperty(required = True)



class Logout(Handler):
    def get(self):
	self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
	self.redirect("/Final/wiki/")


class WikiFront(Handler):
    def get(self):
	user = valid_cookie(self.request.cookies.get('user_id'))
	page = list(db.GqlQuery("select * from Pages where page='Main'"))
	if page:
	    self.render('wiki.html', user = user)
	    self.response.write(page[0].content)
	else:
	    self.render('wiki.html', user = user)
	    front = Pages(page = 'Main', content = '<h1>Welcome to the final!</h1>')
	    front.put()
	    self.response.write('<h1>Welcome to the final!</h1>')
	    



#class WikiPage(Handler):
#    def write_form(self, page):
#	user = valid_cookie(self.request.cookies.get('user_id'))
#	content = db.GqlQuery("select * from Pages where page = '%s'" % page).fetch(1)[0]
#	self.render('wiki.html', user = user, page = content)
#    def get(self, path):
#	path = self.request.path
#	if path == '/Final/wiki' or path == '/Final/wiki/':
#	    page = list(db.GqlQuery("select * from Pages where page = 'Main'"))
#	    if page:
#		self.write_form('Main')
#	    else:
#		wikipage = Pages(page = 'Main', content = '<h1>Welcome to the Final!</h1>')
#		wikipage.put()
#		self.render('wiki.html', user = valid_cookie(self.request.cookies.get('user_id')), content = '<h1>Welcome to the final!</h1>')
#	
#	else:
#	    page = list(db.GqlQuery("select * from Pages where page = '%s'" % path[12:]))
#	    if page:
#		self.write_form(path[12:])
#	    else:
#		self.redirect('/Final/wiki/_edit/%s' % path[12:])


class WikiPage(Handler):
    def write_form(self, page):
	user = valid_cookie(self.request.cookies.get('user_id'))
	content = db.GqlQuery("select * from Pages where page = '%s'" % page).fetch(1)[0]
	self.render('wiki.html', user = user, page = content.page)
	self.response.write(content.content)

    def get(self, page_name):
	page = list(db.GqlQuery("select * from Pages where page='%s'" % page_name))
	if page:
	    self.write_form(page_name)
	else:
	    if page_name == '/':
		p = Pages(page = '/', content = '<h1>Welcome to the final!</h1>')
		p.put()
		self.render('wiki.html', user = valid_cookie(self.request.cookies.get('user_id')), page = page_name)
		self.response.write('<h1>Welcome to the final!</h1>')
	    else:
	        self.redirect("/Final/wiki/_edit" + page_name)



#class EditPage(Handler):
#    def write_form(self, page):
#	user = valid_cookie(self.request.cookies.get('user_id'))
#	if not user:
#	    self.redirect('/Final/wiki/login')
#	else:
#	    content = list(db.GqlQuery('select * from Pages where page="%s"' % page))
#	    self.render('edit.html', content = content[0].content if content else '', user = user)
#    def get(self):
#	self.write_form(self.request.path[18:])
#    def post(self):
#	content = self.request.get('content')
#	page = db.GqlQuery('select * from Pages where page="%s"' % self.request.path[18:]).fetch(1)
#	if page:
#	    page[0].content = content
#	    self.redirect('/Final/wiki/_edit/%s' % self.request.path[18:])
#	else:
#	    page = Pages(page = self.request.path[18:], content = content)
#	    page.put()
#	    self.redirect('/Final/wiki/_edit/%s' % self.request.path[18:])




class EditPage(Handler):
    def write_form(self, page, path):
	user = valid_cookie(self.request.cookies.get('user_id'))
	if not user:
	    self.redirect('/Final/wiki/login')
	else:
	    content = list(db.GqlQuery("select * from Pages where page='%s'" % page))
	    if content:
		self.render('edit.html', user = user, content = content[0].content, page = path)
	    else:
		self.render('edit.html', user = user, page = path)
    def get(self, page_name):
	self.write_form(page_name, page_name)
    def post(self, path):
	content = self.request.get('content')
	page = list(db.GqlQuery("select * from Pages where page='%s'" % path))
	if page:
	    update = page[0]
	    update.delete()
	    new = Pages(page = path, content = content)
	    new.put()
	    self.redirect('/Final/wiki%s' % path)
	    return
	else:
	    newpage = Pages(page = path, content = content)
	    newpage.put()
	    self.redirect('/Final/wiki%s' % path)
	    return



class Bridge(Handler):
    def get(self, path):
	self.redirect('/Final/wiki%s' % path)




PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'


app = webapp2.WSGIApplication([("/Final/wiki/signup", Signup), 
			       ("/Final/wiki/login", Login), 
			       ("/Final/wiki/logout", Logout), 
			       ("/Final/wiki/bridge" + PAGE_RE, Bridge), 
			       ("/Final/wiki/_edit" + PAGE_RE, EditPage), 
			       ("/Final/wiki" + PAGE_RE, WikiPage)],
                              debug=True)
