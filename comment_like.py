from google.appengine.ext import db
from comment import Comment
from user import User


class CommentLike(db.Model):
    comment = db.ReferenceProperty(Comment)
    user = db.ReferenceProperty(User)
