from flask import Flask, render_template, request, redirect, url_for, session
from db_setup import Base, Category, Item, SQLSession
from sqlalchemy.exc import IntegrityError
from google_auth_oauthlib.flow import Flow

app = Flask(__name__)
app.secret_key = "Supersecret Key"

FLOW = Flow.from_client_secrets_file('client_secrets.json',
                                        scopes = ['profile'],
                                        redirect_uri = 'http://localhost:8000/login')

@app.route("/login")
def login():
    # not sure why I should heed this state
    session['state'] = request.args['state']
    authorization_response = request.url
    FLOW.fetch_token(authorization_response = authorization_response)
    credentials = FLOW.credentials
    session['credentials'] = {
        'token' : credentials.token,
         'id' : credentials.client_id}
    return redirect("/")

@app.route("/gconnect")
def gconnect():
    authorization_url, state = FLOW.authorization_url()
    return redirect(authorization_url)
                                                                   
@app.route("/")
def catalog():
    sqlsession = SQLSession()
    items = sqlsession.query(Item).order_by(Item.create_date).limit(10)
    categories = sqlsession.query(Category).all()
    return render_template("catalog.html",
                           items = items,
                           categories = categories)

@app.route("/categories/new", methods=['GET', 'POST'])
def insertCategory():
    if not session['credentials']:
        return redirect(url_for('gconnect'))
    if request.method == 'POST':
        try:
            category = Category(name = request.form['name'])
            sqlsession = SQLSession()
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
        
@app.route("/items/new", methods=['GET', 'POST'])
def insertItem():
    if not session['credentials']:
        return redirect(url_for('gconnect'))
    if request.method == 'POST':
        item = Item(name = request.form['name'],
                    description = request.form['description'],
                    category_id = int(request.form['category']))
        sqlsession = SQLSession()
        sqlsession.add(item)
        sqlsession.commit()
        return redirect("/")
    else:
        sqlsession = SQLSession()
        categories = sqlsession.query(Category).all()
        return render_template("new_item.html",
                               categories = categories)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
