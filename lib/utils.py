###Useful functions###
import hmac
import hashlib
import random
import re
import os
import jinja2
from string import letters
from lib.secret import SECRET

### Jinja Templates ###
template_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'templates'))
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
									autoescape = True)

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

#cookies#
def make_secure_val(val):
	return '%s|%s' % (val, hmac.new(SECRET, val).hexdigest())

def check_secure_val(secure_val):
	val = secure_val.split('|')[0]
	if secure_val == make_secure_val(val):
		return val
	
#password salt/hashing#		
def make_salt(length = 5):
	return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(name + pw + salt).hexdigest()
	return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
	salt = h.split(',')[0]
	return h == make_pw_hash(name, password, salt)

#signup form validation#
def valid_username(username):
	return username and USER_RE.match(username)

def valid_password(password):
	return password and PASS_RE.match(password)

def valid_email(email):
	return not email or EMAIL_RE.match(email)
	
#regular expressions#
PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
PASS_RE = re.compile(r"^.{3,20}$")
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")

#clean up permalinks#
def clean_link(permalink):
	return permalink[1:]