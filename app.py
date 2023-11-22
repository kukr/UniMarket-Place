from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from fire_base_config import *

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a secret key

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Initialize the signup form
    class SignupForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Signup')

    # Get the form data
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Create the user
        try:
            user = auth.create_user_with_email_and_password(username, password)
            flash('You have been signed up.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('signup'))
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Initialize the login form
    class LoginForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Login')

    # Get the form data
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Authenticate the user
        try:
            user = auth.sign_in_with_email_and_password(username, password)
            session['user_email'] = username  # Store user email in session
            flash('You have been logged in.', 'success')
            return redirect(url_for('dashboard'))
        except:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

    # Render the login page
    return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)  # Clear user email from session
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "GET":
        return render_template('home.html')
    else:
        search_term = request.form.get('search_term')
        all_products = products_ref.get()
        # Filter products based on the search term
        print(all_products)
        print(all_products.val())
        filtered_products = {}
        if all_products.val():
            filtered_products = {key: val for key, val in all_products.items() if search_term.lower() in val.get('name', '').lower()}
        return render_template('home.html', products=filtered_products)

@app.route('/profile')
def profile():
    user_email = session.get('user_email', None)
    if user_email:
        # If there's a user email in the session, pass it to the template
        return render_template('profile.html', user_email=user_email)
    else:
        # If no user is logged in, redirect to login
        flash('Please log in to view this page.', 'warning')
        return redirect(url_for('login'))


@app.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    user = users_ref.child(user_id).get()
    if user:
        return jsonify(message="User found", data=user)
    else:
        return jsonify(message="User not found", data={}), 404

@app.route('/product/post', methods=['POST'])
def post_product():
    data = request.json
    result = products_ref.push(data)
    return jsonify(message="Product posted successfully", data=result)

@app.route('/product/<product_id>', methods=['GET'])
def get_product(product_id):
    product = products_ref.child(product_id).get()
    if product:
        return jsonify(message="Product found", data=product)
    else:
        return jsonify(message="Product not found", data={}), 404
    
@app.route('/product/delete/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    products_ref.child(product_id).remove()
    return jsonify(message="Product deleted successfully", data={})

@app.route('/products', methods=['GET'])
def list_products():
    products = products_ref.get()
    return jsonify(message="Products retrieved successfully", data=products)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
