from flask import Flask,render_template, flash, redirect, url_for, session, logging,request
from  flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt

class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.Length(min=4,max=30)])
    username=StringField("Username", validators=[validators.Length(min=10, max=30)])
    email=StringField("Email", validators=[validators.Email(message="Geçerli bir email adresi girin...")])
    password=PasswordField("Parola", validators=[
        validators.DataRequired(message="Liütfen bir parola giriniz..."),
        validators.equal_to(fieldname="confirm",message="Parolalar uyuşmuyor...")
    ])
    confirm=PasswordField("Parola Doğrulama")

app=Flask(__name__)

app.config["MYSQL_HOST"]="localhost"      #uzak bir server kiralamadığımız için 
app.config["MYSQL_USER"]="root"            #xampp de otamatik root ve boş parola ayarlıyor
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="ybblog"          #xampp de db oluştururken verdiğimiz isim
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)

@app.route("/")         #Bu dekoratör, belirli bir URL yolunu (/) Python fonksiyonuna bağlar.
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/register", methods=["GET", "POST"] )
def register():
    form = RegisterForm(request.form)          #eğer post requesti atıldıysa bu request içerisindeki from verileri oluşturduğumuz RegisterForm a gelecek 

    if request.method=="POST":

        name=form.name
        username=form.username
        email=form.email
        password=sha256_crypt.encrypt(form.password)

        return redirect(url_for(index))    # yukardaki index() fonksiyonunun ilişkili olduğu dizine git -> url_of kullanımı
    else:
        return render_template("register.html", form = form )   #yukarda oluşturduğumuz formu template e gönderiyoruz sayfa geldiğinde gösterebilmek için

if __name__ == "__main__":
    app.run(debug=True)