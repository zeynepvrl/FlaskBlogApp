from flask import Flask,render_template, flash, redirect, url_for, session, logging,request
from  flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


#login gerektiren fonksiyonların hemen öncesine bu decorator konulmalı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapmılısınız.")
            return redirect(url_for("login"))
    return decorated_function

class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.Length(min=4,max=30)])
    username=StringField("Username", validators=[validators.Length(min=5, max=30)])
    email=StringField("Email", validators=[validators.Email(message="Geçerli bir email adresi girin...")])
    password=PasswordField("Parola", validators=[
        validators.DataRequired(message="Liütfen bir parola giriniz..."),
        validators.equal_to(fieldname="confirm",message="Parolalar uyuşmuyor...")
    ])
    confirm=PasswordField("Parola Doğrulama")

class LoginForm(Form):
    username=StringField("Username")
    password=PasswordField("Parola")

app=Flask(__name__)

app.secret_key="blogApp"           #flash mesajları için gerekli

app.config["MYSQL_HOST"]="localhost"      #uzak bir server kiralamadığımız için 
app.config["MYSQL_USER"]="root"            #xampp de otamatik root ve boş parola ayarlıyor
app.config["MYSQL_PASSWORD"]="1234"
app.config["MYSQL_DB"]="ybblog"          #xampp de db oluştururken verdiğimiz isim
app.config["MYSQL_CURSORCLASS"]="DictCursor"   # aldığımız verileri cursor sözlük olarak döndürecek

mysql=MySQL(app)

@app.route("/")         #Bu dekoratör, belirli bir URL yolunu (/) Python fonksiyonuna bağlar.
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    form=LoginForm(request.form)

    if request.method=="POST":
        
        username=form.username.data
        password=form.password.data

        cursor=mysql.connection.cursor()
        sorgu="Select * From users where username=%s"

        result= cursor.execute(sorgu,(username,))
        if result>0:
            data=cursor.fetchone()
            real_password=data["password"]               # cursor yukarda belirtildiğimi gibi dictionary döndürü
            if sha256_crypt.verify(password,real_password):
                flash("Başarı ile giriş yaptınız!","success")
                session['logged_in']= True                       # session a projenin her yerinde kullanabilirisn, navbarda bunlara göre görünümü değiştireceksin, çıkış yap gözükecek artık
                session['username']=username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz..", "danger")
                return redirect(url_for("login"))

        else:
            flash("Böyle bir kullanıcı bulunmuyor...", "danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html" , form= form)

@app.route("/register", methods=["GET", "POST"] )
def register():
    form = RegisterForm(request.form)          #form u request.form dan gelen form verileri ile oluşturacağız

    if request.method=="POST" and form.validate():    #form validate değilse bilgilerde yanlışlık var ise çalışmaz

        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()
        sorgu="Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"      #pythondaki özelliğe geel, %s ile direkt alıyor aşağıdaki demetteki değerlerin yerine geçiyor
        cursor.execute(sorgu,(name,username,email,password))       #demet ile göndeririz, eğer bir değer gönderecekse (name,)  şeklinde olmalıydı
        mysql.connection.commit()     # veritabanında bir değişiklik yaptıysan eğer bunu commitlemen gerekir ayrıca 
        cursor.close()     #kaynak kullanım israfı olamması için ardında cursor u kapatmak gerekir her işlemden sonra

        flash("Başarıyla kayıt oldunuz!","success")            #flash mesajlarını layout a yerleştirdim, ,mcludes/messages dan include ederek

        return redirect(url_for("login"))    # yukardaki index() fonksiyonunun ilişkili olduğu dizine git -> url_of kullanımı
    else:
        return render_template("register.html", form = form )   #yukarda oluşturduğumuz formu template e gönderiyoruz sayfa geldiğinde gösterebilmek için

@app.route('/dashboard')
@login_required                    #route de bir decorator bu da, decorator parametre olarak aşağıdaki fonksiyonu alıyor
def dashboard():
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route('/addarticle' , methods=["GET", "POST"])
def addarticle():
    form=articleform(request.form)          #request.form dan gelen form ile oluşturuyoruz
    if request.method == "POST" and form.validate():
        title=form.title.data
        content=form.content.data
        
        cursor=mysql.connection.cursor()
        sorgu="INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu, (title, session['username'], content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarı ile yüklendi.","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html", form=form)      #GET isteği duurmunda sadece formu göstericez
    return render_template("addarticle.html", form=form)

#makale formu
class articleform(Form):
    title=StringField("Makale Başlığı", validators=[validators.length(min=5)])
    content=TextAreaField("Makale İçeriği", validators=[validators.length(min=10)] )

if __name__ == "__main__":
    app.run(debug=True)