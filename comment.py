from google.appengine.ext import db
from user import User


class Comment(db.Model):
    content = db.TextProperty(required=True)
    user_id = db.IntegerProperty(required=True)
    post_id = db.IntegerProperty(required=True)
    created_at = db.DateTimeProperty(auto_now_add=True)

    def username(self):
        user = User.find_by_id(self.user_id)
        return user.user
