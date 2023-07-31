import pickle

import bcrypt
from flask import Flask, render_template, url_for, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Load the trained machine learning model from a pickle file
model = pickle.load(open('model.pkl', 'rb'))

# Set up database configuration
app.config['DEBUG'] = True
app.config['ENV'] = 'development'
app.config['FLASK_ENV'] = 'development'
app.config['SECRET_KEY'] = 'ItShouldBeALongStringOfRandomCharacters'

# Replace the connection details with your MySQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Root@localhost:3306/Loan_Prediction_App'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)
app.app_context().push()


# Create User model for storing registered users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    surname = db.Column(db.String(128))
    username = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(128))
    account_number = db.Column(db.String(128), unique=True)
    ifsc_code = db.Column(db.String(128))

    def __str__(self):
        return f"{self.username} has been registered successfully"


# Create the User table in the database if it doesn't exist
db.create_all()


# Home page for the application
@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


# Register new user details by inserting entries on DB
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("Register.html")

    elif request.method == 'POST':
        # Check if the username already exists in the database
        valid_username = User.query.filter(User.username == request.form.get('username')).first()

        if valid_username:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        else:
            # Hash and salt the user's password before storing it
            hashed_password = bcrypt.hashpw(request.form.get('password').encode('utf-8'), bcrypt.gensalt())

            # Create a new User object with all the form fields
            new_user = User(
                name=request.form.get('name'),
                surname=request.form.get('surname'),
                username=request.form.get('username'),
                password=hashed_password,
                account_number=request.form.get('account_number'),
                ifsc_code=request.form.get('ifsc_code')
            )

            db.session.add(new_user)
            db.session.commit()

            flash('User registered successfully', 'success')
            return redirect(url_for("register"))


# Login into the Loan Prediction application page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("Login.html")

    elif request.method == 'POST':
        # Retrieve the user from the database based on the provided username
        user = User.query.filter_by(username=request.form.get('username')).first()

        if user and bcrypt.checkpw(request.form.get('password').encode('utf-8'), user.password.encode('utf-8')):
            # Set session variables for user authentication
            session['logged_in'] = True
            session['username'] = request.form.get('username')
            return redirect(url_for("enter_details"))
        else:
            flash('Invalid Username or Password')
            return redirect(url_for('login'))


# Logout from Prediction page
@app.route('/logout')
def logout():
    # Clear the session variables for user logout
    session['logged_in'] = False
    session['username'] = ''
    return redirect(url_for('login'))


# Rendering Prediction page for getting user details
@app.route('/enter_details', methods=['GET'])
def enter_details():
    # Check if the user is logged in; if not, redirect to the login page
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template("predict.html", output=None)

# Predict function to read the values from the UI and predict the loan approval value.
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    # Check if the user is logged in; if not, redirect to the login page
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template("predict.html", output=None)

    elif request.method == 'POST':
        # Read user input values from the form
        Gender = request.form['Gender']
        Married = request.form['Married']
        Dependents = float(request.form['Dependents'])
        Education = request.form['Education']
        Self_employed = request.form['Self_employed']
        Applicant_Income = int(request.form['Applicant_Income'])
        Loan_Amount = float(request.form['Loan_Amount'])
        Loan_Amount_Term = float(request.form['Loan_Amount_Term'])
        Credit_History = float(request.form['Credit_History'])
        Property_Area = request.form['Property_Area']

        # Use the loaded model to predict loan eligibility
        prediction = model.predict([[Gender, Married, Dependents, Education, Self_employed, Applicant_Income,
                                     Loan_Amount, Loan_Amount_Term, Credit_History, Property_Area]])
        output = round(prediction[0], 1)

        # Render the prediction result
        return render_template('predict.html', prediction_text='', output=output)


if __name__ == "__main__":
    app.run(debug=True)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
