from google.appengine.ext import db
from user import User
from post import Post


class Comment(db.Model):
    content = db.TextProperty(required=True)
    post = db.ReferenceProperty(Post)
    user = db.ReferenceProperty(User)
    created_at = db.DateTimeProperty(auto_now_add=True)

    def username(self):
        return self.user.username
