from flask import Flask, jsonify, request, render_template, flash, redirect, url_for, session, logging, current_app
from random import randint
import os
import secrets
from flask_mysqldb import MySQL
from wtforms import Form, StringField, IntegerField, TextAreaField, PasswordField, SelectField, validators
from wtforms.fields.html5 import EmailField
import numpy as np
import pickle


from functools import wraps

app = Flask(__name__)

app.secret_key = 'many random bytes'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'project_1'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


####################################~~~~~ACCESS RESTRICTION DECORATORS BEGIN~~~~~##########################################
###########################################################################################################################


#~~~~~~~~~~~~~~~~ TO CHECK IF USER IS LOGGED IN

def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please Login','danger')
			return redirect(url_for('pat_login'))
	return wrap
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~ TO CHECK IF USER IS A PATIENT
def is_patient(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		cur = mysql.connection.cursor()
		result = cur.execute("SELECT role,pat_id From pat_info where username LIKE %s",[session['username']])
		pat = cur.fetchone()
		cur.close() 
		print(pat)
		if pat['role'] == 'Patient':
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please check user access','danger')
			return redirect(url_for('pat_login'))
	return wrap
	

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~ TO CHECK IF USER IS A DOCTOR

def is_emp(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		print(session['username'])
		cur = mysql.connection.cursor()
		result = cur.execute("SELECT * From emp_info where username LIKE %s",[session['username']])
		art = cur.fetchone()
		cur.close() 
		print(art)
		if art['role'] in ["Regular Physician","Junior Doctor","Senior Doctor","System Admin"]:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please check user access','danger')
			return redirect(url_for('emp_login'))
	return wrap

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# #~~~~~~~~~~~~~~~~~ TO CHECK USER IS AN EXPERT/EXECUTIVE

# def is_expert(f):
# 	@wraps(f)
# 	def wrap(*args, **kwargs):
# 		print(session['username'])
# 		cur = mysql.connection.cursor()
# 		result = cur.execute("SELECT * From emp_info where username LIKE %s",[session['username']])
# 		art = cur.fetchone()
# 		cur.close() 
# 		print(art)
# 		if art['Role'] == 'Expert':
# 			return f(*args, **kwargs)
# 		else:
# 			flash('Unauthorized, Please check user access','danger')
# 			return redirect(url_for('login'))
# 	return wrap

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# #~~~~~~~~~~~~~~~~ TO CHECK USER IS AN ADMINISTRATOR

# def is_admin(f):
# 	@wraps(f)
# 	def wrap(*args, **kwargs):
# 		print(session['username'])
# 		cur = mysql.connection.cursor()
# 		result = cur.execute("SELECT * From emp_info where username LIKE %s",[session['username']])
# 		art = cur.fetchone()
# 		cur.close() 
# 		print(art)
# 		if art['Role'] == 'Admin':
# 			return f(*args, **kwargs)
# 		else:
# 			flash('Unauthorized, Please check user access','danger')
# 			return redirect(url_for('login'))
# 	return wrap

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


####################################~~~~~ACCESS RESTRICTION DECORATORS END~~~~~############################################
###########################################################################################################################

####################################~~~~~~~VIEWS AND TEMPLATES (non logged in)~~~~~~~~#####################################
###########################################################################################################################



model = pickle.load(open('model.pkl', 'rb'))


@app.route('/predict',methods=['POST'])
def predict():
    '''
    For rendering results on HTML GUI
    '''
    int_features = [int(x) for x in request.form.values()]
    final_features = [np.array(int_features)]
    prediction = model.predict(final_features)

    output = prediction[0]
    if output == 0:
    	prediction_text = ('You are not diagnosed with any specific disease')
    elif output == 1:
    	prediction_text = ('You have been diagnosed for a disease of category BD01')
    elif output == 2:
    	prediction_text = ('You have been diagnosed for a disease of category BD02') 
    elif output == 3:
    	prediction_text = ('You have been diagnosed for a disease of category BD03') 
    else:
    	prediction_text = ('You have been diagnosed for a disease of category BD04') 

   

    return render_template('home.html', prediction_text=prediction_text)





@app.route('/')
def home():
	return render_template('home.html')

def save_images(photo):
	hash_photo = secrets.token_urlsafe(10)
	_, file_extension = os.path.splitext(photo.filename)
	photo_name = hash_photo + file_extension
	file_path = os.path.join(current_app.root_path, 'static/images', photo_name)
	photo.save(file_path)
	return photo_name



class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	age = IntegerField('Age', [validators.DataRequired()])
	gender = StringField('Gender', [validators.Length(min=1, max=15)])
	email = EmailField('Email', [validators.Length(min=10, max=50), validators.Email()])
	city = StringField('City', [validators.Length(min=3, max=30)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message="Passwords do not match")])
	confirm = PasswordField('Confirm Password')
	sec_ques = SelectField(u'Secret Question', choices=[('Name of your Favorite Animal','Name of your Favorite Animal'),('Name of your Favorite Movie','Name of your Favorite Movie'),('Name of your Favorite Athlete','Name of your Favorite Athlete'),('Name of your Favorite Book','Name of your Favorite Book')])
	sec_ans = StringField('Secret Answer', [validators.Length(min=2, max=50)])

@app.route('/register', methods=["GET","POST"])
def register():
	p = "P"+str(randint(10000,99999))+"20"

	form = RegisterForm(request.form)
	if request.method == "POST":
		
		name = form.name.data
		age = str(form.age.data)
		gender = form.gender.data
		email = form.email.data
		city = form.city.data
		username = form.username.data
		password = form.password.data
		sec_ques = form.sec_ques.data
		sec_ans = form.sec_ans.data
		
		role= "Patient"
		wallet_id = "W"
		pic = "  "
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO pat_info (pat_id, name, age, gender, pic, email, city, username, password, role, wallet_id, sec_ques, sec_ans) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (p, name, age, gender, pic, email, city, username, password, role, wallet_id, sec_ques, sec_ans))
		mysql.connection.commit()
		cur.close()
		flash('You are now registered', 'success')        

		return url_for('pat_login')
	return render_template('register.html', form=form, p=p)	


