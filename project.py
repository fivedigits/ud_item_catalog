import os

# in production, https should be used
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'y'

from flask import Flask, render_template, request, redirect, url_for, session, make_response
import json
import random
import string
from db_setup import Base, Category, Item, SQLSession, User
from sqlalchemy.exc import IntegrityError
from google_auth_oauthlib.flow import Flow


app = Flask(__name__)
# At every startup, compute a new secret key
app.secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))


USERINFO_URL = 'https://www.googleapis.com/userinfo/v2/me'
FLOW = Flow.from_client_secrets_file('client_secrets.json',
                                     scopes = ['profile', 'email'],
                                     redirect_uri = 'http://localhost:8000/login')

@app.route("/logout")
def logout():
    session.pop('userinfo', None)
    # no more steps necessary, because we don't keep the token around
    if not 'target' in session.keys():
        return redirect("/")
    else:
        return redirect(session['target'])
    
@app.route("/login")
def login():
    if session['state'] != request.args['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    authorization_response = request.url
    FLOW.fetch_token(authorization_response = authorization_response)
    auth_session = FLOW.authorized_session()
    userinfo = auth_session.get(USERINFO_URL).json()
    session['userinfo'] = {
        'name' :  userinfo['name'],
        'email' : userinfo['email']}
    sqlsession = SQLSession()
    user = User(name = userinfo['name'], email = userinfo['email'])
    try:
        sqlsession.add(user)
        sqlsession.commit()
    except IntegrityError:
        # user already exists in DB
        pass
    if not 'target' in session.keys():
        return redirect("/")
    else:
        return redirect(session['target'])

@app.route("/gconnect")
def gconnect():
    session['state'] = newState()
    # Google will return the state as a query parameter
    authorization_url, state = FLOW.authorization_url(state = session['state'])
    return redirect(authorization_url)
                                                                   
@app.route("/")
def catalog():
    sqlsession = SQLSession()
    items = sqlsession.query(Item, Category).join(Category).order_by(Item.create_date).limit(10)
    categories = sqlsession.query(Category).all()
    return render_template("catalog.html",
                           items = items,
                           categories = categories,
                           item_title = "Latest Items")

@app.route("/categories/<int:cat_id>")
def viewCategory(cat_id):
    session['target'] = url_for('viewCategory', cat_id = cat_id)
    sqlsession = SQLSession()
    category = sqlsession.query(Category).filter(Category.id == cat_id).first()
    categories = sqlsession.query(Category).all()
    items = sqlsession.query(Item).filter_by(category_id = cat_id).all()
    return render_template("view_category.html", category = category,
                           categories = categories,
                           items = items,
                           item_title = category.name + " Items")

@app.route("/categories/new", methods=['GET', 'POST'])
def insertCategory():
    if not 'userinfo' in session.keys():
        session['target'] = url_for('insertCategory')
        return redirect(url_for('gconnect'))
    if request.method == 'POST':
        try:
            sqlsession = SQLSession()
            creator_email = session['userinfo']['email']
            user = sqlsession.query(User).filter_by(email = creator_email).first()
            category = Category(name = request.form['name'], creator_id = user.id)
            sqlsession.add(category)
            sqlsession.commit()
        except IntegrityError:
            # if the user sends an alread existing name
            # it is safe to assume that the already
            # included copy is what he wanted
            pass
        return redirect("/")
    else:
        return render_template("new_category.html")

@app.route("/items/<int:item_id>")
def viewItem(item_id):
    session['target'] = url_for('viewItem', item_id = item_id)
    sqlsession = SQLSession()
    item = sqlsession.query(Item, Category).join(Category).filter(Item.id == item_id).first()
    return render_template("view_item.html", item = item)
        
@app.route("/items/new", methods=['GET', 'POST'])
def insertItem():
    if not 'userinfo' in session.keys():
        session['target'] = url_for('insertItem')
        return redirect(url_for('gconnect'))
    if request.method == 'POST':
        creator_email = session['userinfo']['email']
        sqlsession = SQLSession()
        user = sqlsession.query(User).filter_by(email = creator_email).first()
        item = Item(name = request.form['name'],
                    description = request.form['description'],
                    category_id = int(request.form['category']),
                    creator_id = user.id)
        sqlsession.add(item)
        sqlsession.commit()
        return redirect("/")
    else:
        sqlsession = SQLSession()
        categories = sqlsession.query(Category).all()
        return render_template("new_item.html",
                               categories = categories)

@app.route("/items/<int:item_id>/edit", methods = ['GET', 'POST'])
def editItem(item_id):
    if not 'userinfo' in session.keys():
        session['target'] = url_for('editItem', item_id = item_id)
        return redirect(url_for('gconnect'))
    if request.method == 'POST':
        sqlsession = SQLSession()
        item = sqlsession.query(Item).filter_by(id = item_id).first()
        item.name = request.form['name']
        item.category_id = request.form['category']
        item.description = request.form['description']
        sqlsession.commit()
        return redirect(url_for('viewItem', item_id = item_id))
    else:
        sqlsession = SQLSession()
        item = sqlsession.query(Item).filter_by(id = item_id).first()
        categories = sqlsession.query(Category).all()
        return render_template("edit_item.html", item = item, categories = categories)

@app.route("/items/<int:item_id>/delete", methods = ['GET', 'POST'])
def deleteItem(item_id):
    if not 'userinfo' in session.keys():
        session['target'] = url_for('deleteItem', item_id = item_id)
        return redirect(url_for('gconnect'))
    if request.method == 'POST':
        sqlsession = SQLSession()
        item = sqlsession.query(Item).filter_by(id = item_id).first()
        sqlsession.delete(item)
        sqlsession.commit()
        return redirect("/")
    else:
        sqlsession = SQLSession()
        item = sqlsession.query(Item, Category).join(Category).filter(Item.id == item_id).first()
        return render_template("delete_item.html", item = item)

def newState():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
