from flask import Flask, request, render_template, make_response, redirect, url_for, jsonify
from mongoLib import *
from werkzeug.security import generate_password_hash, check_password_hash
from schems import *
from datetime import datetime
from constants import *

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
    validate_user_for_menu()
    content = render_template('base.html', menu=menu)
    rez = make_response(content, 200)
    return rez


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
        content, code = return_exept_code(403, "You don't have enough access", cooky=False)
        return content, code
    else:
        if request.method == 'POST':
            try:
                data_from_user = request.get_json()
            except Exception as ex:
                print(ex)
                content, code = return_exept_code(400, f"Bad Request: {ex}")
                return content, code
            if not data_from_user:
                content, code = return_exept_code(400, f"Bad Request: data is None", cooky=False)
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


@app.route("/users/<pk>", methods=['patch'])
def edit_user_users__pk__patch(pk):
    if request.cookies.get('logged') != 'yes':
        content, code = return_exept_code(401, "Unauthorized: You don't have enough access")
        return content, code
    elif request.cookies.get("id") != pk:
        content, code = return_exept_code(403,
                                          "You don't have enough access. Pleas using your 'id', you can find it in '/users/current'.",
                                          cooky=False)
        return content, code
    try:
        pk = int(pk)
    except Exception as ex:
        content, code = return_exept_code(400, f"Bad Request: Your pk isn`t a number.", cooky=False)
        return content, code
    try:
        data_from_user_for_update_info = request.get_json()
    except Exception as ex:
        print(ex)
        content, code = return_exept_code(400, f"Bad Request: {ex}", cooky=False)
        return content, code
    if not data_from_user_for_update_info:
        content, code = return_exept_code(400, f"Bad Request: data is None", cooky=False)
        return content, code
    try:
        login_schema = UpdateUserModel()
        true_data = login_schema.load(data_from_user_for_update_info)
    except Exception as ex:
        print(ex)
        content, code = return_exept_code_422(ex.messages, cooky=False)
        return content, code
    result = find_document(collection_name, {"id": int(pk)})
    if not result:
        print(404)
        content, code = return_exept_code(404, "User not found", cooky=False)
        return content, code
    new_info_user = result | true_data
    update_document(collection_name, {"id": int(pk)}, new_info_user)
    content, code = return_exept_code(200, "Successful Response", cooky=False)
    return content, code


@app.route("/users", methods=['get'])
def users_users_get():
    page = request.args.get('page', default=1, type=int)
    size = request.args.get('size', default=10, type=int)
    if page < 1 or size < 1:
        content, code = return_exept_code(400, f"Bad Request. You are using the wrong request. ", cooky=False)
        return content, code
    elif request.cookies.get('logged') != 'yes':
        content, code = return_exept_code(401, "Unauthorized: You don't have enough access")
        return content, code
    total = int(collection_name.count_documents({})) - 1
    data = []
    start = (page - 1) * size + 1
    end = page * size + 1
    if total < start:
        server_answer = {
            "data": data,
            "meta": {
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size
                }
            }
        }
        return jsonify(server_answer), 200
    else:
        if end > total:
            end = total + 1
        mass_id_users = [id for id in range(start, end)]
        users = []
        for id in mass_id_users:
            users.append(find_document(collection_name, {"id": id}))
        try:
            schem = UsersListElementModel(many=True)
            data = schem.load(users)
        except Exception as ex:
            print(ex)
            content, code = return_exept_code_422(ex.messages, cooky=False)
            return content, code
        server_answer = {
            "data": data,
            "meta": {
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size
                }
            }
        }
        return jsonify(server_answer), 200


@app.route("/private/users", methods=['get'])
def private_users_private_users_get():
    page = request.args.get('page', default=1, type=int)
    size = request.args.get('size', default=10, type=int)
    if page < 1 or size < 1:
        content, code = return_exept_code(400, f"Bad Request. You are using the wrong request. ", cooky=False)
        return content, code
    elif request.cookies.get('logged') != 'yes':
        content, code = return_exept_code(401, "Unauthorized: You don't have enough access")
        return content, code
    elif request.cookies.get('admin') != 'yes':
        content, code = return_exept_code(403,
                                          "You don't have enough access. Response 403 Private Users Private Users Get")
        return content, code
    total = int(collection_name.count_documents({})) - 1
    data = []
    start = (page - 1) * size + 1
    end = page * size + 1
    if total < start:
        server_answer = {
            "data": data,
            "meta": {
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size
                }
            }
        }
        return jsonify(server_answer), 200
    else:
        if end > total:
            end = total + 1
        mass_id_users = [id for id in range(start, end)]
        users = []
        for id in mass_id_users:
            users.append(find_document(collection_name, {"id": id}))
        try:
            schem = UsersListElementModel(many=True)
            data = schem.load(users)
        except Exception as ex:
            print(ex)
            content, code = return_exept_code_422(ex.messages, cooky=False)
            return content, code
        server_answer = {
            "data": data,
            "meta": {
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size
                }
            }
        }
        return jsonify(server_answer), 200


