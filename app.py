from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from fire_base_config import *
from aws_config import *
from datetime import datetime
import base64
from sys import argv
from dotenv import load_dotenv
import os

load_dotenv() 

import uuid
# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a secret key

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#negotiation states
OFFER_ACC = "OFFER_ACCEPTED"
OFFER_REJ = "OFFER_REJECTED"
SELLER = "SELLER_OFFER"
BUYER = "BUYER_OFFER"
PAID = "PAYMENT_DONE"

def encode_email(email):
    # Encode the email using Base64
    encoded_email = base64.b64encode(email.encode())
    return encoded_email

def get_all_products():
    # Fetch all products from the database
    all_products_response = products_ref.get()
    all_products = all_products_response.val() if all_products_response.val() else {}
    if 'offers' in all_products:
        del all_products['offers']
    if 'users' in all_products:
        del all_products['users']
    # remove self products
    copy_of_all_products = all_products.copy()
    for key, val in all_products.items():
        if val.get('seller_email', '') == session['user_email']:
            del copy_of_all_products[key]
        elif val.get('sold', False):
            del copy_of_all_products[key]
    return copy_of_all_products

def get_all_products_dashboard(email):
    # Fetch all products from the database
    all_products_response = products_ref.get()
    all_products = all_products_response.val() if all_products_response.val() else {}
    if 'offers' in all_products:
        del all_products['offers']
    if 'users' in all_products:
        del all_products['users']
    # remove self products
    copy_of_all_products = all_products.copy()
    for key, val in all_products.items():
        if val.get('seller_email', '') != email:
            del copy_of_all_products[key]
    return copy_of_all_products

