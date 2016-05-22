from google.appengine.ext import db
from user import User
from helpers import render_str


class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created_at = db.DateTimeProperty(auto_now_add=True)
    user = db.ReferenceProperty(User)

    @db.ComputedProperty
    def linkified_subject(self):
        return self.subject.replace(' ', '-')

    @db.ComputedProperty
    def ctime(self):
        return self.created_at.strftime("%b %d, %Y")

    @classmethod
    def find_by_subject(cls, post_subject):
        post_subject = post_subject.replace('-', ' ')
        return Post.all().filter('subject =', post_subject).get()

    def render_text(self):
        return self.content.replace('\n', '<br>')

    def truncated_text(self):
        if len(self.render_text()) > 135:
            text = self.render_text()
            clipped_text = text[:text.find(' ', 130)+1]
            more_link = "<a href='/posts/%s'>more</a>" % self.linkified_subject
            return clipped_text + '...' + more_link
        else:
            return self.render_text()

    def render(self, user=None, truncated=False, commented=False, errors=None):
        return render_str(
            "/posts/_post.html",
            post=self,
            user=user,
            truncated=truncated,
            commented=commented,
            errors=errors)

    def username(self):
        return self.user.username

    def link_to(self, action):
        base_link = "/posts/%s" % self.linkified_subject
        if action is 'show':
            return base_link
        elif action is 'edit':
            return base_link + '/edit'
        elif action is 'delete':
            return base_link + '/delete'
        elif action is 'like':
            return base_link + '/like'
        elif action is 'dislike':
            return base_link + '/dislike'
