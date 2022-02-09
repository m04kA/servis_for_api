from marshmallow import Schema, fields, EXCLUDE
from datetime import date
from constants import *


class CurrentUserResponseModel(Schema):
    """
    It is simple data for showing (not admin)
    (return - get)
    """
    id = fields.Integer(required=True)
    first_name = fields.String()
    last_name = fields.String()
    other_name = fields.String(default="NO")
    email = fields.Email()
    phone = fields.String(default="0")
    birthday = fields.DateTime(default=date.today())
    is_admin = fields.Boolean()

    class Meta:
        unknown = EXCLUDE


class LoginModel(Schema):
    """
    It is login model
    (post)
    """
    email = fields.Email(required=True)
    password = fields.String(required=True)

    class Meta:
        unknown = EXCLUDE


class PrivateCreateUserModel(Schema):
    """
    It is for creating user by admin
    (post)
    """
    id = fields.Integer()
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    other_name = fields.String(default="NO")
    email = fields.Email(required=True)
    phone = fields.String(default="0")
    birthday = fields.DateTime(default=date.today())
    city = fields.Number(default=0, validate=lambda n: 0 <= n <= count_cities)
    additional_info = fields.String(default="NO")
    is_admin = fields.Boolean(required=True, default=False)
    password = fields.String(required=True)

    class Meta:
        unknown = EXCLUDE


class PrivateDetailUserResponseModel(Schema):
    """
    It need for showing by admin
    (return - get)
    """
    id = fields.Number()
    first_name = fields.String()
    last_name = fields.String()
    other_name = fields.String(default="NO")
    email = fields.Email()
    phone = fields.String(default="0")
    birthday = fields.DateTime(default=date.today())
    city = fields.Number(default=0)
    additional_info = fields.String(default="NO")
    is_admin = fields.Boolean(default=False)

    class Meta:
        unknown = EXCLUDE


class PrivateUpdateUserModel(Schema):
    """
    It need for update by admin. It is not necessary to fill in all the fields except email (it`s need for identification)
    (post)
    """
    id = fields.Number()
    first_name = fields.String()
    last_name = fields.String()
    other_name = fields.String()
    email = fields.Email()
    phone = fields.String()
    birthday = fields.DateTime()
    city = fields.Number(validate=lambda n: 0 <= n <= count_cities)
    additional_info = fields.String()
    is_admin = fields.Boolean()

    class Meta:
        unknown = EXCLUDE


class UpdateUserModel(Schema):
    """
    It need for update info. It is not necessary to fill in all the fields except email (it`s need for identification)
    (post)
    """
    first_name = fields.String()
    last_name = fields.String()
    other_name = fields.String()
    email = fields.Email()
    phone = fields.String()
    birthday = fields.DateTime()

    class Meta:
        unknown = EXCLUDE


class UpdateUserResponseModel(Schema):
    """
    It need for get info after update info about user.
    (get)
    """
    id = fields.Integer()
    first_name = fields.String()
    last_name = fields.String()
    other_name = fields.String()
    email = fields.Email()
    phone = fields.String()
    birthday = fields.DateTime()

    class Meta:
        unknown = EXCLUDE


class UsersListElementModel(Schema):
    """
    It is 1 information card in list about all users.
    """
    id = fields.Integer()
    first_name = fields.String()
    last_name = fields.String()
    email = fields.Email()

    class Meta:
        unknown = EXCLUDE
