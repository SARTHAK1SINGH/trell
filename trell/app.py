from flask import Flask,render_template,url_for,request,redirect, session, flash
import os
from io import StringIO
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta,date

## Admin user name = sundaram
## admin password = admin


app=Flask(__name__)

## using sqlite will upgrade to postgres if having time
## using flask-sqlalchemy for writing queries..

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trell3.db'
db = SQLAlchemy(app)


## defining models here

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(80), unique=True)
	password = db.Column(db.String(80))
	confirm = db.Column(db.String(80))

	def __init__(self, email, password, confirm):
		self.email = email
		self.password = password
		self.confirm = confirm

class Movies(db.Model):
	"""docstring for Movies"""
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=True) ## making film name unique to disallow repetition..
	description = db.Column(db.String(10000))
	director = db.Column(db.String(100), default ="Christopher Nolan")
	duration = db.column(db.String(20)) ## duration in hours

	def __repr__(self):
		return "<task %r> " % self.id

class Timing(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	timing = db.Column(db.String(80)) ## making film name unique to disallow repetition..
	price = db.Column(db.String(1000))
	tickets = db.Column(db.String(1000))
	movieid = db.Column(db.Integer)
	
	def __repr__(self):
		return "<task %r> " % self.id


db.create_all()

app.secret_key = "Remember Red, hope is a good thing maybe the best of the things and no good thing ever dies"
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


### admin login
@app.route("/admin-login", methods=["GET", "POST"])
def Admin():
	if request.method == "POST":
		if request.form["username"] == "sundaram" and request.form["password"] == "admin":
			session["admin"] = True
			return redirect("/") 
		else:
			return "you are not admin/ you are not authorized to access this area", 403
	else:
		return render_template("adminLogin.html")


## user sign up
@app.route("/signup", methods=["GET", "POST"])
def Signup():
	if request.method == 'POST':
		new_user = User(
		email=request.form['email'],
		password=request.form['password'],
		confirm = request.form["passwordConfirm"])
		if(request.form['password'] != request.form['passwordConfirm']):
			flash('password and confirm password should be same')
			return redirect(url_for('Signup'))
		try:
			db.session.add(new_user)
			db.session.commit()
			return render_template('login.html') ## redirecting to login after signup, can redirect on main page too
		except:
			##handling case if email is already present in database
			flash = "email is already registered their.."
			return redirect(url_for('Signup'))
	return render_template('signup.html')


@app.route("/login", methods =["GET", "POST"])
def Login():
	if request.method == 'GET':
		return render_template('login.html')
	else:
		email = request.form['email']
		passw = request.form['password']
		try:
			session["user_email"] = email
			data = db.session.query(User).filter_by(email=email, password=passw).first()
			#db.session.commit()
			if data is not None:
				session['logged_in'] = True
				return redirect(url_for('index'))
			else:
				return "either wrong credentials or you are not signed up.."
		except:
			return render_template('login.html')


@app.route("/", methods=["GET", "POST"])
def index():
	if(request.method == "GET"):
		if(session["logged_in"] or session["admin"]):
			movieList = db.session.query(Movies).all()
			db.session.commit()
			return render_template("index.html", movieList = movieList)
		else:
			first_user = db.session.query(User).all()
			if(not first_user):
				return redirect("/signup")
			return redirect("/login")
	else:
		## show result for query
		value = request.form["searchKeyword"]
		if value == "" or value is None:
			movieList = db.session.query(Movies).all()
			db.session.commit()
			return render_template("index.html", movieList = movieList)
		movieList = db.session.query(Movies).filter_by(name=value).all()
		db.session.commit()
		return render_template("index.html", movieList = movieList, movieName = value)


@app.route("/add-movie", methods= ["POST", "GET"])
def addMovie():
	if(request.method == "POST"):
		movieName = request.form["title"]
		description = request.form["description"]
		duration = request.form["duration"]
		#duration = str(duration)
		director = request.form["director"]
		new_movie = Movies(
			name = movieName,
			description = description,
			duration = duration,
			director = director
		)
		try:
			db.session.add(new_movie)
			db.session.commit()

			flash = "Movie added successfully"
			return redirect("/")
		except:
			flash = "there was an error in adding movie, we are looking into it"
			return render_template("addMovie.html")
	else:
		if(session["logged_in"] or session["admin"]):
			return render_template("addMovie.html")
		else:
			return redirect("/login")


@app.route("/add-timing/<int:id>", methods=["GET", "POST"])
def addTiming(id):
	if(request.method == "GET"):
		all_timings = db.session.query(Timing).filter_by(movieid=id).all()
		return render_template("addtiming.html", id = id, all_timings = all_timings, available_tickets=10, purchased_tickets=2)
	else:
		timing = request.form["timing"]
		price = request.form["price"]
		tickets = request.form["tickets"]
		movieid = id
		new_timing = Timing(timing = timing, price=price, tickets=tickets, movieid = movieid)
		try:
			db.session.add(new_timing)
			db.session.commit()
			return redirect("/")
		except:
			flash = "error is there!!"
			return render_template("addtiming.html", id = id)


@app.route("/purchase-ticket/<int:id>", methods = ["GET", "POST"])
def purchase(id):
	if(request.method == "POST"):
		timing_val = db.session.query(Timing).filter_by(id = id).first()
		number_of_ticket = request.form["tickets"]
		prev_tickets = timing_val.tickets
		if(int(number_of_ticket) > int(prev_tickets)):
			return render_template("purchaseTicket.html", id=id)
		timing_val.tickets = str(int(prev_tickets) - int(number_of_ticket))
		db.session.commit()
		flash = "you bought a ticket"
		return redirect("/")
	else:
		return render_template("purchaseTicket.html", id=id)


@app.route("/logout")
def logout():
	session['logged_in'] = False
	session["admin"] = False
	##session["teacher_logged_in"] = False
	return redirect(url_for('index'))




if __name__=='__main__':
	app.run(debug=True)
