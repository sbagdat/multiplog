import os
import re
import random
import hashlib
import hmac
from string import letters
from google.appengine.ext import db

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

class User(db.Model):
    user = db.StringProperty(required=True)
    pswd = db.StringProperty(required=True)
    email = db.StringProperty()

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

class BlogUser():
    def __init__(self, username, password, password_confirmation, email=''):
        self.initialize_variables(username, password, password_confirmation, email)
        self.cryptographer = Cryptographer()
        self.check_for_errors()

    def initialize_variables(self, username, password, password_confirmation, email):
        self.id = None
        self.username = username
        self.password = password
        self.password_confirmation = password_confirmation
        self.email = email
        self.errors = []

    def check_for_errors(self):
        # clean old errors
        self.errors = []
        # if any errors found, add the to the end of errors list
        if not self.valid_username():
            self.errors.append("That's not a valid username.")
        if not self.valid_password():
            self.errors.append("That's not a valid password.")
        elif not self.match_passwords():
            self.errors.append("Your passwords didn't match.")
        if not self.valid_email():
            if self.email != '':
                self.errors.append("That's not a valid email.")
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
        return self.email and self.regexp('password').match(self.email)

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
            errors = ['User already exist!']
            return True
        else:
            return False

    def password_hash(self):
        return self.cryptographer.make_pw_hash(self.username, self.password)
