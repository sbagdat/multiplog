from google.appengine.ext import db
from post import Post
from user import User


class PostLike(db.Model):
    post = db.ReferenceProperty(Post)
    user = db.ReferenceProperty(User)
