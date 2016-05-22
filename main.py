import webapp2
from google.appengine.ext import db
from crypto import Cryptographer
from user import User
from post import Post
from comment import Comment
from post_like import PostLike
from comment_like import CommentLike
from helpers import render_str


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


class NewPostHandler(ApplicationHandler):
    def get(self):
        # If any user does not logged in redirect to homepage,
        # otherwise render the new post form
        if self.user:
            self.render("/posts/new.html", values=None, errors=None)
        else:
            self.redirect("/login")

    def post(self):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect('/')

        values = {
            'subject': self.request.get('subject').strip(),
            'content': self.request.get('content').strip()}

        if values['subject'] and values['content']:
            post = Post(
                subject=values['subject'],
                content=values['content'],
                user=self.user)
            post.put()
            self.redirect(post.link_to('show'))
        else:
            errors = {}
            if not values['subject']:
                errors['subject'] = "can't be blank"
            if not values['content']:
                errors['content'] = "can't be blank"
            self.render("/posts/new.html", values=values, errors=errors)


class ShowPostHandler(ApplicationHandler):
    def get(self, post_subject):
        post = Post.find_by_subject(post_subject)

        if not post:
            self.error(404)
            return self.render('404.html')

        self.render("/posts/post.html", post=post, errors=None)

    def post(self, post_subject):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect('/')

        # Post page contains a form to post comments,
        # so a post request comes, lets put that comment into database
        post_to_comment = Post.find_by_subject(post_subject)
        # If post couldn't find redirect 404 page
        if not post_to_comment:
            self.error(404)
            return self.render('404.html')

        content = self.request.get('content').strip()

        if content:
            comment = Comment(
                content=content,
                post=post_to_comment,
                user=self.user)
            comment.put()
            self.redirect(post_to_comment.link_to('show'))
        else:
            errors = {'content': "can't be blank"}
            self.render(
                "/posts/post.html", post=post_to_comment,
                errors=errors)


class EditPostHandler(ApplicationHandler):
    def get(self, post_subject):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect("/login")

        post_to_update = Post.find_by_subject(post_subject)
        # If post couldn't find redirect 404 page
        if not post_to_update:
            self.error(404)
            return self.render('404.html')
        # If user is not owner of the post, redirect with an error
        if not self.user.owner_of(post_to_update):
            self.redirect("/")
        else:
            values = {
                'subject': post_to_update.subject,
                'content': post_to_update.content}

        self.render(
            "/posts/edit.html", post=post_to_update,
            values=values, errors=None)

    def post(self, post_subject):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect('/')
        post_to_update = Post.find_by_subject(post_subject)
        # If post couldn't find redirect 404 page
        if not post_to_update:
            self.error(404)
            return self.render('404.html')
        # If user is not owner of the post, redirect with an error
        # TODO: Show an error
        if not self.user.owner_of(post_to_update):
            self.redirect("/")
        else:
            values = {
                'subject': self.request.get('subject'),
                'content': self.request.get('content')}

            if values['subject'] and values['content']:
                values = {
                    'subject': self.request.get('subject').strip(),
                    'content': self.request.get('content').strip()}

                post_to_update.subject = values['subject']
                post_to_update.content = values['content']
                post_to_update.put()
                self.redirect(post_to_update.link_to('show'))
            else:
                errors = {}
                if not values['subject']:
                    errors['subject'] = "can't be blank"
                if not values['content']:
                    errors['content'] = "can't be blank"
                self.render("/posts/edit.html", values=values, errors=errors)


class DeletePostHandler(ApplicationHandler):
    # not available for get requests

    def post(self, post_subject):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect("/login")

        post_to_delete = Post.find_by_subject(post_subject)
        # If post couldn't find redirect 404 page
        if not post_to_delete:
            self.error(404)
            return self.render('404.html')
        if not self.user.owner_of(post_to_delete):
            self.redirect("/")
        else:
            # delete post likes
            for like in post_to_delete.postlike_set:
                like.delete()
            # delete comment and comment likes
            for comment in post_to_delete.comment_set:
                for like in comment.commentlike_set:
                    like.delete()
                comment.delete()
            # finally delete the post's itself
            post_to_delete.delete()

            self.redirect('/')


