from flask_wtf import FlaskForm
from wtforms import ValidationError, StringField, PasswordField, BooleanField, SubmitField, DecimalField, IntegerField
from wtforms.validators import InputRequired
import pickle

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()], render_kw={"placeholder": "Kullanıcı Adı"}) 
    password = PasswordField("Password", validators=[InputRequired()], render_kw={"placeholder": "Şifre"})
    submit = SubmitField('Giriş Yap')

    def validate_password(form, field):
        users = {}
        with open('/var/www/webApp/users_data.pckl', 'rb') as users_data:  
            users = pickle.load(users_data)

        try:
            username = users[form.username.data]
        except:
            raise ValidationError("Kullanıcı Bulunamadı! ")
            
        if users[form.username.data]["password"] != field.data:
            raise ValidationError("Hatalı Şifre")

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()], render_kw={"placeholder": "Kullanıcı Adı"})
    password = PasswordField("Password", validators=[InputRequired()], render_kw={"placeholder": "Şifre"} )
    api = StringField("Api", validators=[InputRequired()], render_kw={"placeholder": "Api"})
    secret = StringField("Secret", validators=[InputRequired()], render_kw={"placeholder": "Secret"})
    submit = SubmitField('Kayıt Ol')

