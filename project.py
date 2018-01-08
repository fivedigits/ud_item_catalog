from flask import Flask, render_template, request, redirect
from db_setup import Base, Category, Item, SQLSession
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

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
