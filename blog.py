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
    cursor=mysql.connection.cursor()
    query="SELECT * FROM articles WHERE author=%s"
    result=cursor.execute(query,(session['username'],))         #tuple ama tek elemanlı bir tuple olduğunu , ile belirtmeyi unutma

    if result>0:
        articles=cursor.fetchall()
        return render_template('dashboard.html', articles=articles)
    else:
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


#makale formu
class articleform(Form):
    title=StringField("Makale Başlığı", validators=[validators.length(min=5)])
    content=TextAreaField("Makale İçeriği", validators=[validators.length(min=10)] )

@app.route('/articles')
def articles():
    cursor=mysql.connection.cursor()
    query="SELECT * from articles"
    cursor.execute(query)
    articles=cursor.fetchall()
    return render_template('articles.html', articles=articles)


#article detay sayfası, başlığa tıklayınca
@app.route('/article/<string:id>')
def article(id):
    cursor=mysql.connection.cursor()
    query="SELECT * FROM articles WHERE id = %s"
    result=cursor.execute(query, (id,))
    if result>0:
        article=cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        render_template("article.html")

#makale silme
@app.route('/delete/<string:id>')
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    query="Select * from articles where author=%s and id=%s"              #giriş yapmış userın adoyla o makale id sinde bir makale varmmı?
    result=cursor.execute(query, (session['username'], id))
    if result>0:
        article=cursor.fetchone()
        query="Delete from articles where id =%s"
        cursor.execute(query, (id,))
        mysql.connection.commit()                         #veritabanında bir değişiklik yaptın komitlemek gerekir
        return redirect(url_for('dashboard'))
    else:
        flash("Buna yetkiniz yok","danger")
        return redirect(url_for("index"))

#makale güncelleme
@app.route('/update/<string:id>' , methods=["GET","POST"] )
def update(id):
    if request.method =="GET":
        query="SELECT * from articles where id=%s and author=%s"
        cursor=mysql.connection.cursor()
        result = cursor.execute(query,(id, session['username']))
        if result<=0:
            flash("Böyle bir yetkiniz bulunmamaktadır.")
            return redirect(url_for("index"))
        else:
            article=cursor.fetchone()
            form=articleform()
            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template('update.html', form=form)
    else:
        form=articleform(request.form)
        newtitle=form.title.data
        newcontent=form.content.data
        query="Update articles set title=%s , content=%s where id=%s "
        cursor=mysql.connection.cursor()
        cursor.execute(query,(newtitle,newcontent,id))
        mysql.connection.commit()
        flash("Makale Başarı ile güncellendi..")
        return redirect(url_for("dashboard"))

#Arama 
@app.route("/search", methods=["POST","GET"])        #bu sayfaya hem get request hem post request gelebilir ancak benim sadece post requeste e izin vermem gerekir, url den /search yazıldığında get gelir ama bu yapılırsa ana sayfaya gitsin
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connect.cursor()
        query="Select * from articles where title like '%"+keyword+"%' "
        result=cursor.execute(query)
        if result ==0:
            flash("Aranan kelimeye uygun bir makale bulunamadı")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html", articles=articles)
        
if __name__ == "__main__":
    app.run(debug=True)