@app.route('/pat_login', methods=["GET","POST"])
def pat_login():
	if request.method == "POST":
		username = request.form['username']
		password_c = request.form['password']

		cur = mysql.connection.cursor()
		result = cur.execute("SELECT * FROM pat_info where username LIKE %s", [username])
		
		if result > 0:
			data = cur.fetchone()
			password = data['password']


			if password_c == password:
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in', 'success')
				return redirect(url_for('pat_dashboard'))

			else:
				error = "Invalid Login"
				return render_template('pat_login.html', error=error)

			cur.close()
		else:
			error = "Username not found"
			return render_template('pat_login.html', error=error)
	return render_template('pat_login.html')

@app.route('/pat_dashboard')
@is_logged_in
@is_patient
def pat_dashboard():
	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM pat_info where username LIKE %s", (session['username'], ))
	user_info = cur.fetchall()


	result2 = cur.execute("SELECT * FROM pat_hist WHERE username LIKE %s", (session['username'], ))
	user_hist = cur.fetchall()

	result3 = cur.execute("SELECT * FROM pat_medi WHERE username LIKE %s", (session['username'], ))
	user_medi = cur.fetchall()

	result4 = cur.execute("SELECT * FROM pat_wallet WHERE username LIKE %s", (session['username'], ))
	user_wallet = cur.fetchall()

	result5 = cur.execute("SELECT * FROM wallet_trans")
	user_trans = cur.fetchall()

 
	
	if result > 0:
		return render_template('pat_dashboard.html', user_info=user_info, user_medi=user_medi, user_hist=user_hist, user_wallet=user_wallet, user_trans=user_trans)
	else:
		msg = 'No articles Found'
		return render_template('pat_dashboard.html', msg = msg)
	cur.close()



@app.route('/upload_new_pat_pic', methods=["GET","POST"])
@is_logged_in
@is_patient
def upload_new_pat_pic():
	if request.method == "POST":
	    flash("Picture uploaded Successfully")
	    pat_id = request.form['pat_id']
	    pic = save_images(request.files['pic'])
	    cur = mysql.connection.cursor()
	    cur.execute("UPDATE pat_info SET pic=%s WHERE pat_id=%s", (pic, pat_id))
	    mysql.connection.commit()
	    cur.close()
	    return redirect(url_for('pat_dashboard'))
	return render_template('pat_dashboard.html')
	   


