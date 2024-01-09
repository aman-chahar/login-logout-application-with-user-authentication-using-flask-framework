from flask import Flask, render_template, url_for, request, redirect, session, g
from database import get_database
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

def get_current_user():
    user = None
    if "user" in session:
        user = session['user']
        db = get_database()
        user_cursor = db.execute("select * from users where username = ?", [user])
        user = user_cursor.fetchone()
    return user

@app.teardown_appcontext
def close_database(error):
    if hasattr(g, "employee_db"):
        g.employee_db.close()

@app.route("/")
@app.route("/home")
def home():
    user = get_current_user()
    return render_template("home.html", user = user)


@app.route("/login", methods = ["POST", "GET"])
def login():
    user = get_current_user()
    error = None
    if request.method == "POST":
        #collect the information from the html form.
        username = request.form['username']
        user_entered_password = request.form['password']
        #connect to database
        db = get_database()
        #sql query to insert these two values inside database table
        user_cursor = db.execute("select * from users where username = ?", [username])
        
        user = user_cursor.fetchone()

        if user:
            if check_password_hash(user['password'], user_entered_password):
                session['user'] = user['username']
                return redirect(url_for("home"))
            else:
                error = "Password did not match."    
    return render_template("login.html", loginerror = error, user = user)

@app.route("/register", methods = ["POST", "GET"])
def register():
    user = get_current_user()
    register_error = None
    if request.method == "POST":
        #collect the information from the html form.
        username = request.form['username']
        password = request.form['password']

        #generate a hashcode for the password entered by the user
        hashed_password = generate_password_hash(password)

        #connect to database
        db = get_database()

        #checking for duplicate username in the database
        user_cursor = db.execute("select * from users where username = ?", [username])
        existing_user = user_cursor.fetchone()

        if existing_user:
            register_error = "Username is already taken, please select a diffrent username."
            return render_template("register.html", register_error = register_error)
        #sql query to insert these two values inside database table
        db.execute("insert into users (username, password, admin) values (?,?,?)", [username, hashed_password, '0'])
        #make all the changes permanent
        db.commit()
        return redirect(url_for("login"))
    return render_template("register.html", user = user)  

@app.route("/promote")
def promote():
    user = get_current_user()
    db = get_database()
    allusers_cursor = db.execute("select * from users")
    all_employees = allusers_cursor.fetchall()
    return render_template("promote.html", user = user, all_employees = all_employees)

@app.route("/promotetoadmin/<int:empid>")
def promotetoadmin(empid):
    db = get_database()
    db.execute("update users set admin = 1 where id = ?", [empid])
    db.commit()
    return redirect(url_for("promote"))

@app.route("/deleteuser/<int:empid>")
def deleteuser(empid):
    db = get_database()
    db.execute("delete from users where id = ?", [empid])
    db.commit()
    return redirect(url_for("promote"))
    

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for("home"))

if __name__=="__main__":
    app.run(debug = True)