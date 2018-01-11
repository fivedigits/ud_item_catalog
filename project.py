#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module contains code for a flask application serving
an item catalog. Login functionality is provided via Google's
OAuth2 API. Since oauth2client has recently been deprecated,
google-auth-oauthlib is used. This provides a server side flow.
The client authenticates with Google. Google sends the access
token to the server by a GET request to the redirect_uri
provided in the FLOW. There is a JSON API under /json which
can be queried for categories and items by supplying their
names. """

import os
import string
import json
import random
from flask import Flask, render_template, request, redirect,\
    url_for, session, make_response
from db_setup import Category, Item, SQLSession, User
from sqlalchemy.exc import IntegrityError
from google_auth_oauthlib.flow import Flow

# in production, https should be used
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'y'

APP = Flask(__name__)
# At every startup, compute a new secret key
APP.secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                         for x in range(32))


LOGIN_URL = 'http://localhost:8000/login'
USERINFO_URL = 'https://www.googleapis.com/userinfo/v2/me'
FLOW = Flow.from_client_secrets_file('client_secrets.json',
                                     scopes=['profile', 'email'],
                                     redirect_uri=LOGIN_URL)


@APP.route("/logout")
def logout():
    """This function logs the user out by removing his profile
       information from the session. This is sufficient because
       no access token is saved.
    """
    session.pop('userinfo', None)
    # no more steps necessary, because we don't keep the token around
    if 'target' not in session.keys():
        return redirect("/")
    return redirect(session['target'])


@APP.route("/login")
def login():
    """This function is called, when Google sends the access
       token during authentication. The token is immediately
       discarded, after the profile info of the user has been
       obtained. The login information is saved into the
       cryptographically signed session.

       Returns:
           A redirect to the page the user was visiting before
           authenticating, if a session cookie was sent,
           otherwise redirects to the root page.
    """
    if session['state'] != request.args['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    authorization_response = request.url
    FLOW.fetch_token(authorization_response=authorization_response)
    auth_session = FLOW.authorized_session()
    userinfo = auth_session.get(USERINFO_URL).json()
    session['userinfo'] = {
        'name':  userinfo['name'],
        'email': userinfo['email']}
    sqlsession = SQLSession()
    user = User(name=userinfo['name'], email=userinfo['email'])
    try:
        sqlsession.add(user)
        sqlsession.commit()
    except IntegrityError:
        # user already exists in DB
        pass
    if 'target' not in session.keys():
        return redirect("/")
    return redirect(session['target'])


@APP.route("/gconnect")
def gconnect():
    """Constructs an authorization_url for the user.
       An anti-forgery state token is passed as a parameter.

       Returns:
           A redirect to the authorization_url (Google).
    """
    session['state'] = new_state()
    # Google will return the state as a query parameter
    authorization_url, state = FLOW.authorization_url(state=session['state'])
    return redirect(authorization_url)


@APP.route("/")
def catalog():
    """Constructs the main view of the item catalog.

       Returns:
           A http response containing catalog.html.
    """
    session['target'] = "/"
    sqlsession = SQLSession()
    items = sqlsession.query(Item, Category)\
                      .join(Category).order_by(Item.create_date).limit(10)
    categories = sqlsession.query(Category).all()
    return render_template("catalog.html",
                           items=items,
                           categories=categories,
                           item_title="Latest Items")


@APP.route("/categories/<int:cat_id>")
def view_category(cat_id):
    """Constructs an html page displaying the category with
    cat_id. Returns it in an http response.

    Args:
        cat_id: The id of the requested category.

    Returns:
        An http response containing view_category.html.
    """
    session['target'] = url_for('view_category', cat_id=cat_id)
    sqlsession = SQLSession()
    category = sqlsession.query(Category).filter_by(id=cat_id).first()
    categories = sqlsession.query(Category).all()
    items = sqlsession.query(Item).filter_by(category_id=cat_id).all()
    return render_template("view_category.html",
                           category=category,
                           categories=categories,
                           items=items,
                           item_title=category.name + " Items")


@APP.route("/categories/new", methods=['GET', 'POST'])
def insert_category():
    """If the user is not logged in, redirects to Google
    for authentication. Otherwise inserts the new category
    into the database on a POST, silently failing if there
    already is a category with the same name. Returns
    a page with a form for a new category on a GET.

    Returns:
        A redirect to gconnect, if the user is not logged in.
        On GET returns a form to insert a new category.
        On POST redirects to the newly inserted category.
    """
    if 'userinfo' not in session.keys():
        session['target'] = url_for('insert_category')
        return redirect(url_for('gconnect'))
    if request.method == 'POST':
        try:
            sqlsession = SQLSession()
            creator_email = session['userinfo']['email']
            user = sqlsession.query(User)\
                             .filter_by(email=creator_email).first()
            category = Category(name=request.form['name'],
                                creator_id=user.id)
            sqlsession.add(category)
            sqlsession.commit()
        except IntegrityError:
            # if the user sends an alread existing name
            # it is safe to assume that the already
            # included copy is what he wanted
            pass
        return redirect("/")
    return render_template("new_category.html")


@APP.route("/items/<int:item_id>")
def view_item(item_id):
    """Constructs the page to view the item given by item_id.

        Args:
            item_id: The id of the requested item.

        Returns:
            An http response containing view_item.html.
    """
    session['target'] = url_for('view_item', item_id=item_id)
    sqlsession = SQLSession()
    item = sqlsession.query(Item, Category).join(Category)\
                                           .filter(Item.id == item_id).first()
    return render_template("view_item.html", item=item)


@APP.route("/items/new", methods=['GET', 'POST'])
def insert_item():
    """Constructs a form to insert a new item or inserts a
       new item into the db on a POST request. Redirects the
       user to gconnect if he is not logged in.

       Returns:
           A redirect to the newly created item on a POST.
           An http response containing new_item.html on GET.
           A redirect to gconnect, if the user is not logged in.
    """
    if 'userinfo' not in session.keys():
        session['target'] = url_for('insert_item')
        return redirect(url_for('gconnect'))
    if request.method == 'POST':
        creator_email = session['userinfo']['email']
        sqlsession = SQLSession()
        user = sqlsession.query(User).filter_by(email=creator_email).first()
        item = Item(name=request.form['name'],
                    description=request.form['description'],
                    category_id=int(request.form['category']),
                    creator_id=user.id)
        sqlsession.add(item)
        sqlsession.commit()
        return redirect("/")
    sqlsession = SQLSession()
    categories = sqlsession.query(Category).all()
    return render_template("new_item.html",
                           categories=categories)


@APP.route("/items/<int:item_id>/edit", methods=['GET', 'POST'])
def edit_item(item_id):
    """Constructs and pre-fills a form to edit the item given
       by item_id. On a POST, the item is updated.

       Args:
           item_id: The id of the item to be edited.

       Returns:
           A redirect to the edited item on POST.
           An http response containg edit_item.html on GET.
           A redirect to gconnect, if the user is not logged in.
    """
    if 'userinfo' not in session.keys():
        session['target'] = url_for('edit_item', item_id=item_id)
        return redirect(url_for('gconnect'))
    if request.method == 'POST':
        sqlsession = SQLSession()
        item = sqlsession.query(Item).filter_by(id=item_id).first()
        item.name = request.form['name']
        item.category_id = request.form['category']
        item.description = request.form['description']
        sqlsession.commit()
        return redirect(url_for('view_item', item_id=item_id))
    sqlsession = SQLSession()
    item = sqlsession.query(Item).filter_by(id=item_id).first()
    categories = sqlsession.query(Category).all()
    return render_template("edit_item.html",
                           item=item,
                           categories=categories)


@APP.route("/items/<int:item_id>/delete", methods=['GET', 'POST'])
def delete_item(item_id):
    """Constructs the page containing the delete form, or
       deletes the item given by item_id on a POST.

       Args:
           item_id: The id of the item to be deleted.

       Returns:
           A redirect to the root page on a POST.
           A redirect to gconnect, if the user is not logged in.
           An http response containing delete_item.html on GET.
    """
    if 'userinfo' not in session.keys():
        session['target'] = url_for('delete_item', item_id=item_id)
        return redirect(url_for('gconnect'))
    if request.method == 'POST':
        sqlsession = SQLSession()
        item = sqlsession.query(Item).filter_by(id=item_id).first()
        sqlsession.delete(item)
        sqlsession.commit()
        return redirect("/")
    sqlsession = SQLSession()
    item = sqlsession.query(Item, Category).join(Category)\
                                           .filter(Item.id == item_id).first()
    return render_template("delete_item.html", item=item)


@APP.route("/json")
def json_api():
    """This functions contains the json API for the app.
       Args can be passed as query parameters.

       Args:
           category: Name of the requested category.
           item: Name of the requested item(s).

       Returns:
           A JSON object containing the information about the
           category and all its items, if category is given.

           If item is given, returns a JSON object containing
           the list of all items which match the given name.

           A JSON object containing all 'categories' and all
           'items' in the database.
    """
    if 'category' in request.args:
        sqlsession = SQLSession()
        category = sqlsession.query(Category)\
                             .filter_by(name=request.args['category']).first()
        items = sqlsession.query(Item).filter_by(category_id=category.id)\
                                      .all()
        return json.dumps({'category_id': category.id,
                           'category_name': category.name,
                           'items': [item.serialize() for item in items]})
    elif 'item' in request.args:
        sqlsession = SQLSession()
        items = sqlsession.query(Item).filter_by(name=request.args['item'])\
                                      .all()
        return json.dumps([item.serialize() for item in items])
    sqlsession = SQLSession()
    categories = sqlsession.query(Category).all()
    items = sqlsession.query(Item).all()
    return json.dumps(
        {'categories': [cat.serialize() for cat in categories],
         'items': [item.serialize() for item in items]})


def new_state():
    """Computes a random string to be used as state or secret key.

       Returns:
           A random string of length 32 containing letters and digits.
    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(32))


if __name__ == '__main__':
    APP.debug = True
    APP.run(host='0.0.0.0', port=8000)