@app.route("/private/users", methods=['post'])
def private_create_users_private_users_post():
    if request.cookies.get('logged') != 'yes':
        content, code = return_exept_code(401, "Unauthorized: You don't have enough access")
        return content, code
    elif request.cookies.get('admin') != 'yes':
        content, code = return_exept_code(403,
                                          "You don't have enough access. Response 403 Private Users Private Users Get")
        return content, code
    try:
        new_user_from_admin = request.get_json()
    except Exception as ex:
        print(ex)
        content, code = return_exept_code(400, f"Bad Request: {ex}", cooky=False)
        return content, code
    if not new_user_from_admin:
        content, code = return_exept_code(400, f"Bad Request: data is None", cooky=False)
        return content, code
    try:
        new_user_from_admin['birthday'] = str(datetime.strptime(new_user_from_admin['birthday'], "%d.%m.%Y"))
        login_schema = PrivateCreateUserModel()
        true_data = login_schema.load(new_user_from_admin)
        true_data['password'] = generate_password_hash(true_data['password'])
    except Exception as ex:
        print(ex)
        content, code = return_exept_code_422(ex.messages, cooky=False)
        return content, code
    id_new_user = int(collection_name.count_documents({}))
    true_data['id'] = id_new_user
    result = ''
    result = find_document(collection_name, {"id": true_data['id']})
    if result:
        content, code = return_exept_code(400, f"Bad Request this user already exists.", cooky=False)
        return content, code
    insert_document(collection_name, true_data)
    result = find_document(collection_name, {"id": id_new_user})
    try:
        result["birthday"] = str(result["birthday"])
        login_schema = PrivateDetailUserResponseModel()
        server_answer = login_schema.load(result)
    except Exception as ex:
        print(ex)
        content, code = return_exept_code_422(ex.messages, cooky=False)
        return content, code
    return jsonify(server_answer), 201


@app.route("/private/users/<pk>", methods=['get'])
def private_get_user_private_users__pk__get(pk):
    if request.cookies.get('logged') != 'yes':
        content, code = return_exept_code(401, "Unauthorized: You don't have enough access")
        return content, code
    elif request.cookies.get('admin') != 'yes':
        content, code = return_exept_code(403,
                                          "You don't have enough access. Response 403 Private Users Private Users Get")
        return content, code
    try:
        pk = int(pk)
    except Exception as ex:
        content, code = return_exept_code(400, f"Bad Request: Your pk isn`t a number.", cooky=False)
        return content, code
    if pk < 1:
        content, code = return_exept_code(400, f"Bad Request this user isn`t exists.", cooky=False)
        return content, code
    elif int(collection_name.count_documents({})) - 1 < pk:
        content, code = return_exept_code(404, "User not found", cooky=False)
        return content, code
    result = find_document(collection_name, {"id": int(pk)})
    try:
        result["birthday"] = str(result["birthday"])
        login_schema = PrivateDetailUserResponseModel()
        server_answer = login_schema.load(result)
    except Exception as ex:
        print(ex)
        content, code = return_exept_code_422(ex.messages, cooky=False)
        return content, code
    return jsonify(server_answer), 201


@app.route("/private/users/<pk>", methods=['delete'])
def private_delete_user_private_users__pk__delete(pk):
    if request.cookies.get('logged') != 'yes':
        content, code = return_exept_code(401, "Unauthorized: You don't have enough access")
        return content, code
    elif request.cookies.get('admin') != 'yes':
        content, code = return_exept_code(403,
                                          "You don't have enough access. Response 403 Private Users Private Users Get")
        return content, code
    try:
        pk = int(pk)
    except Exception as ex:
        content, code = return_exept_code(400, f"Bad Request: Your pk isn`t a number.", cooky=False)
        return content, code
    if pk < 1:
        content, code = return_exept_code(400, f"Bad Request this user isn`t exists.", cooky=False)
        return content, code
    elif int(collection_name.count_documents({})) - 1 < pk:
        content, code = return_exept_code(404, "User not found", cooky=False)
        return content, code
    total = int(collection_name.count_documents({}))
    start = pk + 1
    delete_document(collection_name, {"id": int(pk)})

    mass_id_users = [id for id in range(start, total)]
    for id in mass_id_users:
        user = find_document(collection_name, {"id": id})
        user['id'] = id - 1
        update_document(collection_name, {'email': user['email']}, user)

    content, code = return_exept_code(204, "Successful Response", cooky=False)
    return content, code


