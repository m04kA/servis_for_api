from flask import Flask, request, render_template, make_response
from mongoLib import *

app = Flask(__name__)

collection_name = None
client = None
links_all = ["/login", "/logout", "/users/current", "/users", "/users/{pk}", "/private/users", "/private/users/{pk}"]

links_with_log = {"Главная": "/", "Выйти": "/logout", "Данные о пользователе": "/users/current",
                  "Изменить данные о пользователе": "/users/{pk}", "Данные о всех пользователях": "/users"}

links_with_log_admin = {"Главная": "/", "Выйти": "/logout", "Данные о пользователе": "/users/current",
                        "Изменить данные о пользователе": "/users/{pk}", "Данные о всех пользователях": "/users",
                        "Все данные о пользователях для админа": "/private/users",
                        "Изменить данные о пользователе для админа": "/private/users/{pk}"}

links_without_log = {"Главная": "/", "Войти": "/login", "Данные о всех пользователях": "/users"}


@app.before_request
def conecting_to_DB(name_DB="Kefir", name_collection="Kefir_collection", port=27017):
    """
    Connect to DB
    :param name_DB:
    :param name_collection:
    :param port:
    :return:
    """
    global collection_name, client
    client = pymongo.MongoClient(port=port)
    DB = client[name_DB]
    collection_name = DB[name_collection]
    # return collection_name


# @app.teardown_request
# def disconecting_to_DB():
#     global client
#     client.close()


@app.route('/')
def main_page():
    menu = links_without_log
    cooky = ""
    if request.cookies.get('logged'):
        cooky = request.cookies.get('logged')

    if cooky == 'yes':
        menu = links_with_log
    content = render_template('base.html', menu=menu)
    rez = make_response(content, 200)
    rez.set_cookie('logged', 'yes')
    return rez


@app.route("/logout")
def logout():
    menu = links_without_log
    content = render_template("base.html", menu=menu, title="Вы больше не авторизованы!")
    res = make_response(content)
    res.set_cookie("logged", "", 0)
    return res


@app.route("/login")
def login():
    menu = links_with_log
    content = render_template("base.html", menu=menu, title="Вы авторизованы!")
    res = make_response(content)
    res.set_cookie("logged", "yes")
    return res


# admin = {
#     'login': 'admin',
#     'password': 'ADmIn'
# }
# conecting_to_DB()
# insert_document(collection_name, admin)

if __name__ == '__main__':
    app.run(debug=True)
