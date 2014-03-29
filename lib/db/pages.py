##### Pages ###
from google.appengine.ext import db
from lib import utils

#set parent#
def pages_key(group = 'default'):
	return db.Key.from_path('users', group)

#page entity#
class Page(db.Model):
	content = db.TextProperty(required = True)
	author = db.StringProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)
	
	@staticmethod
	def parent_key(path):
		return db.Key.from_path('/root' + path, 'pages')
	
	@classmethod
	def by_path(cls, path):
		q = cls.all()
		q.ancestor(cls.parent_key(path))
		q.order("-created")
		return q
	
	@classmethod
	def by_id(cls, page_id, path):
		return cls.get_by_id(page_id, cls.parent_key(path))
	
	def render(self):
		self._render_text = self.content.replace('\n', '<br>')
		return utils.render_str("post.html", p = self)