def decode_email(encoded_email):
    # Decode the Base64-encoded email
    decoded_email = base64.b64decode(encoded_email).decode('utf-8')
    return decoded_email

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Initialize the signup form
    class SignupForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Signup')
    try:
    # Get the form data
        form = SignupForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            # get .edu from email
            if '@' not in username:
                flash('Please enter a valid email address.', 'danger')
                return redirect(url_for('signup'))
            email = username.split('@')[1]
            if not email.endswith('.edu'):
                flash('Please use an .edu email address.', 'danger')
                return redirect(url_for('signup'))
            # Create the user
            try:
                user = auth.create_user_with_email_and_password(username, password)
                flash('You have been signed up.', 'success')
                return redirect(url_for('login'))
            except:
                flash('Invalid username or password.', 'danger')
                return redirect(url_for('signup'))
        return render_template('signup.html', form=form)
    except Exception as e:
        flash('Invalid username or password.', 'danger')
        return redirect(url_for('signup'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard

    
    if session.get('user_email', None):
        return redirect(url_for('home'))

    # Initialize the login form
    class LoginForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Login')

    # Get the form data
    form = LoginForm()
    if request.method == "GET":
        return render_template('login.html', form=form)
    username = form.username.data
    password = form.password.data

    # Authenticate the user
    try:
        user = auth.sign_in_with_email_and_password(username, password)
        session['user_email'] = username  # Store user email in session
        # if user.get('user_email', None):
        #     flash('You have been logged in.', 'success')
        #     
        return redirect(url_for('home'))
    except:
        flash('Invalid username or password.', 'danger')
        return redirect(url_for('login'))
    # Render the login page
    # return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    # If user is not logged in, redirect to login
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    # Fetch products posted by the current user
    current_user_email = session['user_email']
    
    required = get_all_products_dashboard(current_user_email)
    user_products = []
    for key, val in required.items():
        user_products.append({
            'name': val.get('name', ''),
            'description': val.get('description', ''),
            'images': val.get('images', ['']),
            'price': val.get('price', ''),
            'category': val.get('category', ''),
            'condition': val.get('condition', ''),
            'posted_at': val.get('posted_at', ''),
            'product_id': key
        })
        
    return render_template('dashboard.html', user_products=user_products)

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
        search_term = request.form.get('search_term', '').lower()
        selected_category = request.form.get('category', '')
        sort_order = request.form.get('sort', '')
        condition = request.form.get('condition', '')
        campus = request.form.get('campus', '')


        all_products = get_all_products()
        # Filter products
        filtered_products = []
        for key, val in all_products.items():
            if search_term in val.get('name', '').lower():
                if selected_category and val.get('category', '') != selected_category:
                    continue
                if condition and val.get('condition', '') != condition:
                    continue
                if campus == 'self_campus':
                    seller_email = val.get('seller_email', '')
                    if not seller_email:
                        continue
                    seller_campus = seller_email.split('@')[1].split('.')[0]
    
                    if seller_campus != session['user_email'].split('@')[1].split('.')[0]:
                        continue
                    
                filtered_products.append({
                    'name': val.get('name', ''),
                    'description': val.get('description', ''),
                    'image_link': val.get('images', [''])[0],
                    'price': val.get('price', ''),
                    'category': val.get('category', ''),
                    'condition': val.get('condition', ''),
                    'posted_at': val.get('posted_at', ''),
                    'product_id': key
                })

        # Sorting logic
        if sort_order == 'price_asc':
            filtered_products.sort(key=lambda x: float(x['price']))
        elif sort_order == 'price_desc':
            filtered_products.sort(key=lambda x: float(x['price']), reverse=True)
        elif sort_order == 'name_asc':
            filtered_products.sort(key=lambda x: x['name'].lower())
        elif sort_order == 'name_desc':
            filtered_products.sort(key=lambda x: x['name'].lower(), reverse=True)
        elif sort_order == 'date_asc':
            filtered_products.sort(key=lambda x: x['posted_at'])
        elif sort_order == 'date_desc':
            filtered_products.sort(key=lambda x: x['posted_at'], reverse=True)
        

        return render_template('home.html', products=filtered_products)

@app.route('/profile')
def profile():
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    user_email = session.get('user_email', None)
    if user_email:
        # If there's a user email in the session, pass it to the template
        profile_pic = db.child("users").child(encode_email(user_email)).child("profile_pic").get().val()
        if not profile_pic:
            profile_pic = 'static/images/Default_pfp.svg'
        phone = db.child("users").child(encode_email(user_email)).child("phone").get().val()
        if not phone:
            phone = ""
        name = db.child("users").child(encode_email(user_email)).child("name").get().val()
        if not name:
            name = ""
        qr_code_url = db.child("users").child(encode_email(user_email)).child("qr_code").get().val()
        if not qr_code_url:
            qr_code_url = ""
        return render_template('profile.html', user_email=user_email, profile_pic=profile_pic,  name=name, phone=phone, qr_code_url=qr_code_url)
    else:
        # If no user is logged in, redirect to login
        flash('Please log in to view this page.', 'warning')
        return redirect(url_for('login'))

# Route to update the profile picture
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    
    if 'profile_pic' not in request.files:
        return redirect(url_for('profile'))


    file = request.files['profile_pic']

    if file.filename == '':
        return redirect(url_for('profile'))
    
    if file:
        # Save the file locally
        user_email = session.get('user_email', None)
        filename = 'user_uploaded.jpg'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Upload the file to S3
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"

        # Upload the file to S3
        s3.upload_file(
            file_path, 
            s3_bucket_name, 
            unique_filename
            # ExtraArgs={'ACL': 'public-read'}  # Optional: Set ACL to public-read if you want the file to be publicly accessible
        )
        old_image = db.child("users").child(encode_email(user_email)).child("profile_pic").get().val()
        if old_image:
            object_key = old_image.split('/')[-1]
            s3.delete_object(Bucket=s3_bucket_name, Key=object_key)
        # Add the URL to the product data
        image_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{unique_filename}"
        os.remove(file_path)  # Remove the local file after uploading

        db.child("users").child(encode_email(user_email)).child("profile_pic").set(image_url)

        # Return the updated profile picture URL
        return redirect(url_for('profile'))    
    return redirect(url_for('profile'))

@app.route('/update_qr', methods=['POST'])
def update_qr():
        if not session.get('user_email', None):
            return redirect(url_for('login'))
        user_email = session.get('user_email', None)
    
        image = request.files['qr_code']
        if image:
            # Secure a filename and generate a unique one
            filename = secure_filename(image.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"

            # Upload the file to S3
            s3.upload_fileobj(
                image, 
                s3_bucket_name, 
                unique_filename
                # ExtraArgs={'ACL': 'public-read'}  # Optional: Set ACL to public-read if you want the file to be publicly accessible
            )

            # Add the URL to the product data
            image_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{unique_filename}"
            db.child("users").child(encode_email(user_email)).child("qr_code").set(image_url)
            return redirect(url_for('profile'))
        return redirect(url_for('profile'))

@app.route('/update_password', methods=['POST'])
def update_password():
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    # Get the user's current and new passwords from the request
    current_password = request.form.get('currentPassword')
    new_password = request.form.get('newPassword')
    try:
        # Authenticate the user
        user = auth.sign_in_with_email_and_password(session.get('user_email', None), current_password)

        # Change the user's password
        fba_auth.update_user(user['localId'], password=new_password)

        flash('Password updated successfully', 'success')
        return jsonify({'success': True, 'message': 'Password changed successfully'})

    except Exception as e:
        flash('Incorrect current password. Password update failed.', 'error')
        return jsonify({'success': False, 'error': 'Incorrect current password.'})


# Route to update the name
@app.route('/update_name', methods=['POST'])
def update_name():
    if not session.get('user_email', None):
        return redirect(url_for('login'))

    user_email = session.get('user_email', None)
    new_name = request.form.get('name')
    db.child("users").child(encode_email(user_email)).child("name").set(new_name)

    return redirect(url_for('profile'))

# Route to update the phone number
@app.route('/update_phone', methods=['POST'])
def update_phone():
    if not session.get('user_email', None):
        return redirect(url_for('login'))

    user_email = session.get('user_email', None)
    phone = request.form.get('phone')
    db.child("users").child(encode_email(user_email)).child("phone").set(phone)
    
    return redirect(url_for('profile'))


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
        if not session.get('user_email', None):
            return redirect(url_for('login'))
        user_email = session.get('user_email', None)
        product_data = {
            "name": request.form['product_name'],
            "description": request.form['product_description'],
            "price": request.form['product_price'],
            "images": request.form.getlist('product_image'),
            "category": request.form['product_category'],
            "condition": request.form['product_condition'],
            "seller_email": session['user_email'],
            "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        images = request.files.getlist('product_image')
        for image in images:
            if image:
                # Secure a filename and generate a unique one
                filename = secure_filename(image.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"

                # Upload the file to S3
                s3.upload_fileobj(
                    image, 
                    s3_bucket_name, 
                    unique_filename
                    # ExtraArgs={'ACL': 'public-read'}  # Optional: Set ACL to public-read if you want the file to be publicly accessible
                )

                # Add the URL to the product data
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

    product = get_product_by_id(product_id)
    if product['seller_email'] == session['user_email']:
        product['is_seller'] = True
    else:
        product['is_seller'] = False
    if product:
        return render_template('product_detail.html', product=product ,product_id=product_id, user_email=session['user_email'])
    else:
        flash('Product not found.', 'danger')
        return redirect(url_for('dashboard'))

def get_product_by_id(product_id):
    # Implement this function to fetch product data from the database
    # For example:
    return products_ref.child(product_id).get().val()

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

@app.route('/offers/negotiate/<product_id>', methods = ['POST'])
def negotiate(product_id):
    print(request.form.get('offer_price'))
    # Logic to support negotiation
    if not session.get('user_email'):
        return redirect(url_for('login'))
    user_email = session['user_email']
    product = products_ref.child(product_id).get()
    try: 
        seller_email = product.val()['seller_email']
        buyer_email = request.form.get('buyer_email')
        offer_status = ""
        if user_email == seller_email:
            offer_status = SELLER
        else:
            offer_status = BUYER
        offer_key = f"{product_id}_{encode_email(buyer_email)}"
        # Creating a dictionary representing the offer data
        offer_data = {
            'product_id': product_id,
            'seller_email': seller_email,
            'buyer_email': buyer_email,
            'timestamp': datetime.now().isoformat(),
            'offer_price': request.form.get('offer_price'),
            'offer_status': offer_status,
        }
        offer = db.child('offers').child(offer_key).get().val()
        if offer:
            if offer['offer_status'] == offer_status:
                flash('Not your turn to negotiate.', 'danger')
                return redirect(url_for('offers'))
            elif offer['offer_status'] == OFFER_ACC:
                flash('Offer already accepted.', 'danger')
                return redirect(url_for('offers'))
            elif offer['offer_status'] == OFFER_REJ:
                flash('Offer already rejected.', 'danger')
                return redirect(url_for('offers'))
        db.child('offers').child(offer_key).set(offer_data)
        return redirect(url_for('offers'))
    except Exception as e:
        print(e)
        flash('Product not found.', 'danger')
        return redirect(url_for('offers'))

@app.route('/offers/accept/<product_id>', methods = ['POST'])
def accept(product_id):
    # Logic to accepting offer
    if not session.get('user_email'):
        return redirect(url_for('login'))
    try: 
        # Fetching all offers
        buyer_email = request.form.get('buyer_email')
        product = db.child(product_id).get()
        print("product",product.val())
        seller_email = product.val()['seller_email']
        status = request.form.get('status')
        # meeting_location = request.form.get('meeting_location')
        offer_key = f"{product_id}_{encode_email(buyer_email)}"
        # if meeting_location=='' or meeting_location==None:
        #     try:
        #         meeting_location=db.child('offers').child(offer_key).get().val()['meeting_location']
        #     except:
        #         meeting_location="Meeting location not specified, please contact the seller: "+seller_email+" for more details."
            # print("meeting location",meeting_location)
        offer_entry = {
            'product_id': product_id,
            'seller_email': seller_email,
            'buyer_email': buyer_email,
            'timestamp': datetime.now().isoformat(),
            'offer_price': request.form.get('offer_price'),
            'offer_status': status,
            # 'meeting_location': meeting_location,
        }
        
        db.child('offers').child(offer_key).set(offer_entry)
        print("offer entry",offer_entry)
        # Updating offer_status to "rejected" for offers with the given product_id
        for offer_key, offer_data in db.child('offers').get().val().items():
            if offer_data['product_id'] == product_id:
                print("offer data",offer_data)
                if offer_data['buyer_email'] != buyer_email:
                    db.child('offers').child(offer_key).update({'offer_status': OFFER_REJ, 
                                                                'timestamp': datetime.now().isoformat()})
        if seller_email == session['user_email']:
            return redirect(url_for('offers'))
        else:
            return redirect(url_for('payment', seller_email=seller_email))
    except Exception as e:
        print("error opn 515", e)
        flash('Product not found.', 'danger')
        return redirect(url_for('offers'))

@app.route('/offers/reject/<product_id>', methods = ['POST'])
def reject(product_id):
    # Logic to rejecting offer
    if not session.get('user_email'):
        return redirect(url_for('login'))
    try: 
        # Fetching all offers
        buyer_email = request.form.get('buyer_email')
        offer_key = f"{product_id}_{encode_email(buyer_email)}"
        # Updating offer_status to "rejected" for offers with the given product_id
        db.child('offers').child(offer_key).update({'offer_status': OFFER_REJ, 
                                                    'timestamp': datetime.now().isoformat()})
        return redirect(url_for('offers'))
    except Exception as e:
        print(e)
        flash('Product not found.', 'danger')
        return redirect(url_for('offers'))
 
@app.route('/offers/paid/<product_id>', methods = ['POST'])
def paid(product_id):
    # Logic to ack payment
    if not session.get('user_email'):
        return redirect(url_for('login'))
    try: 
        # Fetching all offers
        buyer_email = request.form.get('buyer_email')
        offer_key = f"{product_id}_{encode_email(buyer_email)}"
        # Updating offer_status to "rejected" for offers with the given product_id
        offer = db.child('offers').child(offer_key).get().val()
        meeting_location = request.form.get('meeting_location')
        if offer['seller_email'] ==  session['user_email']:
            db.child('offers').child(offer_key).update({'offer_status': PAID,
                                                        'meeting_location': meeting_location,
                                                        'timestamp': datetime.now().isoformat()})
            products_ref.child(product_id).update({'sold': True})
        return redirect(url_for('offers'))
    except Exception as e:
        print(e)
        flash('Product not found.', 'danger')
        return redirect(url_for('offers'))
       
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
    offers = []
    for _, offer_data in db.child('offers').get().val().items():
        if offer_data['seller_email'] == user_email:
            offer_data['product'] = get_product_by_id(offer_data['product_id'])
            offers.append(offer_data)
    sorted_offers = sorted(offers, key=lambda x: x['timestamp'], reverse=True)
    return sorted_offers

def get_customer_offers(user_email):
    # Logic to get all offers where the current user is the customer
    offers = []
    for _, offer_data in db.child('offers').get().val().items():
        if offer_data['buyer_email'] == user_email:
            offer_data['product'] = get_product_by_id(offer_data['product_id'])
            offers.append(offer_data)
    sorted_offers = sorted(offers, key=lambda x: x['timestamp'], reverse=True)
    return sorted_offers


@app.route('/payment/<seller_email>')
def payment(seller_email):
    offer_id = request.args.get('offerId')
    # Fetch payment details for the offer using the offer_id
    # For example, get the seller's payment QR code information from the database
    payment_details = get_payment_details(offer_id)
    # get qr code url
    qr_code_url = db.child("users").child(encode_email(seller_email)).child("qr_code").get().val()
    return render_template('payment.html', payment_details=payment_details, qr_code_url=qr_code_url)

def get_payment_details(offer_id):
    # Implement this function to retrieve payment details from the database
    # For now, just returning a placeholder dictionary
    return {'qr_code_url': 'https://example.com/qr_code.png', 'offer_id': offer_id}


@app.route('/users/rate_seller/<seller_id>', methods = ['POST'])
def rate_seller(seller_id):
    if not session.get('user_email'):
        return redirect(url_for('login'))
    seller_id = encode_email(seller_id)
    rating = db.child('users').child(seller_id).get().val()
    if rating:
        rating['seller_rating'] = rating['seller_rating']*rating['seller_rating_count'] + int(request.form.get('rating'))
        rating['seller_rating_count'] += 1
        rating['seller_rating'] /= rating['seller_rating_count']
    else:
        rating = {
            'seller_rating' : int(request.form.get('rating')),
            'seller_rating_count' : 1,
            'buyer_rating' : 0,
            'buyer_rating_count' : 0,
        }
    db.child('users').child(seller_id).set(rating)
    return redirect(url_for('offers'))


@app.route('/users/rate_buyer/<buyer_id>', methods = ['POST'])
def rate_buyer(buyer_id):
    if not session.get('user_email'):
        return redirect(url_for('login'))
    buyer_id = encode_email(buyer_id)
    rating = db.child('users').child(buyer_id).get().val()
    if rating:
        rating['buyer_rating'] = rating['buyer_rating']*rating['buyer_rating_count'] + int(request.form.get('rating'))
        rating['buyer_rating_count'] += 1
        rating['buyer_rating'] /= rating['buyer_rating_count']
    else:
        rating = {
            'seller_rating' : 0,
            'seller_rating_count' : 0,
            'buyer_rating' : int(request.form.get('rating')),
            'buyer_rating_count' : 1,
        }
    db.child('users').child(buyer_id).set(rating)
    return redirect(url_for('offers'))

@app.route('/product/<product_id>/edit', methods=['GET'])
def edit_product(product_id):
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    
    product = get_product_by_id(product_id)
    if product:
        if request.method == "GET":
            return render_template('edit_product.html', product=product, product_id=product_id)
        
    else:
        flash('Product not found.', 'danger')
        return redirect(url_for('dashboard'))
    
@app.route('/product/edit', methods=['POST'])
def update_product():
    if not session.get('user_email', None):
        return redirect(url_for('login'))
    product_id = request.form['product_id']
    product = get_product_by_id(product_id)
    if product:
        if request.method == "POST":
            previous_images = list(request.form.getlist('previous_images')[0].split(',')) if request.form.getlist('previous_images') else []          
            product_data = {
                "name": request.form['product_name'],
                "description": request.form['product_description'],
                "price": request.form['product_price'],
                "images": previous_images,
                "category": request.form['product_category'],
                "condition": request.form['product_condition'],
                }
            new_images = request.files.getlist('product_image')
            for image in new_images:
                if image:
                    # Secure a filename and generate a unique one
                    filename = secure_filename(image.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    # Upload the file to S3
                    s3.upload_fileobj(
                        image, 
                        s3_bucket_name, 
                        unique_filename
                    )
                    # Add the URL to the product data
                    image_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{unique_filename}"
                    product_data["images"].append(image_url)
            if update_product_in_db(product_id, product_data):
                flash('Product updated successfully', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Error updating product', 'danger')
                return redirect(url_for('/product/edit'))
    else:
        flash('Product not found.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/delete_image', methods=['POST'])
def delete_image():
    data = request.get_json()
    image_url = data.get('image_url')
    return jsonify({'success': True})

def update_product_in_db(product_id, product_data):
    # Reference to the product
    product_ref = db.child(product_id)

    # Update the product each field in the product_ref dictionary 
    product_ref.update(product_data)

    return True

if __name__ == '__main__':
    # get port from args
    if len(argv) > 1:
        port = argv[1]
    else:
        port = 5000
    if port != 500:
        debug = False
    else:
        debug = True
    app.run(host='0.0.0.0', port=port, debug=debug)