@app.route("/private/users/<pk>", methods=['patch'])
def private_patch_user_private_users__pk__patch(pk):
    if request.cookies.get('logged') != 'yes':
        content, code = return_exept_code(401, "Unauthorized: You don't have enough access")
        return content, code
    elif request.cookies.get('admin') != 'yes':
        content, code = return_exept_code(403,
                                          "You don't have enough access. Response 403 Private Users Private Users Get")
        return content, code
    try:
        pk = int(pk)
    except Exception as ex:
        content, code = return_exept_code(400, f"Bad Request: Your pk isn`t a number.", cooky=False)
        return content, code
    if pk < 1:
        content, code = return_exept_code(400, f"Bad Request this user isn`t exists.", cooky=False)
        return content, code
    elif int(collection_name.count_documents({})) - 1 < pk:
        content, code = return_exept_code(404, "User not found", cooky=False)
        return content, code
    try:
        data_from_admin_for_update_info = request.get_json()
    except Exception as ex:
        print(ex)
        content, code = return_exept_code(400, f"Bad Request: {ex}", cooky=False)
        return content, code
    if not data_from_admin_for_update_info:
        content, code = return_exept_code(400, f"Bad Request: data is None", cooky=False)
        return content, code
    try:
        login_schema = PrivateUpdateUserModel()
        true_data = login_schema.load(data_from_admin_for_update_info)
    except Exception as ex:
        print(ex)
        content, code = return_exept_code_422(ex.messages, cooky=False)
        return content, code
    result = find_document(collection_name, {"id": int(pk)})
    if not result:
        print(404)
        content, code = return_exept_code(404, "User not found", cooky=False)
        return content, code
    new_info_user = result | true_data
    update_document(collection_name, {"id": pk}, new_info_user)
    result = find_document(collection_name, {"id": pk})
    try:
        result["birthday"] = str(result["birthday"])
        login_schema = PrivateDetailUserResponseModel()
        server_answer = login_schema.load(result)
    except Exception as ex:
        print(ex)
        content, code = return_exept_code_422(ex.messages, cooky=False)
        return content, code
    return jsonify(server_answer), 200


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

# { (user_7 data for /private/users)
#     "first_name": "Salamolekume",
#     "last_name": "Popalameslam",
#     "email": "admin2@admin2.ru",
#     "phone": '8-922-122-22-22',
#     "birthday": "14.03.2020",
#     "city": 4,
#     "password": "keKaKu",
#     "is_admin": True
# }

user = {
    "id": 2,
    "first_name": "Salam",
    "last_name": "Popalam",
    "other_name": "Sidorovich",
    "email": "noadmin2@noadmin2.ru",
    "phone": '8-912-192-12-22',
    "birthday": str(datetime.strptime("14.02.2020", "%d.%m.%Y")),
    "city": 2,
    "password": generate_password_hash("JoHAn"),
    "is_admin": False
}

# --------------------------
user1 = {
    "id": 3,
    "first_name": "Sam",
    "last_name": "Johan",
    "other_name": "Petrovich",
    "email": "noadmin3@noadmin3.ru",
    "phone": '8-913-193-13-23',
    "birthday": str(datetime.strptime("14.02.2020", "%d.%m.%Y")),
    "city": 2,
    "password": generate_password_hash("JoHAn"),
    "is_admin": False
}
user2 = {
    "id": 4,
    "first_name": "Toshka",
    "last_name": "Koshka",
    "other_name": "Petroh",
    "email": "noadmin4@noadmin4.ru",
    "phone": '8-914-194-14-24',
    "birthday": str(datetime.strptime("14.02.2020", "%d.%m.%Y")),
    "city": 2,
    "password": generate_password_hash("JoHAn"),
    "is_admin": False
}
user3 = {
    "id": 5,
    "first_name": "Sam5",
    "last_name": "Johan5",
    "other_name": "Petrovich5",
    "email": "noadmin5@noadmin5.ru",
    "phone": '8-915-195-15-25',
    "birthday": str(datetime.strptime("14.02.2020", "%d.%m.%Y")),
    "city": 2,
    "password": generate_password_hash("JoHAn"),
    "is_admin": False
}
user4 = {
    "id": 6,
    "first_name": "Sam6",
    "last_name": "Johan6",
    "other_name": "Petrovich6",
    "email": "noadmin6@noadmin6.ru",
    "phone": '8-916-196-16-26',
    "birthday": str(datetime.strptime("14.02.2020", "%d.%m.%Y")),
    "city": 2,
    "password": generate_password_hash("JoHAn"),
    "is_admin": False
}
# ---------------------------

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
result = find_document(collection_name, {"id": admin_schem['id']})
if result:
    update_document(collection_name, {"id": admin_schem['id']}, admin_schem)
else:
    collection_name.create_index([("email", pymongo.ASCENDING)], unique=True)
    collection_name.create_index([("id", pymongo.ASCENDING)], unique=True)
    insert_document(collection_name, admin_schem)
# -----------------------------------

# ---- Upload data about Users ----
create_admin_shem = PrivateCreateUserModel()
for user in [user, user1, user2, user3, user4]:
    try:
        admin_schem = create_admin_shem.load(user)
    except Exception as exx:
        raise ValueError(f"Problem with user: {exx}")
    result = find_document(collection_name, {"id": admin_schem['id']})
    if result:
        update_document(collection_name, {"id": admin_schem['id']}, admin_schem)
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
