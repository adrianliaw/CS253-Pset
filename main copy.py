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
	




app = webapp2.WSGIApplication([("/Fun/ABgame", ABgameHandler), 
			       ("/Fun/ABgame/play", ABgamePlay)],
                              debug=True)
