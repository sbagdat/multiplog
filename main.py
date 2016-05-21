import webapp2
from google.appengine.ext import db
from crypto import Cryptographer
from helpers import render_str
from user import User
from post import Post


class ApplicationHandler(webapp2.RequestHandler):
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        user_id = self.read_secure_cookie('user_id')
        # Attach current user to every handler
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


class SignUpHandler(ApplicationHandler):
    def get(self):
        # Any user logged in, then redirect to homepage, else render the form
        if not self.user:
            self.render('signup.html', values=None, errors=None)
        else:
            self.redirect('/')

    def post(self):
        values = {
            'username': self.request.get('username').strip().lower(),
            'password': self.request.get('password'),
            'password_confirmation': self.request.get('password_confirmation'),
            'email': self.request.get('email').strip().lower()}

        # If user is successfully saved to database, it returns the user,
        # otherwise it returns errors occured during validation process
        new_user = errors = User.save(values)
        if new_user.__class__ == User:
            # User successfully created_at
            self.login(new_user.key().id())
            self.redirect('/')
        else:
            # User information has some errors
            self.render('signup.html', values=values, errors=errors)


class SignInHandler(ApplicationHandler):
    def get(self):
        # Any user logged in, then redirect to homepage, else render the form
        if not self.user:
            self.render('login.html')
        else:
            self.redirect('/')

    def post(self):
        username = self.request.get('username').strip().lower()
        password = self.request.get('password')
        # If user/password matches redirect to homepage,
        # otherwise re-render the form with errors
        if not (username and password):
            self.render(
                'login.html', error='Enter both username and password!')
        else:
            user = User.find_by_username(username)
            if user and Cryptographer().valid_password(
                    username, password, user.password):
                self.login(user.key().id())
                self.redirect('/')
            else:
                self.render(
                    'login.html', error='Wrong username and/or  password!')


class SignOutHandler(ApplicationHandler):
    def get(self):
        self.logout()
        self.redirect('/')


class HomeHandler(ApplicationHandler):
    def get(self):
        posts = Post.all().order('-created_at')
        self.render('front.html', posts=posts)


app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/signup', SignUpHandler),
    ('/login', SignInHandler),
    ('/logout', SignOutHandler),
    ('/posts/new', NewPostHandler),
], debug=True)