@app.route('/remove_pat_pic', methods = ['GET','POST'])
@is_logged_in
@is_patient
def remove_pat_pic():
	if request.method == "POST":
	    flash("Picture removed Successfully")
	    pat_id = request.form['pat_id']
	    pic = "default.png"
	    cur = mysql.connection.cursor()
	    cur.execute("UPDATE pat_info SET pic=%s WHERE pat_id=%s", (pic, pat_id))
	    mysql.connection.commit()
	    cur.close()
	    return redirect(url_for('pat_dashboard'))
	return render_template('pat_dashboard.html')
	   
@app.route('/setup_wallet', methods = ["GET","POST"])
@is_logged_in
@is_patient
def setup_wallet():
	wall = "W"+str(randint(1000,9999))+"20"

	if request.method == "POST":

		pat_id = request.form['pat_id']
		amount = request.form['amount']
		payment_type = "recharge"
		one = int("1")
		uname= session["username"]

		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO pat_wallet (pat_id,username, wallet_id, amount) VALUES (%s, %s, %s, %s)", (pat_id,uname, wall, amount))

		cur.execute("INSERT INTO wallet_trans (wallet_id, amount, payment_type, rec_emp_id) VALUES (%s, %s, %s, %s)", (wall, amount, payment_type, one))


		cur.execute("UPDATE pat_info SET wallet_id = %s WHERE pat_id = %s", (wall, pat_id))

		mysql.connection.commit()
		cur.close()

		return redirect(url_for('pat_dashboard'))

	return render_template('pat_dashboard.html')

@app.route('/recharge_wallet', methods = ["GET","POST"])
@is_logged_in
@is_patient
def recharge_wallet():
	if request.method == "POST":
		wallet_id = request.form['wallet_id']
		pat_id = request.form['pat_id']
		new_amount = request.form['amount']
		payment_type = "recharge"
		one = int("1")
		uname= session["username"]

		cur = mysql.connection.cursor()
		cur.execute("UPDATE pat_wallet SET amount=amount+%s WHERE pat_id=%s", (new_amount, pat_id))

		cur.execute("INSERT INTO wallet_trans (wallet_id, amount, payment_type, rec_emp_id) VALUES (%s, %s, %s, %s)", (wallet_id, new_amount, payment_type, one))

		mysql.connection.commit()
		cur.close()

		return redirect(url_for('pat_dashboard'))

@app.route('/all_transactions')



@app.route('/add_new_disease', methods = ['GET','POST'])
@is_logged_in
@is_patient
def add_new_disease():
	if request.method == "POST":
	    flash("Picture removed Successfully")
	    pat_id = request.form['pat_id']
	    ailment = request.form['ailment']
	    status = request.form['status']
	    uname = session["username"]
       
	    cur = mysql.connection.cursor()
	    cur.execute("INSERT into pat_hist (pat_id,username,ailment,status) VALUES (%s, %s, %s, %s)", (pat_id, uname, ailment, status))
	    mysql.connection.commit()
	    cur.close()
	    return redirect(url_for('pat_dashboard'))
	return render_template('pat_dashboard.html')


@app.route('/edit_disease', methods = ['GET','POST'])
@is_logged_in
@is_patient
def edit_disease():
	if request.method == "POST":
	    flash("Picture removed Successfully")
	    pat_id = request.form['pat_id']
	    ailment = request.form['ailment']
	    status = request.form['status']
	    uname = session["username"]
	    ail_id = int(request.form['id'])
	    cur = mysql.connection.cursor()
	    cur.execute("UPDATE pat_hist SET ailment = %s,status = %s WHERE id = %s", (ailment, status, ail_id))
	    mysql.connection.commit()
	    cur.close()
	    return redirect(url_for('pat_dashboard'))
	return render_template('pat_dashboard.html')


