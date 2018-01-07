from flask import Flask
from db_setup import Base, Category, Item, SQLSession

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World"
