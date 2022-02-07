from flask import Flask, request, render_template, make_response, redirect, url_for, jsonify
from mongoLib import *
from werkzeug.security import generate_password_hash, check_password_hash
from schems import *
from datetime import datetime
from constants import *

from forms import RegistrationForm, LoginForm

app = Flask(__name__)

collection_name = None
links_all = ["/login", "/logout", "/users/current", "/users", "/users/{pk}", "/private/users", "/private/users/{pk}"]

links_with_log = {"Главная": "/", "Выйти": "/logout", "Данные о пользователе": "/users/current",
                  "Изменить данные о пользователе": "/users/{pk}", "Данные о всех пользователях": "/users"}

links_with_log_admin = {"Главная": "/", "Выйти": "/logout", "Данные о пользователе": "/users/current",
                        "Изменить данные о пользователе": "/users/{pk}", "Данные о всех пользователях": "/users",
                        "Все данные о пользователях для админа": "/private/users",
                        "Изменить данные о пользователе для админа": "/private/users/{pk}"}

links_without_log = {"Главная": "/", "Войти || Зарегистрироваться": "/login", "Данные о всех пользователях": "/users"}

menu = links_without_log


@app.before_request
def validate_user_for_menu():
    global menu
    if request.cookies.get('logged'):
        if request.cookies.get('logged') == 'yes':
            if request.cookies.get('admin'):
                if request.cookies.get('admin') == 'yes':
                    menu = links_with_log_admin
            else:
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


@app.route('/')
def main_page():
    content = render_template('base.html', menu=menu)
    rez = make_response(content, 200)
    return rez


@app.route('/test/<pk>', methods=['post', 'get'])
def test_pk(pk):
    if request.method == "POST":
        code = 403
        test_dict = {"message": "You don't have enough access", "code": code}
        return jsonify(test_dict), code

    if pk == 0:
        if request.cookies.get("logged") == 'yes':
            test_dict = {"hi": "login", "id": 1, "num": 15}
            content = jsonify(test_dict)
            content.set_cookie("logged", "", 0)
        else:
            test_dict = {"hi": "bye", "id": 0, "num": 12.3}
            content = jsonify(test_dict)
            content.set_cookie("logged", "yes")
        return content, 200
    else:
        print(type(pk))
        return pk


@app.route('/test', methods=['post', 'get'])
def test():
    if request.method == "POST":
        code = 403
        test_dict = {"message": "You don't have enough access", "code": code}
        return jsonify(test_dict), code
    else:
        if request.cookies.get("logged") == 'yes':
            test_dict = {"hi": "login", "id": 1, "num": 15}
            content = jsonify(test_dict)
            content.set_cookie("logged", "", 0)
        else:
            test_dict = {"hi": "bye", "id": 0, "num": 12.3}
            content = jsonify(test_dict)
            content.set_cookie("logged", "yes")
        return content, 200


def return_exept_code(code, text, cooky=True):
    code = code
    server_answer = {"Message": text, "code": code}
    content = jsonify(server_answer)
    if cooky:
        content.set_cookie("logged", "", 0)
        content.set_cookie("admin", "", 0)
        content.set_cookie("id", "", 0)
    return content, code


def return_exept_code_422(exept, cooky=True):
    code = 422
    server_answer = {
        "Detail": [{"Location": [[el for el in exept]],
                    "Message": "Wrong input",
                    "Error Type": "ValidationError"}]
    }
    content = jsonify(server_answer)
    if cooky:
        content.set_cookie("logged", "", 0)
        content.set_cookie("admin", "", 0)
        content.set_cookie("id", "", 0)
    return content, code


@app.route("/login", methods=['post'])
def login_login_post():
    if request.cookies.get('logged') == 'yes':
        content, code = return_exept_code(403, "You don't have enough access")
        return content, code
    else:
        if request.method == 'POST':
            try:
                data_from_user = request.get_json()
            except Exception as ex:
                print(ex)
                content, code = return_exept_code(400, f"Bad Request: {ex}")
                return content, code
            try:
                login_schema = LoginModel()
                true_data = login_schema.load(data_from_user)
            except Exception as ex:
                print(ex)
                content, code = return_exept_code_422(ex.messages)
                return content, code
            email = true_data['email']
            password = true_data['password']
            result = find_document(collection_name, {"email": email})
            if result:
                if check_password_hash(result['password'], password):
                    content, code = return_exept_code(200, "Successful Response")
                    content.set_cookie("logged", "yes")
                    content.set_cookie("id", str(result['id']))
                    if result["is_admin"]:
                        content.set_cookie("admin", "yes")
                    return content, code
                else:
                    content, code = return_exept_code_422(["Password isn`t true"])
                    return content, code
            else:
                content, code = return_exept_code_422(["The user does not exist"])
                return content, code


@app.route("/logout", methods=['get'])
def logout_logout_get():
    if request.cookies.get('logged') == 'yes':
        content, code = return_exept_code(200, "Successful Response")
        return content, code
    else:
        content, code = return_exept_code(403, "You don't have enough access")
        return content, code


@app.route("/users/current")
def current_user_users_current_get():
    if request.method == "GET":
        if request.cookies.get('logged') == 'yes' and request.cookies.get('id') != "":
            user = find_document(collection_name, {'id': int(request.cookies.get('id'))})
            try:
                user['birthday'] = str(user['birthday'])
                schem_for_info_user = CurrentUserResponseModel()
                answer_server_info = schem_for_info_user.load(user)
            except Exception as ex:
                content, code = return_exept_code_422(ex.messages)
                return content, 500
            content = jsonify(answer_server_info)
            return content, 200
        else:
            content, code = return_exept_code(401, "Unauthorized: You don't have enough access")
            return content, code
    else:
        content, code = return_exept_code(400, f"Bad Request. You are using the wrong request. ")
        return content, code


