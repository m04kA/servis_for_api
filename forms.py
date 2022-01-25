from wtforms import Form, validators, BooleanField, StringField, PasswordField, DateField


class RegistrationForm(Form):
    First_name = StringField('Имя', [validators.Length(min=2, max=25)])
    Second_name = StringField('Фамилия', [validators.Length(min=2, max=25)])
    Other_name = StringField('Отчество', [validators.Length(min=2, max=25)], default="NO")
    email = StringField('Email-адрес', [validators.Length(min=6, max=35)])
    phone = StringField('Телефон', [validators.Length(min=7, max=20)])
    birthday = DateField('День рождения', [validators.Length(min=9, max=11)])
    city = StringField('Город', [validators.Length(min=2, max=30)], default="NO")
    additional_info = StringField('Доп. информация', default="Nothing")
    password = PasswordField('Новый пароль', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Пароли должны совпадать')
    ])
    confirm = PasswordField('Повторите пароль')


class LoginForm(Form):
    email = StringField('Email-адрес', [validators.Length(min=6, max=35)])
    password = PasswordField('Введите пароль')
    remember_me = BooleanField('Запомнить меня', [validators.DataRequired()], default=False)
