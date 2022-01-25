from flask import Flask, request, render_template, make_response, redirect
from mongoLib import *
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm

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

menu = links_without_log


@app.before_request
def validate_user_for_menu():
    global menu
    cooky = ""
    if request.cookies.get('logged'):
        cooky = request.cookies.get('logged')

    if cooky == 'yes':
        menu = links_with_log
    else:
        menu = links_without_log


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
    # menu = links_without_log
    # cooky = ""
    # if request.cookies.get('logged'):
    #     cooky = request.cookies.get('logged')
    #
    # if cooky == 'yes':
    #     menu = links_with_log
    global menu
    content = render_template('base.html', menu=menu)
    rez = make_response(content, 200)
    return rez


@app.route("/logout")
def logout_logout_get():
    global menu
    if request.cookies.get('logged'):
        if request.cookies.get('logged') == 'yes':
            content = render_template("base.html", menu=menu, title="Вы больше не авторизованы!")
            res = make_response(content)
            res.set_cookie("logged", "", 0)
            return res
    else:
        return redirect("/", code=401)


@app.route("/login", methods=['post', 'get'])
def login_login_post():
    global menu
    if request.cookies.get('logged'):
        if request.cookies.get('logged') == 'yes':
            return redirect("/", code=200)
    else:
        form = LoginForm(request.form)
        content = render_template("login.html", menu=menu, title="Вход на портал", form=form)
        res = make_response(content)
        res.set_cookie("logged", "yes", 24 * 3600)
        return res


@app.route("/register", methods=['post', 'get'])
def register():
    global menu
    form = RegistrationForm
    return render_template("register.html", menu=menu, title="Регистрация", form=form)


#
admin = {

    "First Name": "Jack",
    "Last Name": "Sims",
    "Other Name": "Alexandrovich",
    "Email": "admin@admin.ru",
    "phone": '8-915-190-17-22',
    "birthday": "12.11.2003",
    "city": "Moscow",
    "additional_info": "Nothing",
    "password": "ADmIn",
    "is_admin": True
}
conecting_to_DB()
result = find_document(collection_name, {"Email": admin['Email'], "password": admin['password']})
if result:
    update_document(collection_name, {"Email": admin['Email'], "password": admin['password']}, admin)
else:
    collection_name.create_index([("Email", pymongo.ASCENDING)], unique=True)
    insert_document(collection_name, admin)

if __name__ == '__main__':
    app.run(debug=True)