@app.route("/users/<pk>", methods=['post', 'get'])
def edit_user_users__pk__patch(pk):
    if request.method != "POST":
        content, code = return_exept_code(400, f"Bad Request. You are using the wrong request. ", cooky=False)
        return content, code
    elif request.cookies.get('logged') != 'yes':
        content, code = return_exept_code(401, "Unauthorized: You don't have enough access")
        return content, code
    elif request.cookies.get("id") != pk:
        content, code = return_exept_code(403,
                                          "You don't have enough access. Pleas using your 'id', you can find it in '/users/current'.",
                                          cooky=False)
        return content, code
    else:
        try:
            data_from_user_for_update_info = request.get_json()
        except Exception as ex:
            print(ex)
            content, code = return_exept_code(400, f"Bad Request: {ex}", cooky=False)
            return content, code
        try:
            login_schema = UpdateUserModel()
            true_data = login_schema.load(data_from_user_for_update_info)
        except Exception as ex:
            print(ex)
            content, code = return_exept_code_422(ex.messages, cooky=False)
            return content, code
        result = find_document(collection_name, {"id": int(pk)})
        new_info_user = result | true_data
        update_document(collection_name, {"id": int(pk)}, new_info_user)
        content, code = return_exept_code(200, "Successful Response", cooky=False)
        return content, code


# @app.route("/register", methods=['post', 'get'])
# def register():
#     form = RegistrationForm(request.form)
#     if request.method == "POST":
#         email = request.form.get('email')
#         password = request.form.get('password')
#         confirm = request.form.get('confirm')
#         first_name = request.form.get('First_name')
#         second_name = request.form.get('Second_name')
#         other_name = request.form.get('Other_name')
#         phone = request.form.get('phone')
#         birthday = request.form.get('birthday')
#         city = request.form.get('city')
#         additional_info = request.form.get('additional_info')
#
#         result = find_document(collection_name, {"Email": email})
#         if password != confirm:
#             return render_template("register.html", menu=menu, title="Пароли не совпадают", form=form)
#         elif result:
#             return render_template("register.html", menu=menu, title="Почта уже занята", form=form)
#         elif form.validate_on_submit:
#             user = {
#                 "First Name": first_name,
#                 "Last Name": second_name,
#                 "Other Name": other_name,
#                 "Email": email,
#                 "phone": phone,
#                 "birthday": birthday,
#                 "city": city,
#                 "additional_info": additional_info,
#                 "password": generate_password_hash(password),
#                 "is_admin": False
#             }
#             insert_document(collection_name, user)
#             return redirect(url_for("login_login_post", code=200))
#
#     return render_template("register.html", menu=menu, title="Регистрация", form=form)


# ---- Start info for DB ----
conecting_to_DB()
admin = {
    "id": 1,
    "first_name": "Jack",
    "last_name": "Sims",
    "other_name": "Alexandrovich",
    "email": "admin@admin.ru",
    "phone": '8-915-190-17-22',
    "birthday": str(datetime.strptime("12.11.2003", "%d.%m.%Y")),
    "city": 1,
    "password": generate_password_hash("ADmIn"),
    "is_admin": True
}
# int(collection_name.count_documents({}))
user = {
    "id": 2,
    "first_name": "Sam",
    "last_name": "Johan",
    "other_name": "Petrovich",
    "email": "noadmin@noadmin.ru",
    "phone": '8-916-196-16-26',
    "birthday": str(datetime.strptime("14.02.2020", "%d.%m.%Y")),
    "city": 2,
    "password": generate_password_hash("JoHAn"),
    "is_admin": False
}

cities = {
    "id": 0,
    "0": "NO",
    "1": "Moscow",
    "2": "Saint-Petersburg",
    "3": "Nizhny-Novgorod",
    "4": "Samara",
    "5": "Uglich"
}
count_cities = len(cities) - 2
# -----------------------------------

# ---- Upload data about ADMIN ----
create_admin_shem = PrivateCreateUserModel()
try:
    admin_schem = create_admin_shem.load(admin)
except Exception as exx:
    raise ValueError(f"Problem with admin: {exx}")
result = find_document(collection_name, {"email": admin_schem['email']})
if result:
    update_document(collection_name, {"email": admin_schem['email']}, admin_schem)
else:
    collection_name.create_index([("email", pymongo.ASCENDING)], unique=True)
    collection_name.create_index([("id", pymongo.ASCENDING)], unique=True)
    insert_document(collection_name, admin_schem)
# -----------------------------------


# ---- Upload data about User ----
create_admin_shem = PrivateCreateUserModel()
try:
    admin_schem = create_admin_shem.load(user)
except Exception as exx:
    raise ValueError(f"Problem with user: {exx}")
result = find_document(collection_name, {"email": admin_schem['email']})
if result:
    update_document(collection_name, {"email": admin_schem['email']}, admin_schem)
else:
    insert_document(collection_name, admin_schem)
# -----------------------------------


# ---- Upload data about cities ----
result = ""
result = find_document(collection_name, {"id": cities['id']})
if result:
    update_document(collection_name, {"id": cities['id']}, cities)
else:
    collection_name.create_index([("id", pymongo.ASCENDING)], unique=True)
    insert_document(collection_name, cities)
# -----------------------------------

if __name__ == '__main__':
    app.run(debug=True)
