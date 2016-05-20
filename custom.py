import os
import re
import random
import hashlib
import hmac
from string import letters
from google.appengine.ext import db
from helpers import users_key

class User(db.Model):
    user = db.StringProperty(required=True)
    pswd = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def find_by_id(cls, id):
        return User.get_by_id(id, parent = users_key())

    @classmethod
    def find_by_username(cls, username):
        return User.all().filter('user =', username).get()

class Cryptographer():
    def __init__(self):
        self.secret = self.read_secret_file()
        self.salt = self.make_salt()

    @staticmethod
    def read_secret_file():
        # Put secret to another file, so able to don't checkout it to vcs
        file_dir = os.path.dirname(os.path.realpath('__file__'))
        secret_file = open(os.path.join(file_dir, 'secret.txt'))
        secret = secret_file.read()
        secret_file.close()
        return secret

    def make_secure_val(self, val):
        return '%s|%s' % (val, hmac.new(self.secret, val).hexdigest())

    def check_secure_val(self, secure_val):
        val = secure_val.split('|')[0]
        if secure_val == self.make_secure_val(val):
            return val

    def make_salt(self, length = 5):
        return ''.join(random.choice(letters) for x in xrange(length))

    def make_pw_hash(self, name, pw):
        h = hashlib.sha256(name + pw + self.salt).hexdigest()
        return '%s,%s' % (self.salt, h)

    def valid_pw(self, name, password, h):
        self.salt = h.split(',')[0]
        return h == self.make_pw_hash(name, password)

class BlogUser():
    def __init__(self, values):
        self.initialize_variables(values)
        self.cryptographer = Cryptographer()
        self.check_for_errors()

    def initialize_variables(self, values):
        self.id = None
        self.username = values['username']
        self.password = values['password']
        self.password_confirmation = values['password_confirmation']
        self.email = values['email']
        self.errors = {}

    def check_for_errors(self):
        # clean old errors
        self.errors = {}
        if not self.valid_username():
            self.errors['username'] = 'not valid username'
        if not self.valid_password():
            self.errors['password'] = 'not valid password.'
        elif not self.match_passwords():
            self.errors['password_confirmation'] = "passwords didn't match"
        if not self.valid_email():
            self.errors['email'] = 'not valid email.'
        return self.errors

    def have_errors(self):
        return self.errors != []

    def valid_username(self):
        return self.username and self.regexp('username').match(self.username)

    def valid_password(self):
        return self.password and self.regexp('password').match(self.password)

    def match_passwords(self):
        return self.password == self.password_confirmation

    def valid_email(self):
        return not self.email or self.regexp('email').match(self.email)

    def save(self):
        if self.errors:
            return False
        elif self.user_exist():
            return False
        else:
            new_user = User(parent=users_key(),
                            user=self.username,
                            pswd=self.password_hash(),
                            email=self.email)
            new_user.put()
            self.id = new_user.key().id()
            return True

    @staticmethod
    def regexp(key):
        return {
            'username': re.compile(r"^[a-zA-Z0-9_-]{3,20}$"),
            'password': re.compile(r"^.{3,20}$"),
            'email':    re.compile(r'^[\S]+@[\S]+\.[\S]+$')
        }[key]

    def user_exist(self):
        user = User.all().filter('user =', self.username).get()
        if user:
            self.errors['exist'] = 'User already exist, try different username'
            return True
        else:
            return False

    def password_hash(self):
        return self.cryptographer.make_pw_hash(self.username, self.password)
