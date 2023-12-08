from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from fire_base_config import *
from aws_config import *
import uuid
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
    # If user is already logged in, redirect to dashboard
    if session.get('user_email', None):
        return redirect(url_for('dashboard'))

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
            if user.get('user_email', None):
                flash('You have been logged in.', 'success')
                return redirect(url_for('dashboard'))
        except:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

    # Render the login page
    return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    # If user is not logged in, redirect to login
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)  # Clear user email from session
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def home():
    # check if user is logged in
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    if request.method == "GET":
        return render_template('home.html')
    else:
        search_term = request.form.get('search_term')
        all_products_response = products_ref.get()

        # Convert PyreResponse to a dictionary
        all_products = all_products_response.val() if all_products_response.val() else {}

        # Filter products based on the search term
        filtered_products = [
            {'name': val.get('name', ''), 'description': val.get('description', ''), 'image_link': val.get('image_link', ''), 'price': val.get('price', '')}
            for key, val in all_products.items() if search_term.lower() in val.get('name', '').lower()
        ]

        return render_template('home.html', products=filtered_products)

@app.route('/profile')
def profile():
    if not session.get('user_email', None):
        return redirect(url_for('login'))
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
    
# @app.route('/post_product', methods=['POST'])
def process_and_post_product(request):
    try:
        product_data = {
            "name": request.form['product_name'],
            "description": request.form['product_description'],
            "price": request.form['product_price'],
            "images": []
        }

        images = request.files.getlist('product_images')
        for image in images:
            if image:
                filename = secure_filename(image.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                s3.upload_fileobj(image, s3_bucket_name, unique_filename)
                image_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{unique_filename}"
                product_data["images"].append(image_url)

        # Save product data to Firestore
        products_ref.push(product_data)

        return True
    except Exception as e:
        print(e)
        return False

@app.route('/product/post', methods=['POST', 'GET'])
def post_product():
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    if request.method == "GET":
        # create a form to post a product
        return render_template('post_product.html')
    elif request.method == "POST":
        if process_and_post_product(request):
            flash('Product posted successfully', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Error posting product', 'danger')
            return redirect(url_for('/product/post'))


@app.route('/product/<product_id>', methods=['GET'])
def get_product(product_id):
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    product = products_ref.child(product_id).get()
    if product:
        return jsonify(message="Product found", data=product)
    else:
        return jsonify(message="Product not found", data={}), 404
    
@app.route('/product/delete/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    products_ref.child(product_id).remove()
    return jsonify(message="Product deleted successfully", data={})

@app.route('/products', methods=['GET'])
def list_products():
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    products = products_ref.get()
    return jsonify(message="Products retrieved successfully", data=products)

@app.route('/offers')
def offers():
    if not session.get('user_email'):
        return redirect(url_for('login'))

    user_email = session['user_email']
    # Fetch offers for the logged-in seller from the database
    seller_offers = get_seller_offers(user_email)
    # Fetch offers made by the logged-in customer from the database
    customer_offers = get_customer_offers(user_email)

    return render_template('offers.html', seller_offers=seller_offers, customer_offers=customer_offers)

# Helper functions to fetch offers - implement these according to your database schema
def get_seller_offers(user_email):
    # Logic to get all offers where the current user is the seller
    return []

def get_customer_offers(user_email):
    # Logic to get all offers where the current user is the customer
    return []


@app.route('/payment')
def payment():
    offer_id = request.args.get('offerId')
    # Fetch payment details for the offer using the offer_id
    # For example, get the seller's payment QR code information from the database
    payment_details = get_payment_details(offer_id)
    return render_template('payment.html', payment_details=payment_details)

def get_payment_details(offer_id):
    # Implement this function to retrieve payment details from the database
    # For now, just returning a placeholder dictionary
    return {'qr_code_url': 'https://example.com/qr_code.png', 'offer_id': offer_id}



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
