from google.appengine.ext import db
from user import User
from post import Post
from helpers import render_str


class Comment(db.Model):
    content = db.TextProperty(required=True)
    post = db.ReferenceProperty(Post)
    user = db.ReferenceProperty(User)
    created_at = db.DateTimeProperty(auto_now_add=True)

    @db.ComputedProperty
    def ctime(self):
        return self.created_at.strftime("%b %d, %Y")

    @classmethod
    def find_by_id(cls, id):
        return Comment.get_by_id(int(id))

    def username(self):
        return self.user.username

    def link_to(self, action):
        base_link = "/comments/%s" % self.key().id()
        if action is 'edit':
            return base_link + '/edit'
        elif action is 'delete':
            return base_link + '/delete'

    def render(self, user=None):
        return render_str("/comments/_comment.html", comment=self, user=user)