class EditCommentHandler(ApplicationHandler):
    def get(self, comment_id):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect("/login")

        comment_to_update = Comment.find_by_id(comment_id)
        if not comment_to_update:
            self.error(404)
            return self.render('404.html')
        if not self.user.owner_of(comment_to_update):
            self.redirect("/")

        values = {'content': comment_to_update.content}
        self.render(
            "/comments/edit.html", comment=comment_to_update,
            values=values, errors=None)

    def post(self, comment_id):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect("/login")

        comment_to_update = Comment.find_by_id(comment_id)
        if not comment_to_update:
            self.error(404)
            return self.render('404.html')
        if not self.user.owner_of(comment_to_update):
            self.redirect("/")

        values = {'content': self.request.get('content').strip()}
        if values['content']:
            comment_to_update.content = values['content']
            comment_to_update.put()
            self.redirect(comment_to_update.post.link_to('show'))


class DeleteCommentHandler(ApplicationHandler):
    # not available for get requests

    def post(self, comment_id):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect("/login")

        comment_to_delete = Comment.find_by_id(comment_id)
        if not comment_to_delete:
            self.error(404)
            return self.render('404.html')
        if not self.user.owner_of(comment_to_delete):
            self.redirect("/")

        # Save post to use after delete
        parent_post = comment_to_delete.post

        # delete comment likes before
        for like in comment_to_delete.commentlike_set:
            like.delete()
        # then delete the comment
        comment_to_delete.delete()
        self.redirect(parent_post.link_to('show'))


class LikePostHandler(ApplicationHandler):
    def post(self, post_subject):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect("/login")

        post_to_like = Post.find_by_subject(post_subject)
        # If post couldn't find redirect 404 page
        if not post_to_like:
            self.error(404)
            return self.render('404.html')
        # If user is owner of the post, redirect with an error
        if self.user.owner_of(post_to_like):
            self.redirect("/")
        elif self.user.liked_post_before(post_to_like):
            self.redirect("/")
        else:
            new_like = PostLike(post=post_to_like, user=self.user)
            new_like.put()
        self.redirect('/')


class DislikePostHandler(ApplicationHandler):
    def post(self, post_subject):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect("/login")

        post_to_dislike = Post.find_by_subject(post_subject)
        # If post couldn't find redirect 404 page
        if not post_to_dislike:
            self.error(404)
            return self.render('404.html')

        if not self.user.liked_post_before(post_to_dislike):
            self.redirect("/")
        else:
            for like in post_to_dislike.postlike_set:
                if like.user.key() == self.user.key():
                    like.delete()
                    break
        self.redirect('/')


class LikeCommentHandler(ApplicationHandler):
    def post(self, comment_id):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect("/login")

        comment_to_like = Comment.find_by_id(comment_id)
        # If comment couldn't find redirect 404 page
        if not comment_to_like:
            self.error(404)
            return self.render('404.html')
        # If user is owner of the comment, redirect with an error
        if self.user.owner_of(comment_to_like):
            self.redirect("/")
        # If user is liked this post before, redirect with an error
        elif self.user.liked_comment_before(comment_to_like):
            self.redirect(comment_to_like.post.link_to('show'))
        else:
            new_like = CommentLike(comment=comment_to_like, user=self.user)
            new_like.put()
        self.redirect(comment_to_like.post.link_to('show'))


class DislikeCommentHandler(ApplicationHandler):
    def post(self, comment_id):
        # If any user does not logged in redirect to homepage
        if not self.user:
            self.redirect("/login")

        comment_to_dislike = Comment.find_by_id(comment_id)
        # If comment couldn't find redirect 404 page
        if not comment_to_dislike:
            self.error(404)
            return self.render('404.html')

        if not self.user.liked_comment_before(comment_to_dislike):
            self.redirect(comment_to_dislike.post.link_to('show'))
        else:
            for like in comment_to_dislike.commentlike_set:
                if like.user.key() == self.user.key():
                    like.delete()
                    break
        self.redirect(comment_to_dislike.post.link_to('show'))

app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/signup', SignUpHandler),
    ('/login', SignInHandler),
    ('/logout', SignOutHandler),
    ('/posts/new', NewPostHandler),
    ('/posts/([^/]+)', ShowPostHandler),
    ('/posts/([^/]+)/edit', EditPostHandler),
    ('/posts/([^/]+)/delete', DeletePostHandler),
    ('/posts/([^/]+)/like', LikePostHandler),
    ('/posts/([^/]+)/dislike', DislikePostHandler),
    ('/comments/([0-9]+)/edit', EditCommentHandler),
    ('/comments/([0-9]+)/delete', DeleteCommentHandler),
    ('/comments/([0-9]+)/like', LikeCommentHandler),
    ('/comments/([0-9]+)/dislike', DislikeCommentHandler)
], debug=True)
