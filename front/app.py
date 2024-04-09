from flask import Flask, request, redirect, render_template, url_for, session
from flask_mysqldb import MySQL
from datetime import timedelta
from dotenv import load_dotenv
import os
import uuid
from flask_mail import Mail, Message


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('flask_app_key')  
app.config['SESSION_COOKIE_HTTPONLY'] = True # Set session cookies to be HTTPOnly
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS.
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1) 

app.config['MYSQL_HOST'] = os.getenv('db_host')
app.config['MYSQL_USER'] = os.getenv('db_user')
app.config['MYSQL_PASSWORD'] = os.getenv('db_password')
app.config['MYSQL_DB'] = os.getenv('db_database')
mysql = MySQL(app)

app.config['MAIL_SERVER'] = os.getenv('mail_host')
app.config['MAIL_PORT'] = os.getenv('mail_port')
#app.config['MAIL_USE_TLS'] = False
#app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT query_txt, times_used 
        FROM query_stats 
        ORDER BY times_used DESC 
        LIMIT 5
    """)
    query_results = cursor.fetchall()
    # Manually convert tuples to dictionaries
    top_queries = [{'query_txt': result[0], 'times_used': result[1]} for result in query_results]
    user_email = session.get('email')
    return render_template('home.html', user_email=user_email, top_queries=top_queries)



@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        session.permanent = True 
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT user_id, user_password, verified FROM app_users WHERE email = %s", [email])
        user = cursor.fetchone()
        if user:
            user_id, user_password, verified = user
            if user_password == password:
                if verified:
                    session['user_id'] = user_id  # Store user ID in session
                    session['email'] = email 
                    return redirect(url_for('home'))
                else:
                    message = "Your email address has not been verified. Please check your email to verify your account."
            else:
                message = "Invalid email or password"
        else:
            message = "Invalid email or password"
    
    return render_template('login.html', message=message)



@app.route('/logout')
def logout():
    session.clear()  # Clear the session, removing all stored data
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_email = request.form['email']
        user_password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT email FROM app_users WHERE email = %s", [user_email])
        existing_user = cursor.fetchone()

        if existing_user:
            return render_template('register.html', error="An account with this email already exists.")

        verification_code = str(uuid.uuid4())  # Generate a unique token

        # Proceed to insert the new user since the email does not exist
        cursor.execute("INSERT INTO app_users (email, user_password, verified, verification_code) VALUES (%s, %s, %s, %s)",
                       (user_email, user_password, False, verification_code))
        mysql.connection.commit()
        send_verification_email(user_email, verification_code)  # Send verification email

        return render_template('registration_success.html')
    return render_template('register.html')



@app.route('/verify_email/<token>')
def verify_email(token):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT email FROM app_users WHERE verification_code = %s", [token])
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE app_users SET verified = %s WHERE verification_code = %s", (True, token))
        mysql.connection.commit()
        return render_template('verification_success.html')
    else:
        return render_template('verification_error.html')



def send_verification_email(user_email, token):
    msg = Message('Verify Your Email', sender='no_reply@example.com', recipients=[user_email])
    link = url_for('verify_email', token=token, _external=True)
    msg.body = f'Please click on the link to verify your email: {link}'
    mail.send(msg)



if __name__ == '__main__':
    app.run(debug=True,  host='0.0.0.0', port=5000)