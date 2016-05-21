import re
from google.appengine.ext import db
from crypto import Cryptographer
from helpers import users_key


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()

    # Used for making password hash before saving
    cryptographer = Cryptographer()

    @classmethod
    def find_by_id(cls, id):
        """Find a user by its id"""
        return User.get_by_id(id)

    @classmethod
    def find_by_username(cls, username):
        """Find a user by its username"""
        return User.all().filter('username =', username).get()

    @classmethod
    def save(cls, values):
        """
            If user data is valid, then save it to the database,
            otherwise return errors
        """
        valid, errors = User.is_valid_candidate(values)
        new_user = ""
        if valid:
            new_user = User(
                username=values['username'],
                password=User.cryptographer.password_hash(
                    values['username'],
                    values['password']),
                email=values['email'])
            try:
                new_user.put()
                return new_user
            except:
                raise
        else:
            return errors

    @staticmethod
    def regexp(key):
        return {
            'username': re.compile(r"^[a-zA-Z0-9_-]{3,20}$"),
            'password': re.compile(r"^.{3,20}$"),
            'email':    re.compile(r'^[\S]+@[\S]+\.[\S]+$')
        }[key]

    @staticmethod
    def is_valid_candidate(values):
        """Check user-entered values are valid to become a new user"""
        errors = {}
        username = values['username']
        password = values['password']
        password_confirmation = values['password_confirmation']
        email = values['email']

        # check username is invalid or already exists
        if not (username and User.regexp('username').match(username)):
            errors['username'] = 'invalid username'
        if User.find_by_username(username):
            errors['username'] = 'already exists'

        # check password is invalid or doesn't match with confirmation
        if not (password and User.regexp('password').match(password)):
            errors['password'] = 'invalid password'
        elif not password == password_confirmation:
            errors['password_confirmation'] = "passwords don't match"

        # check email is valid(empty email is also valid)
        if email and not User.regexp('email').match(email):
            errors['email'] = 'invalid email'

        # If errors found return them with a False value,
        # otherwise return True
        if errors:
            return (False, errors)
        else:
            return (True, {})

    def owner_of(self, thing):
        return thing.user.key() == self.key()
