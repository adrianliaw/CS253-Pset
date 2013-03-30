import webapp2

import cgi

import re

import jinja2

import os

import json

import time

from google.appengine.ext import db

from collections import namedtuple

from random import randrange



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



def answer():
	game_answer = []
	num_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
	for i in range(0, 4):
    	    ans = randrange(len(num_range))
	    game_answer.append(num_range[ans])
	    num_range.remove(num_range[ans])
	return game_answer

def escape_html(s):
    return cgi.escape(s, quote=True)

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

def rot13(string):
    result = []
    letters = []
    for i in range(97, 123):
        letters.append(chr(i))
    LETTERS = []
    for i in range(65, 91):
        LETTERS.append(chr(i))
    for letter in string:
        if letter in letters:
            result.append(letters[(letters.index(letter) + 13) % 26])
        elif letter in LETTERS:
            result.append(LETTERS[(LETTERS.index(letter) + 13) % 26])
        else:
            result.append(letter)
    return "".join(result)





class MainHandler(Handler):
    def get(self):
        self.render("front.html")



class SignupHandler(Handler):
    def write_form(self, name="", email="", invalidname="", invalidpassword="", verifypassword="", invalidemail=""):
        self.render("signup.html" , name = name, email = email, invalidname = invalidname, invalidpassword = invalidpassword, verifypassword = verifypassword, invalidemail = invalidemail)
    
    def get(self):
        self.write_form()

    def post(self):
        username = escape_html(self.request.get("username"))
        email = escape_html(self.request.get("email"))
        user_username = valid_username(username)
        user_password = valid_password(self.request.get("password"))
        user_verify = verify_password(self.request.get("password"), self.request.get("verify"))
        user_email = valid_email(email)
        invalids = []
        if not user_username:
            invalids.append("That's not a valid username.")
        else:
            invalids.append("")
        if not user_password:
            invalids.append("That's not a valid password.")
        else:
            invalids.append("")
        if not user_email:
            invalids.append("That's not a valid email.")
        else:
            invalids.append("")

        if (user_username and user_password and user_email):
            if not user_verify:
                self.write_form(self.request.get("username"), self.request.get("email"), "", "", "Your passwords didn't match")
                return
            else:
                self.redirect("/Unit2/signup/Welcome?name=" + self.request.get("username"))
                return
        if user_password:
            if user_verify:
                self.write_form(self.request.get("username"), self.request.get("email"), invalids[0], invalids[1], "", invalids[2])
            else:
                self.write_form(self.request.get("username"), self.request.get("email"), invalids[0], invalids[1], "Your passwords didn't match", invalids[2])
        else:
            self.write_form(self.request.get("username"), self.request.get("email"), invalids[0], invalids[1], "", invalids[2])
        
            


class Rot13Handler(Handler):
    def get(self):
        text = ""
        self.render("rot13.html", text = text)

    def post(self):
        text = self.request.get("text")
        self.render("rot13.html", text = rot13(text))

class HelloUdacityHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Hello, Udacity!")

welcomeform = """
<html>
<head>
<title>Welcome</title>
</head>
<body>
<font face="Comic Sans MS" size="8">Welcome,  %s !
"""

class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        name = self.request.get("name")
        if not valid_username(name):
            self.redirect('/Unit2/signup')
        else:
            self.response.out.write(welcomeform % name)


