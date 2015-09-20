from flask.ext.sqlalchemy import SQLAlchemy
from flask import Markup

import calendar

from datetime import datetime, timedelta

class Model():
    def __init__(self, app):
        self.db = SQLAlchemy(app)
        db = self.db

        class Category(self.db.Model):
            __tablename__ = 'category'

            id = db.Column(db.Integer, primary_key=True)
            title = db.Column(db.String)

            def __init__(self, title):
                self.title = title
        self.Category = Category

        class Review(self.db.Model):
            __tablename__ = 'review'

            id = db.Column(db.Integer, primary_key=True)
            text = db.Column(db.String)
            rating = db.Column(db.Integer)
            category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
            category = db.relationship('Category', backref=db.backref('Review', lazy='dynamic'))
            user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
            user = db.relationship('User', backref=db.backref('Review', lazy='dynamic'))

            def __init__(self, text, rating, category, user):
                self.text = text
                self.rating = rating
                self.category = category
                self.user = user
        self.Review = Review

        class User(self.db.Model):
            __tablename__ = 'users'

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(80))
            email = db.Column(db.String(120), unique=True)
            password = db.Column(db.String)
            authenticated = db.Column(db.Boolean())
            is_admin = db.Column(db.Boolean())
            is_anonymous = False

            def __init__(self, name, email, is_admin=False):
                self.name = name
                self.email = email
                self.authenticated = False
                self.is_admin = is_admin

            def __str__(self):
                return "User: {}".format((self.id, self.name, self.email, self.password, self.authenticated, self.is_admin))

            def is_authenticated(self) :
                return self.authenticated

            def is_active(self) :
                return self.is_authenticated()

            def get_id(self) :
                return self.email

            def get_id_num(self):
                return self.id
        self.User = User
