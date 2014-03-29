import webapp2
from google.appengine.ext import db
from lib import utils
from lib.db.users import User
from lib.db.pages import Page, pages_key

### Main Handler ###
class WikiHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return utils.render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = utils.make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and utils.check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))
	
	def notfound(self):
		self.error(404)
		self.write('<h1>404: Not Found</h1>Sorry, but that page does not exist.')

### Registration/Login/Logout ###
class Signup(WikiHandler):
	def get(self):
		self.render("signup-form.html")

	def post(self):
		have_error = False
		self.username = self.request.get('username')
		self.password = self.request.get('password')
		self.verify = self.request.get('verify')
		self.email = self.request.get('email')

		params = dict(username = self.username,
						email = self.email)

		if not utils.valid_username(self.username):
			params['error_username'] = "That's not a valid username."
			have_error = True

		if not utils.valid_password(self.password):
			params['error_password'] = "That wasn't a valid password."
			have_error = True
		elif self.password != self.verify:
			params['error_verify'] = "Your passwords didn't match."
			have_error = True

		if not utils.valid_email(self.email):
			params['error_email'] = "That's not a valid email."
			have_error = True

		if have_error:
			self.render('signup-form.html', **params)
		else:
			self.done()

	def done(self, *a, **kw):
		raise NotImplementedError

class Register(Signup):
    def done(self):
		u = User.by_name(self.username)
		if u:
			msg = 'That user already exists.'
			self.render('signup-form.html', error_username = msg)
		else:
			u = User.register(self.username, self.password, self.email)
			u.put()

			self.login(u)
			self.redirect('/welcome')

class Login(WikiHandler):
	def get(self):
		self.render('login-form.html')

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')

		u = User.login(username, password)
		if u:
			self.login(u)
			self.redirect('/welcome')
		else:
			msg = 'Invalid login'
			self.render('login-form.html', error = msg)

class Logout(WikiHandler):
    def get(self):
		next_url = self.request.headers.get('referer', '/')
		self.logout()
		self.redirect(next_url)

class Welcome(WikiHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/signup')

### Wiki Stuff ###
class WikiPage(WikiHandler):
	def get(self, path):
		v = self.request.get('v')
		p = None
		if v:
			if v.isdigit():
				p = Page.by_id(int(v), path)
			if not p:
				return self.notfound()
		else:
			p = Page.by_path(path).get()
		
		if p:
			self.render("permalink.html", page = p, path = path)
		else:
			self.redirect('/_edit' + path)

class EditPage(WikiHandler):
	def get(self, path):	
		if not self.user:
			self.redirect('/login')
			
		v = self.request.get('v')
		p = None
		if v:
			if v.isdigit():
				p = Page.by_id(int(v), path)
			if not p:
				return self.notfound()
		else:
			p = Page.by_path(path).get()
			
		self.render("newpost.html", path = path, page = p)

	def post(self, path):
		if not self.user:
			self.error(400)
			return

		content = self.request.get('content')
		old_page = Page.by_path(path).get()
		author = self.user.name
		
		if not (old_page or content):
			error = "Please enter some new content!"
			self.render("newpost.html", error=error)
			return
		elif not old_page or old_page.content != content:
			p = Page(parent = Page.parent_key(path), content=content, author=author)
			p.put()
			
		self.redirect(path)

class HistoryPage(WikiHandler):
	def get(self, path):
		q = Page.by_path(path)
		q.fetch(limit = 100)
		
		posts = list(q)
		if posts:
			self.render("history.html", path = path, posts = posts)
		else:
			self.redirect("/_edit" + path)

### Routing Table ###
app = webapp2.WSGIApplication([('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/welcome', Welcome),
							   ('/_history' + utils.PAGE_RE, HistoryPage),
							   ('/_edit' + utils.PAGE_RE, EditPage),
							   (utils.PAGE_RE, WikiPage),
                               ],
                              debug=True)
