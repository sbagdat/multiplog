import os
import random
import hashlib
import hmac
from string import letters
from google.appengine.ext import db



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