class Artdb(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    

class AsciiArtHandler(Handler):
    def render_front(self, title = "", art = "", error = ""):
        arts = db.GqlQuery("SELECT * FROM Artdb ORDER BY created DESC")
        self.render("asciiart.html", title = title, art = art, error = error, arts = arts)
    def get(self):
        self.render_front()
    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        if title and art:
            a = Artdb(title = title, art = art)
            a.put()
            self.redirect('/Fun/ASCIIart')
        else:
            error = "We need both a title and some artwork!"
            self.render_front(title, art, error)


class Entrydb(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

class PermalinkHandler(Handler):
    def get(self, post_id):
	entry = Entrydb.get_by_id(int(post_id))
	self.render("blog.html", entries = [entry])


class BlogHandler(Handler):
    def get(self):
	entries = db.GqlQuery("select * from Entrydb order by created desc")
	self.render("blog.html", entries = entries)
	


class NewPostHandler(Handler):
    def render_front(self, subject = "", content = "", error = ""):
	self.render("newpost.html", subject = subject, content = content, error = error)
    def get(self):
	self.render_front()
    def post(self):
	subject = self.request.get("subject")
	content = self.request.get("content")

	if subject and content:
	    toput = Entrydb(subject = subject, content = content)
	    toput.put()
	    pageid = str(toput.key().id())
	    self.redirect("/Unit3/blog/%s" % pageid)
	else:
	    error = "SUBJECT and CONTENT, please."
	    self.render_front(subject, content, error)
	    


class BlogJson(Handler):
    def get(self):
	self.response.headers['Content-Type'] = 'application/json'
	entries = db.GqlQuery("select * from Entrydb order by created desc")
	j = []
	for entry in entries.fetch(100):
	    ct = entry.created.timetuple()
	    lmt = entry.last_modified.timetuple()
	    j.append({"subject": entry.subject, "content": entry.content, "created": time.asctime(ct), "last_modified": time.asctime(lmt)})
	self.write(json.dumps(j))


class PermalinkJson(Handler):
    def get(self, post_id):
	self.response.headers['Content-Type'] = 'application/json'
	entry = Entrydb.get_by_id(int(post_id))
	ct = entry.created.timetuple()
	lmt = entry.last_modified.timetuple()
	self.write(json.dumps({"subject": entry.subject, "content": entry.content, "created": time.asctime(ct), "last_modified": time.asctime(lmt)}))




class BGColorHandler(Handler):
    def get(self):
        self.render("bgcolor.html")
        

class ABgameHandler(Handler):
    def get(self):
	self.render("ABgame.html")

class ABgamePlay(Handler):
    
    guesses = namedtuple('guess', ['count', 'guessing', 'response'])
    game_ans = answer()
    user_guess = []
    guess_count = 0



    def get(self):
	self.game_ans = answer()
	self.user_guess = []
	self.guess_count = 0
	self.render("ABgameplay.html", error = '')
    def post(self):
	guess_list = [self.request.get("first"), self.request.get("second"), self.request.get("third"), self.request.get("fourth")]
	for number in guess_list:
	    if guess_list.count(number) > 1:
		error = "Your guess can't repeat any number."
		self.render("ABgameplay.html", user_guess = self.user_guess, error = error)
		return
	self.guess_count = self.guess_count.__add__(len(self.user_guess) + 1)
	A = 0
	B = 0
	for a in range(0, 4):
            if int(guess_list[a]) == self.game_ans[a]:
                A += 1
            elif int(guess_list[a]) in self.game_ans:
                B += 1

	
	if self.guesses(str(self.guess_count), ''.join(guess_list), str(A) + 'A' + str(B) + 'B') in self.user_guess:
		self.render('ABgameplay.html', user_guess = self.user_guess, error = "Can't guess same numbers.")

	elif A:
	    

	    if A == 4:
		if self.guess_count > 15:
		    self.render("ABgameWin.html", guess_count = str(self.guess_count), grade = "Too Bad! BOOOOOOOO!")
		    self.game_ans, self.user_guess, self.guess_count = answer(), [], 0
		elif self.guess_count > 9:
		    self.render("ABgameWin.html", guess_count = str(self.guess_count), grade = "Not Bad!")
		    self.game_ans, self.user_guess, self.guess_count = answer(), [], 0
		elif self.guess_count > 5:
		    self.render("ABgameWin.html", guess_count = str(self.guess_count), grade = "Nice! Great Job!")
		    self.game_ans, self.user_guess, self.guess_count = answer(), [], 0
		else:
		    self.render("ABgameWin.html", guess_count = str(self.guess_count), grade = "You're AWESOME")
		    self.game_ans, self.user_guess, self.guess_count = answer(), [], 0

	    
	    elif B:
		self.user_guess.append(self.guesses(str(self.guess_count), ''.join(guess_list), str(A) + 'A' + str(B) + 'B'))
		self.render("ABgameplay.html", user_guess = self.user_guess, error = '')
	    
	    else:
		self.user_guess.append(self.guesses(str(self.guess_count), ''.join(guess_list), str(A) + 'A'))
		self.render("ABgameplay.html", user_guess = self.user_guess, error = '')
	elif B:
	    self.user_guess.append(self.guesses(str(self.guess_count), ''.join(guess_list), str(B) + 'B'))
	    self.render("ABgameplay.html", user_guess = self.user_guess, error = '')
	else:
	    self.user_guess.append(self.guesses(str(self.guess_count), ''.join(guess_list), 'Nothing'))
	    self.render("ABgameplay.html", user_guess = self.user_guess, error = '')
	




app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/Unit2/signup', SignupHandler),
                               ('/Unit2/rot13', Rot13Handler),
                               ("/Unit1/HelloUdacity", HelloUdacityHandler),
                               ("/Unit2/signup/Welcome", WelcomeHandler),
                               ("/Fun/ASCIIart", AsciiArtHandler), 
                               ("/Fun/BGcolors", BGColorHandler), 
			       ("/Unit3/blog", BlogHandler), 
			       ("/Unit3/blog/.json", BlogJson), 
			       ("/Unit3/blog/newpost", NewPostHandler), 
			       ("/Unit3/blog/(\d+)", PermalinkHandler), 
			       ("/Unit3/blog/(\d+).json", PermalinkJson), 
			       ("/Fun/ABgame", ABgameHandler), 
			       ("/Fun/ABgame/play", ABgamePlay)],
                              debug=True)
