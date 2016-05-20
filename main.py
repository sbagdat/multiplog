import webapp2
from google.appengine.ext import db
from crypto import *
from helpers import render_str, blog_key
from user import User, BlogUser
from post import Post
from comment import Comment


class Handler(webapp2.RequestHandler):
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        user_id = self.read_secure_cookie('user_id')
        self.user = user_id and User.find_by_id(int(user_id))

    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = Cryptographer().make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and Cryptographer().check_secure_val(cookie_val)

    def login(self, user_id):
        self.set_secure_cookie('user_id', str(user_id))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')


class SignUpHandler(Handler):
    def render_signup_form(self, values={}, errors={}):
        self.render('signup.html', values=values, errors=errors)

    def get(self):
        if not self.user:
            self.render_signup_form()
        else:
            self.redirect('/')

    def post(self):
        values = {
          'username': (self.request.get('user') or ''),
          'password': (self.request.get('pswd') or ''),
          'password_confirmation': (self.request.get('pswd_verify') or ''),
          'email': (self.request.get('email') or '')}

        new_user = BlogUser(values)
        if new_user.save():
            self.login(new_user.id)
            self.redirect('/')
        else:
            self.render_signup_form(values=values, errors=new_user.errors)


class LogInHandler(Handler):
    def get(self):
        if not self.user:
            self.render('login.html')
        else:
            self.redirect('/')

    def post(self):
        username = self.request.get('user')
        password = self.request.get('pswd')
        if not (username and password):
            self.render(
                'login.html',
                error='Enter both username and password!')
        else:
            user = User.find_by_username(username)
            if (user and Cryptographer().valid_pw(username,
                                                  password,
                                                  user.pswd)):
                self.login(user.key().id())
                self.redirect('/')
            else:
                self.render(
                    'login.html',
                    error='Wrong username and/or  password!')


class LogOutHandler(Handler):
    def get(self):
        self.logout()
        self.redirect('/')


class HomeHandler(Handler):
    def get(self):
        posts = Post.all().order('-created_at')
        self.render('front.html', posts=posts)


class NewPostHandler(Handler):
    def get(self):
        if self.user:
            self.render("newpost.html", values="")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/')

        values = {
            'subject': self.request.get('subject'),
            'content': self.request.get('content')}

        if values['subject'] and values['content']:
            post = Post(
                parent=blog_key(),
                subject=values['subject'],
                content=values['content'],
                user_id=self.user.key().id())
            post.put()
            self.redirect('/posts/%s' % post.linkified_subject())
        else:
            error = "we need subject and content!"
            self.render("newpost.html", values=values, error=error)


class ShowPostHandler(Handler):
    def get(self, post_subject):
        post = Post.find_by_subject(post_subject)

        if not post:
            self.error(404)
            return

        self.render("post.html", post=post)


class EditPostHandler(Handler):
    def get(self, post_subject):
        if not self.user:
            self.redirect("/login")

        post = Post.find_by_subject(post_subject)
        # If user is not owner of the post, redirect with an error
        # TODO: Show an error
        if not self.user.owner_of(post):
            self.redirect("/")
        else:
            values = {
                'subject': post.subject,
                'content': post.content
            }
        self.render("editpost.html", post=post, values=values)

    def post(self, post_subject):
        if not self.user:
            self.redirect('/')
        post = Post.find_by_subject(post_subject)
        # If user is not owner of the post, redirect with an error
        # TODO: Show an error
        if not self.user.owner_of(post):
            self.redirect("/")
        else:
            values = {
                'subject': self.request.get('subject'),
                'content': self.request.get('content')}

            if values['subject'] and values['content']:
                values = {
                    'subject': self.request.get('subject'),
                    'content': self.request.get('content')}

                post.subject = values['subject']
                post.content = values['content']
                post.put()
                self.redirect('/posts/%s' % post.linkified_subject())
            else:
                error = "we need subject and content!"
                self.render("editpost.html", values=values, error=error)


class DeletePostHandler(Handler):
    def post(self, post_subject):
        if not self.user:
            self.redirect("/login")

        post_to_delete = Post.find_by_subject(post_subject)
        if not self.user.owner_of(post_to_delete):
            self.render("HomeHandler")
        else:
            post_to_delete.delete()
            self.redirect('/')


class NewCommentHandler(Handler):
    def post(self, post_subject):
        if not self.user:
            self.redirect('/')

        post_to_comment = Post.find_by_subject(post_subject)
        content = self.request.get('content')

        if content:
            comment = Comment(
                parent=blog_key(),
                content=content,
                post_id=post_to_comment.key().id(),
                user_id=self.user.key().id())
            comment.put()

            post_to_comment.comments_count += 1
            post_to_comment.put()

            self.redirect('/posts/%s' % post_to_comment.linkified_subject())
        else:
            self.render(
                "post.html",
                post=post_to_comment)


app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/signup', SignUpHandler),
    ('/login', LogInHandler),
    ('/logout', LogOutHandler),
    ('/newpost', NewPostHandler),
    ('/posts/([^/]+)', ShowPostHandler),
    ('/posts/([^/]+)/edit', EditPostHandler),
    ('/posts/([^/]+)/delete', DeletePostHandler),
    ('/posts/([^/]+)/comments/new', NewCommentHandler)
], debug=True)
