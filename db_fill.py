from faker import Faker
import random
from fire_base_config import *

fake = Faker()
# Function to create fake users
def create_fake_users(n):
    for _ in range(n):
        user_data = {
            'email': fake.email(),
            'password': fake.password(length=10)  # Simple text password, not recommended for real applications
        }
        users_ref.push(user_data)

# Function to create fake products
def create_fake_products(n, user_emails):
    for _ in range(n):
        product_data = {
            'seller_email': random.choice(user_emails),  # Linking product to user via email
            'name': fake.catch_phrase(),
            'description': fake.text(max_nb_chars=200),
            'price': round(random.uniform(10, 1000), 2),
            'category': fake.random_choice(elements=('electronics', 'furniture', 'clothing', 'books', 'others')),
            'condition': fake.random_choice(elements=('new', 'used', 'refurbished')),
            'posted_at': fake.date_time_this_year().isoformat(),
            'image_link': fake.image_url()  # Link to a random image
        }
        products_ref.push(product_data)

# Generate and populate data
# user_count = 100
product_count = 10

# Create fake users and collect their emails
fake_emails = ['santosh8@illinois.edu']
all_users = users_ref.get()
for user_id, user in all_users.items():
    fake_emails.append(user['email'])

# Create fake products linked to these emails
create_fake_products(product_count, fake_emails)

print("Database populated with fake data.")
