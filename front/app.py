from flask import Flask, request, redirect, render_template, url_for, session
from flask_mysqldb import MySQL
from datetime import timedelta
from dotenv import load_dotenv
import os

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
        cursor.execute("SELECT user_id, user_password FROM app_users WHERE email = %s", [email])
        user = cursor.fetchone()
        
        if user and user[1] == password:
            session['user_id'] = user[0]  # Store user ID in session
            session['email'] = email 
            return redirect(url_for('home'))
        else:
            message = "Invalid email or password"
    
    return render_template('login.html', message=message)


@app.route('/logout')
def logout():
    session.clear()  # Clear the session, removing all stored data
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True,  host='0.0.0.0', port=5000)