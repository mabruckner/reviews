from flask import *
from logging.handlers import RotatingFileHandler

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.assets import Environment, Bundle
from htmlmin import minify
from flask.ext.login import LoginManager,login_user,logout_user, current_user, login_required
from flask_wtf import Form
from wtforms import StringField, PasswordField, TextField, TextAreaField
from wtforms import validators
from passlib.hash import pbkdf2_sha256

import logging

from model import Model

import json

import os
import platform

app = Flask(__name__)
loginmanager = LoginManager()
loginmanager.init_app(app)
# https://flask-login.readthedocs.org/en/latest/
loginmanager.login_view = '/signin'

if platform.system().startswith('Win'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\temp\\cosmicac.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/cosmicac.db'

app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

UPLOAD_FOLDER = "/tmp/cosmicac-pics"
if platform.system().startswith('Win'):
    UPLOAD_FOLDER = "C:\\temp\\cosmicac-pics"

assets = Environment(app)
assets.url_expire = False

css = Bundle('css/bootstrap.css', 'css/main.css', filters="cssmin", output='css/gen/packed.css')
assets.register('css_all', css)

model = Model(app)
db = model.db

## Authentication
class LoginForm(Form):
    email = StringField('email', validators=[validators.DataRequired()])
    password = PasswordField('password', validators=[validators.DataRequired()])

class SignupForm(Form):
    name = StringField('name', validators=[validators.DataRequired()])
    email = StringField('email', validators=[validators.DataRequired()])
    password = PasswordField('password', validators=[validators.DataRequired()])
    repeatpassword = PasswordField('repeatpassword', validators=[validators.DataRequired()])

class EditUserForm(Form):
    name = TextField('name')
    email = TextField('email')
    password = PasswordField('password', [
       validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat password')

def create_user(name, email, password, is_admin=False):
    newuser = model.User(name, email, is_admin)
    newuser.password = pbkdf2_sha256.encrypt(password)
    db.session.add(newuser)
    db.session.commit()
    return newuser

@loginmanager.user_loader
def load_user(email):
    users = model.User.query.filter_by(email=email)
    return users.first()

@app.route('/authenticate', methods=['GET','POST'])
def authenticate():
    form = LoginForm()
    if form.validate_on_submit():
        users = model.User.query.filter_by(email=form.email.data)
        user = users.first()
        if user != None :
            if pbkdf2_sha256.verify(request.form["password"], user.password) :
                user.authenticated = True
                db.session.commit()
                login_user(user)
    return redirect(request.form["redirect"])

@app.route('/signin', methods=['GET','POST'])
def login():
    form = LoginForm()
    if request.method == 'GET' :
        return render_template("signin.html",form = form,error = "")
    error = "some fields were empty"
    if form.validate_on_submit():
        user = model.User.query.filter_by(email=request.form["email"]).first()
        if user != None :
            if pbkdf2_sha256.verify(request.form["password"],user.password) :
                user.authenticated = True
                db.session.commit()
                login_user(user)
                return redirect("/")
        error = "Incorrect Email or Password"
    return render_template("signin.html",form = form,error = error);

@app.route('/signup', methods=['GET','POST'])
def signup():
    form = SignupForm()
    if request.method == 'GET' :
        return render_template("signup.html",form = form,error="")
    error = "some fields were empty"
    if form.validate_on_submit():
        error = "some fields were empty"

        find_user = model.User.query.filter_by(email=request.form['email']).first()
        if find_user:
            error = "Account already exists"
        elif request.form["password"] == request.form["repeatpassword"]:
            user = create_user(request.form["name"], request.form["email"], request.form["password"])
            user.authenticated = True
            db.session.commit()
            login_user(user)
            return redirect("/")
        else:
            error = "passwords did not match"
    return render_template("signup.html",form = form,error=error)

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(request.args.get("redirect"))

@app.route('/signout')
@login_required
def signout():
    logout_user()
    return redirect('/signin')

@app.route('/', methods=['GET'])
def index():
    print(current_user.is_anonymous)
    if current_user.is_anonymous:
        return redirect("/signin")
    return render_template('index.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == "POST":
        form = EditUserForm()
        if not form.validate_on_submit():
            for error in form.errors:
                flash("Error for {}".format(error), "danger")
            return render_template("profile.html", form=form)

        current_user.name = form.name.data
        current_user.email = form.email.data
        if form.password.data.strip() != "":
            current_user.password = pbkdf2_sha256.encrypt(form.password.data)
        db.session.commit()
        flash("User updated", "success")
    return render_template('profile.html', form=EditUserForm())

@app.route('/admin', methods=['GET'])
@login_required
def admin():
    if current_user.is_admin:
        users = model.User.query.all()
        return render_template('admin.html', users=users)
    # If the user isn't an admin, return them to /
    return abort(403)

@app.route('/add/user', methods=['GET', 'POST'])
@login_required
def user_add():
    form = EditUserForm()
    if current_user.is_admin:
        if request.method == "POST":
            if not form.validate_on_submit():
                for error in form.errors:
                    flash("Error for {}".format(error), "danger")
                return render_template("add/user.html", form=form)

            user = model.User(form.name.data, form.email.data)
            user.password = pbkdf2_sha256.encrypt(form.password.data)

            db.session.add(user)
            db.session.commit()
            flash("User added", "success")
            return redirect("/admin")
        return render_template("add/user.html", form=EditUserForm())
    abort(403)

@app.route('/edit/user/<user_id>', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    form = EditUserForm()
    if current_user.is_admin:
        user = model.User.query.filter_by(id=user_id).first()
        if request.method == "POST":
            if not form.validate_on_submit():
                for error in form.errors:
                    flash("Error for {}".format(error), "danger")
                return render_template("add/user.html", form=form)

            user.name = form.name.data
            user.email = form.email.data
            user.password = pbkdf2_sha256.encrypt(form.password.data)

            db.session.commit()
            flash("User edited", "success")
            return redirect("/admin")
        return render_template("edit/user.html", form=EditUserForm(), user=user)
    abort(403)

@app.route('/delete/user/<user_id>', methods=['GET'])
@login_required
def user_delete(user_id):
    if current_user.is_admin:
        user = model.User.query.filter_by(id=user_id)
        flash("User {} deleted".format(user.first().name), "success")
        user.delete()
        db.session.commit()
        return redirect("/admin")
    abort(403)

@app.route('/js/<remainder>', methods=['GET'])
@app.route('/img/<remainder>', methods=['GET'])
@login_required
def get_static(remainder):
    return send_from_directory(app.static_folder,request.path[1:])

app.secret_key = "Secret"


## Example Logging
if __name__ == "__main__":
    handler = RotatingFileHandler('log.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    app.run(host="0.0.0.0")