@app.route('/delete_disease/<string:id_data>', methods = ['GET'])
@is_logged_in
@is_patient
def delete_disease(id_data):
    flash("Disease Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM pat_hist WHERE id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('pat_dashboard'))
    cur.close()

@app.route('/add_new_prescription', methods = ['GET','POST'])
@is_logged_in
@is_patient
def add_new_prescription():
	if request.method == "POST":
	    flash("Prescription Added Successfully")
	    pat_id = request.form['pat_id']
	    medi_name = request.form['medi_name']
	    medi_dose = int(request.form['medi_dose'])
	    status = request.form['status']
	    uname = session["username"]
       
	    cur = mysql.connection.cursor()
	    cur.execute("INSERT into pat_medi (pat_id,username,medi_name,medi_dose,status) VALUES (%s, %s, %s, %s, %s)", (pat_id, uname, medi_name, medi_dose, status))
	    mysql.connection.commit()
	    cur.close()
	    return redirect(url_for('pat_dashboard'))
	return render_template('pat_dashboard.html')



@app.route('/edit_prescription', methods = ['GET','POST'])
@is_logged_in
@is_patient
def edit_prescription():
	if request.method == "POST":
	    flash("Picture removed Successfully")
	    pat_id = request.form['pat_id']
	    medi_name = request.form['medi_name']
	    medi_dose = int(request.form['medi_dose'])
	    status = request.form['status']
	    uname = session["username"]
	    medi_id = int(request.form['id'])
	    cur = mysql.connection.cursor()
	    cur.execute("UPDATE pat_medi SET medi_name = %s, medi_dose = %s, status = %s WHERE id = %s", (medi_name, medi_dose, status, medi_id))
	    mysql.connection.commit()
	    cur.close()
	    return redirect(url_for('pat_dashboard'))
	return render_template('pat_dashboard.html')


@app.route('/delete_prescription/<string:id_data>', methods = ['GET'])
@is_logged_in
@is_patient
def delete_prescription(id_data):
    flash("Prescription Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM pat_medi WHERE id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('pat_dashboard'))
    cur.close()



@app.route('/emp_dashboard')
def emp_dashboard():
	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM emp_info where username LIKE %s", (session['username'], ))
	user_info = cur.fetchall()

	if result > 0:
		return render_template('emp_dashboard.html', user_info=user_info)
	else:
		msg = 'No articles Found'
		return render_template('emp_dashboard.html', msg = msg)
	cur.close()





#LOGOUT 
@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out','success')
	return redirect(url_for('index'))


@app.route('/emp_login', methods=["GET","POST"])
def emp_login():
	if request.method == "POST":
		username = request.form['username']
		password_c = request.form['password']

		cur = mysql.connection.cursor()
		result = cur.execute("SELECT * FROM emp_info where username LIKE %s", [username])
		
		if result > 0:
			data = cur.fetchone()
			password = data['password']


			if password_c == password:
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in', 'success')
				if data['role'] in ["Regular Physician","Junior Doctor","Senior Doctor","System Admin"]:
					return redirect(url_for('emp_dashboard'))	
				else:
					return redirect(url_for('emp_login'))

			else:
				error = "Invalid Login"
				return render_template('emp_login.html', error=error)

			cur.close()
		else:
			error = "Username not found"
			return render_template('emp_login.html', error=error)
	return render_template('emp_login.html')


@app.route('/upload_new_emp_pic', methods=["GET","POST"])
@is_logged_in
@is_emp
def upload_new_emp_pic():
	if request.method == "POST":
	    flash("Picture uploaded Successfully")
	    emp_id = request.form['emp_id']
	    pic = save_images(request.files['pic'])
	    cur = mysql.connection.cursor()
	    cur.execute("UPDATE emp_info SET pic=%s WHERE emp_id=%s", (pic, emp_id))
	    mysql.connection.commit()
	    cur.close()
	    return redirect(url_for('emp_dashboard'))
	return render_template('emp_dashboard.html')
	   

@app.route('/remove_emp_pic', methods = ['GET','POST'])
@is_logged_in
@is_emp
def remove_emp_pic():
	if request.method == "POST":
	    flash("Picture removed Successfully")
	    emp_id = request.form['emp_id']
	    pic = "default.png"
	    cur = mysql.connection.cursor()
	    cur.execute("UPDATE emp_info SET pic=%s WHERE emp_id=%s", (pic, emp_id))
	    mysql.connection.commit()
	    cur.close()
	    return redirect(url_for('emp_dashboard'))
	return render_template('emp_dashboard.html')
	
@app.route('/upload_new_emp_work_pic', methods=["GET","POST"])
def upload_new_emp_work_pic():
	if request.method == "POST":
	    flash("Picture uploaded Successfully")
	    emp_id = request.form['emp_id']
	    work_pic = save_images(request.files['work_pic'])
	    cur = mysql.connection.cursor()
	    cur.execute("UPDATE emp_info SET work_pic=%s WHERE emp_id=%s", (work_pic, emp_id))
	    mysql.connection.commit()
	    cur.close()
	    return redirect(url_for('emp_dashboard'))
	return render_template('emp_dashboard.html')
	

@app.route('/remove_emp_work_pic', methods = ['GET','POST'])
@is_logged_in
@is_emp
def remove_emp_work_pic():
	if request.method == "POST":
	    flash("Picture removed Successfully")
	    emp_id = request.form['emp_id']
	    work_pic = "default_wrok.png"
	    cur = mysql.connection.cursor()
	    cur.execute("UPDATE emp_info SET work_pic=%s WHERE emp_id=%s", (work_pic, emp_id))
	    mysql.connection.commit()
	    cur.close()
	    return redirect(url_for('emp_dashboard'))
	return render_template('emp_dashboard.html')

@app.route('/admin_career')
@is_logged_in
@is_emp
def admin_career():
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM job_posting")
	jobs = cur.fetchall()
	print(jobs)
	if result > 0:
		return render_template('admin_career.html', jobs=jobs)
	cur.close()

	return render_template('admin_career.html')




@app.route('/add_job',methods=["GET","POST"])
def add_job():
	if request.method == "POST":
		flash("Job Posted Inserted Successfully")
		role = request.form['role']
		field = request.form['field']
		min_exp = int(request.form['min_exp'])
		openings = int(request.form['openings'])
		description = request.form['descrip']
		
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO job_posting (role, field, min_exp, openings, descrip) VALUES (%s, %s, %s, %s, %s)", (role, field, min_exp, openings, description))
		mysql.connection.commit()
		cur.close()
		return redirect(url_for('admin_career'))
	return render_template('admin_career.html')

@app.route('/careers')
def careers():		
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM job_posting")
	jobs = cur.fetchall()

	if result > 0:
		return render_template('careers.html', jobs=jobs)
	cur.close()
	return render_template('careers.html')


@app.route('/apply_job',methods=["POST","GET"])
def apply_job():
	if request.method == "POST":
		flash("Applied to job Successfully")
		job_id = int(request.form['job_id'])
		name = request.form['name']
		age = int(request.form['age'])
		gender = request.form['gender']
		email = request.form['email']
		username = request.form['username']
		password = request.form['password']
		role = request.form['role']
		field = request.form['field']
		exp = int(request.form['exp'])
		work_location = request.form['work_location']
		city = request.form['city']
		alm_mat = request.form['alm_mat']
		sec_ques = request.form['sec_ques']
		sec_ans = request.form['sec_ans']
		approval_1 = "Pending"
		approval_2 = "Pending"
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO job_appn (job_id, name , age, gender, email, username, password, role, field, exp, work_location, city, alm_mat, sec_ques, sec_ans, approval_1, approval_2) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (job_id, name , age, gender, email, username, password, role, field, exp, work_location, city, alm_mat, sec_ques, sec_ans, approval_1, approval_2))
		mysql.connection.commit()
		cur.close()
		return redirect(url_for('careers'))
	return render_template('careers.html')

@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM job_posting WHERE id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('admin_career'))

@app.route('/jobappn/<string:id>/')
def jobappn(id):
	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM job_appn WHERE job_id = %s", [id])
	appns = cur.fetchall()

	return render_template('jobappn.html', appns=appns)

@app.route('/transactions')
@is_logged_in
@is_emp
def transactions():
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT a.id, a.wallet_id, a.amount, c.name, a.payment_type, a.payment_time, b.role FROM `wallet_trans` AS a INNER JOIN `emp_info` AS b ON a.rec_emp_id = b.emp_id INNER JOIN `pat_info` AS c ON a.wallet_id = c.wallet_id")
	trans = cur.fetchall()
	
	if result > 0:
		return render_template('transactions.html', trans=trans)
	cur.close()

	return render_template('transactions.html')


if __name__ == "__main__":
	app.run(debug=True)

