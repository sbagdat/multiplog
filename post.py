from google.appengine.ext import db
from user import User
from comment import Comment
from helpers import render_str


class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created_at = db.DateTimeProperty(auto_now_add=True)
    comments_count = db.IntegerProperty(default=0)
    user_id = db.IntegerProperty(required=True)

    @classmethod
    def find_by_subject(cls, post_subject):
        post_subject = post_subject.replace('-', ' ')
        return Post.all().filter('subject =', post_subject).get()

    def render(self, user=None, truncated=False, commented=False):
        self._render_text = self.content.replace('\n', '<br>')
        if len(self._render_text) < 135:
            self._truncated_render_text = self._render_text
        else:
            text = self._render_text[:(self._render_text.find(' ', 130))+1]
            self._truncated_render_text = text + (
                "... <a href='/posts/%s'>more</a>" % self.linkified_subject())
        return render_str(
            "_post.html",
            post=self,
            user=user,
            truncated=truncated,
            commented=commented)

    def username(self):
        return User.find_by_id(self.user_id).user

    def comments(self):
        return Comment.all().filter('post_id =', self.key().id()).order('-created_at')

    def linkified_subject(self):
        return self.subject.replace(' ', '-')

    def unlinkified_subject(self):
        return self.subject.replace('-', ' ')
