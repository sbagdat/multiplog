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

    def username(self):
        return self.user.username

    def link_to(self, action):
        base_link = "%s/comments/%s"
        base_link = base_link % (self.post.link_to('show'), self.key().id())
        if action is 'show':
            return base_link
        elif action is 'edit':
            return base_link + '/edit'
        elif action is 'delete':
            return base_link + 'delete'

    def render(self, user=None):
        return render_str("/comments/_comment.html", comment=self, user=user)
