from google.appengine.ext import db
from user import User
from helpers import render_str


class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created_at = db.DateTimeProperty(auto_now_add=True)
    user_id = db.IntegerProperty(required=True)

    @classmethod
    def find_by_subject(cls, post_subject):
        post_subject = post_subject.replace('-', ' ')
        return Post.all().filter('subject =', post_subject).get()

        self._render_text = self.content.replace('\n', '<br>')
        return render_str("_post.html", post=self, user=user)

    def username(self):
        return User.find_by_id(self.user_id).user

    def linkified_subject(self):
        return self.subject.replace(' ', '-')

    def unlinkified_subject(self):
        return self.subject.replace('-', ' ')
