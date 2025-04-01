from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from wtforms import Form, StringField, PasswordField, validators, SubmitField
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message



db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.static_folder = 'static'
app.secret_key = "randomstatement"
db.init_app(app)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


UPLOAD_FOLDER = os.path.join('static', 'images', 'drawings')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Flask-Mail configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "selene.contactus@gmail.com"  # Gmail address
app.config["MAIL_PASSWORD"] = "jjyh bwjs fmsx enzx"    
app.config["MAIL_DEBUG"] = True

mail = Mail(app)

class Collections(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    artist = db.Column(db.String(200), unique=True, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    dimensions = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean)
    cart = db.Column(db.String, nullable=False)


class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.Length(min=8, max=30),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Go')


class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('New Password', [validators.Length(min=8, max=30)])
    submit = SubmitField('Go')


with app.app_context():
    db.create_all()



@app.route("/")
def landing():
    return redirect(url_for('home'))

@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        query = request.form["search-form"]
        if query != "":
            return redirect(url_for("search", query=query))
        else:
            return redirect(url_for("browse"))


    return render_template("index.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message:
            flash("All fields are required!")
            return redirect(url_for("contact"))

        try:
            msg = Message(
                subject=f"New Contact Form Submission from {name}",
                sender=email,
                recipients=["selene.contactus@gmail.com"],
                body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            )
            mail.send(msg)

            flash("Thank you for reaching out! Your message has been sent.")
            return redirect(url_for("contact"))
        except Exception:
            flash("An error occurred while sending your message. Please try again.")
            return redirect(url_for("contact"))


    return render_template("contact.html")


@app.route("/browse", methods=["GET", "POST"])
def browse():
    collections = db.session.execute(db.select(Collections)).scalars()

    user = None
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()

    if request.method == "POST":

        if list(request.form)[-1] == "search-button":
            query = request.form.get("search-form", "")
            if query != "":
                return redirect(url_for("search", query=query))
            else:
                return redirect(url_for("browse"))
        if list(request.form)[-1] == "add-file" and user and user.admin == 1:

            return redirect(url_for("adding_file"))


    return render_template("browse.html", collections=collections, user=user, query=request.form.get("search-form", ""))


@app.route("/adding_file", methods=["GET", "POST"])
def adding_file():
    if request.method == "POST":

        form_data = request.form

        title = form_data.get("title")
        artist = form_data.get("artist")
        date = form_data.get("date")
        dimensions = form_data.get("dimensions")
        price = form_data.get("price")
        image_file = request.files.get("image")

        if all([title, artist, date, dimensions, image_file, price]):
            # Check if the file is allowed
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                image_file.save(file_path)
                # Save relative path to the database
                image_src = os.path.join(filename)

                new_drawing = Collections(
                    title=title,
                    artist=artist,
                    date=date,
                    dimensions=dimensions,
                    image=image_src,
                    price=price
                )
                db.session.add(new_drawing)
                db.session.commit()

                return redirect(url_for("browse"))
            else:
                flash("Invalid image file format!")
        else:
            flash("All fields are required!")

    return render_template("adding_file.html")


@app.route("/search=<query>", methods=["GET", "POST"])
def search(query):
    user = None
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()

    collections = Collections.query.filter(Collections.title.like(f"%{query}%") | Collections.artist.like(f"%{query}%"))
    if request.method == "POST":
        query = request.form["search-form"]
        if query != "":
            return redirect(url_for("search", query=query))
        else:
            return redirect(url_for("browse"))
    return render_template("browse.html", collections=collections, user=user)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data
        user = db.session.execute(db.select(User).filter_by(username=username)).scalar()
        if user is None:
            flash("User Does Not Exist")
        elif not check_password_hash(user.password, password):
            flash("Incorrect Password")
        else:
            session["username"] = user.username
            session["email"] = user.email
            session["date"] = str(user.date)[:-9]
            session["admin"] = user.admin
            return redirect(url_for("home"))
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        email = form.email.data
        username = form.username.data
        password = form.password.data
        if db.session.execute(db.select(User).filter_by(username=username)).scalar() is not None:
            flash(f"Username Is Taken")
        elif db.session.execute(db.select(User).filter_by(email=email)).scalar() is not None:
            flash(f"Email Already In Use")
        else:
            user = User(email=email, username=username, password=generate_password_hash(password),
                        date=datetime.date.today(), admin=False, cart="")
            db.session.add(user)
            db.session.commit()
            flash(f"Registered!")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    flash("Logged Out")
    return redirect(url_for("login"))

@app.route("/browse/<album_title>/<album_id>", methods=["GET", "POST"])
def album(album_title, album_id):
    album_obj = db.session.execute(db.select(Collections).filter_by(id=album_id)).scalar()

    user = None
    show_edit_form = False

    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()

    if request.method == "POST":
        if list(request.form)[0] == "buy-album":
            if "username" in session:
                flash("Purchase Successful!")
            else:
                flash("Can't Purchase Without An Account!")
        if list(request.form)[0] == "add-album":
            if "username" in session:

                user = User.query.filter_by(username = session["username"]).first()
                if album_id not in user.cart.split(","):
                    flash("added Successfully!")
                    user.cart += album_id + ','

                else:
                    flash("already in the cart")

                db.session.commit()

            else:
                flash("Can't add to the cart Without An Account!")
        if list(request.form)[0] == "delete-album" and user.admin == 1:
            if "username" in session:
                user = User.query.filter_by(username = session["username"]).first()
                admin = user.admin
                print(admin)
                if admin == 1:
                    db.session.delete(album_obj)
                    db.session.commit()
                    return redirect(url_for('browse'))
                else:
                    flash("You do not have the required permissions to delete.")
        if list(request.form)[0] == "change-description" and user.admin == 1:
            show_edit_form = True
        if list(request.form)[-1] == "save-changes" and user and user.admin == 1:
            # Update album details in the database
            album_obj.title = request.form.get("title", album_obj.title)
            album_obj.price = request.form.get("price", album_obj.price)
            album_obj.artist = request.form.get("artist", album_obj.artist)
            album_obj.dimensions = request.form.get("dimensions", album_obj.dimensions)
            album_obj.date = request.form.get("date", album_obj.date)

            db.session.commit()
            flash("Changes saved successfully!")


    return render_template("album.html", collection=album_obj, user=user, show_edit_form=show_edit_form)

@app.route("/cart", methods=["GET", "POST"])
def cart():

    cart_obj = User.query.filter_by(username = session["username"]).first().cart[:-1].split(',')
    collections = db.session.query(Collections.image, Collections.title, Collections.artist, Collections.price, Collections.date,
                                   Collections.dimensions, Collections.id).filter(Collections.id.in_(cart_obj)).all()
    user = User.query.filter_by(username=session["username"]).first()

    if request.method == "POST":
        if list(request.form)[0] == "buy-album":
            if "username" in session:
                flash("Purchase Successful!")
            else:
                flash("Can't Purchase Without An Account!")
        if list(request.form)[0] == "remove-album":

            album_id = request.form.get("album_id")

            if album_id in cart_obj:
                cart_obj.remove(album_id)
                user.cart = ','.join(cart_obj) + ',' if cart_obj else ''
                db.session.commit()
                flash(f"Drawing: {request.form.get("album_title")} removed from the cart!")
                return redirect(url_for('cart'))
            else:
                flash("Album not found in the cart.")
        if list(request.form)[0] == "buy-all":
            user.cart = ""
            db.session.commit()
            flash(f"purchased all items in the cart successfully!")
            return redirect(url_for('cart'))
    total = 0
    for collection in collections:

        total += int("".join([ele for ele in collection.price if ele.isdigit()]))

    return render_template("cart.html", collections=collections, total=total)




if __name__ == "__main__":
    app.run(debug=True, port=8080)
