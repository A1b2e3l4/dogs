from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from models import db, User, Dog, Order
import os
import random
import requests
import json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///woofcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'petloveden@gmail.com'
app.config['MAIL_PASSWORD'] = 'oaat ucdl yvpk yyka'
app.config['MAIL_DEFAULT_SENDER'] = 'petloveden@gmail.com'

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads/profiles'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
mail = Mail(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Dog breeds data
DOG_BREEDS = [
    'Labrador Retriever', 'German Shepherd', 'Golden Retriever', 'Bulldog', 
    'Poodle', 'Beagle', 'Rottweiler', 'Yorkshire Terrier', 'Dachshund', 
    'Boxer', 'Siberian Husky', 'Chihuahua', 'Doberman Pinscher', 'Great Dane', 
    'Shih Tzu', 'Border Collie', 'Australian Shepherd', 'Pug', 'Cocker Spaniel', 
    'Maltese', 'French Bulldog', 'Saint Bernard', 'Shetland Sheepdog', 
    'Bernese Mountain Dog', 'Greyhound', 'Bichon Frisé', 'Akita', 
    'Pit Bull Terrier', 'Dalmatian', 'Irish Setter'
]

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_verification_email(user_email, verification_code):
    try:
        msg = Message('Woofcare - Email Verification',
                      recipients=[user_email])
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #8B7355, #a88c6c);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .verification-code {{
                    background: #8B7355;
                    color: white;
                    padding: 20px;
                    font-size: 2rem;
                    font-weight: bold;
                    text-align: center;
                    border-radius: 8px;
                    letter-spacing: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 0.9rem;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Woofcare</h1>
                <p>Find Your Perfect Companion</p>
            </div>
            
            <div class="content">
                <h2>Verify Your Email Address</h2>
                <p>Hello!</p>
                <p>Thank you for joining Woofcare! To complete your registration and start browsing our lovely dogs, please verify your email address using the code below:</p>
                
                <div class="verification-code">
                    {verification_code}
                </div>
                
                <p>Enter this code on the verification page to activate your account. This code will expire in 1 hour for security reasons.</p>
                
                <p>If you didn't create an account with Woofcare, please ignore this email.</p>
                
                <p>Best regards,<br>The Woofcare Team</p>
            </div>
            
            <div class="footer">
                <p>&copy; 2024 Woofcare. All rights reserved.</p>
                <p>Nairobi, Kenya</p>
            </div>
        </body>
        </html>
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def init_db():
    with app.app_context():
        # Drop all tables and recreate them (for development only)
        db.drop_all()
        db.create_all()
        
        # Add sample dogs if none exist - WITH CORRECTED IMAGE PATHS
        sample_dogs = [
            Dog(
                name="Max", breed="Labrador Retriever", age=2, 
                age_category="young", size="large", color="Golden", 
                energy_level="high", price=25000.0,
                description="Friendly and energetic Labrador Retriever. Great with families and children.",
                image_url="/static/images/breeds/Labrador.jpg"  # Corrected path
            ),
            Dog(
                name="Bella", breed="German Shepherd", age=3, 
                age_category="adult", size="large", color="Black and Tan", 
                energy_level="high", price=30000.0,
                description="Loyal and intelligent German Shepherd. Excellent guard dog and family companion.",
                image_url="/static/images/breeds/german-shepherd.jpg"  # Corrected path
            ),
            Dog(
                name="Charlie", breed="French Bulldog", age=1, 
                age_category="puppy", size="small", color="Brindle", 
                energy_level="medium", price=45000.0,
                description="Playful and affectionate French Bulldog. Perfect for apartment living.",
                image_url="/static/images/breeds/french-bulldog.jpg"  # Corrected path
            ),
            # Add more sample dogs for better variety
            Dog(
                name="Luna", breed="Golden Retriever", age=1, 
                age_category="puppy", size="large", color="Cream", 
                energy_level="high", price=35000.0,
                description="Sweet and intelligent Golden Retriever puppy. Loves to play and learn new tricks.",
                image_url="/static/images/breeds/Golden_Retriever.jpg"
            ),
            Dog(
                name="Rocky", breed="Beagle", age=2, 
                age_category="young", size="medium", color="Tri-color", 
                energy_level="medium", price=22000.0,
                description="Curious and friendly Beagle with a great sense of smell. Perfect for active families.",
                image_url="/static/images/breeds/beagle.jpg"
            ),
            Dog(
                name="Daisy", breed="Poodle", age=4, 
                age_category="adult", size="medium", color="White", 
                energy_level="medium", price=28000.0,
                description="Elegant and intelligent Poodle. Hypoallergenic and great for families with allergies.",
                image_url="/static/images/breeds/poodle.jpg"
            )
        ]
        for dog in sample_dogs:
            db.session.add(dog)
        
        # Create a test admin user
        admin_user = User(
            email="admin@woofcare.com",
            first_name="Admin",
            last_name="User",
            phone="254700000000",
            is_verified=True,
            is_admin=True
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        
        # Create a test regular user
        test_user = User(
            email="test@woofcare.com",
            first_name="Test",
            last_name="User",
            phone="254711111111",
            is_verified=True,
            is_admin=False
        )
        test_user.set_password("test123")
        db.session.add(test_user)
        
        db.session.commit()
        print("Database initialized successfully with corrected image paths!")

# Routes
@app.route('/')
def index():
    dogs = Dog.query.filter_by(is_available=True).limit(6).all()
    return render_template('index.html', dogs=dogs)

@app.route('/dogs')
def dogs():
    breed = request.args.get('breed')
    age_category = request.args.get('age_category')
    size = request.args.get('size')
    color = request.args.get('color')
    energy_level = request.args.get('energy_level')
    
    query = Dog.query.filter_by(is_available=True)
    
    if breed:
        query = query.filter_by(breed=breed)
    if age_category:
        query = query.filter_by(age_category=age_category)
    if size:
        query = query.filter_by(size=size)
    if color:
        query = query.filter(Dog.color.ilike(f'%{color}%'))
    if energy_level:
        query = query.filter_by(energy_level=energy_level)
    
    dogs = query.all()
    return render_template('dogs.html', dogs=dogs, breeds=DOG_BREEDS)

@app.route('/dog/<int:dog_id>')
def dog_detail(dog_id):
    dog = Dog.query.get_or_404(dog_id)
    # Get similar dogs (same breed or same size)
    similar_dogs = Dog.query.filter(
        Dog.id != dog.id,
        Dog.is_available == True
    ).filter(
        (Dog.breed == dog.breed) | (Dog.size == dog.size)
    ).limit(4).all()
    
    return render_template('dog_detail.html', dog=dog, similar_dogs=similar_dogs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        verification_code = str(random.randint(100000, 999999))
        
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            verification_code=verification_code
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        if send_verification_email(email, verification_code):
            flash('Verification code sent to your email', 'success')
        else:
            flash('Error sending verification email', 'error')
        
        return redirect(url_for('verify_email', email=email))
    
    return render_template('register.html')

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    email = request.args.get('email')
    
    if request.method == 'POST':
        email = request.form['email']
        code = request.form['code']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.verification_code == code:
            user.is_verified = True
            user.verification_code = None
            db.session.commit()
            flash('Email verified successfully! You can now login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid verification code', 'error')
    
    return render_template('verify.html', email=email)

@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    email = request.form['email']
    user = User.query.filter_by(email=email).first()
    
    if user and not user.is_verified:
        verification_code = str(random.randint(100000, 999999))
        user.verification_code = verification_code
        db.session.commit()
        
        if send_verification_email(email, verification_code):
            flash('Verification code resent to your email', 'success')
        else:
            flash('Error sending verification email', 'error')
    else:
        flash('Email not found or already verified', 'error')
    
    return redirect(url_for('verify_email', email=email))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember_me = 'remember_me' in request.form
        
        print(f"🔐 Login attempt for: {email}")
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            print(f"✅ User found: {user.email}, verified: {user.is_verified}")
            if user.check_password(password):
                print("✅ Password correct")
                if user.is_verified:
                    login_user(user, remember=remember_me)
                    print(f"🎉 User logged in successfully. Authenticated: {current_user.is_authenticated}")
                    flash('Logged in successfully!', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('index'))
                else:
                    print("❌ User not verified")
                    flash('Please verify your email first. Check your email for the verification code.', 'error')
                    return redirect(url_for('verify_email', email=email))
            else:
                print("❌ Password incorrect")
                flash('Invalid email or password', 'error')
        else:
            print("❌ User not found")
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            reset_code = str(random.randint(100000, 999999))
            user.verification_code = reset_code
            db.session.commit()
            
            # Send reset code via email
            try:
                msg = Message('Woofcare - Password Reset',
                            recipients=[email])
                msg.body = f'Your password reset code is: {reset_code}'
                mail.send(msg)
                flash('Reset code sent to your email', 'success')
                return redirect(url_for('reset_password', email=email))
            except Exception as e:
                flash('Error sending reset code', 'error')
        else:
            flash('Email not found', 'error')
    
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email')
    
    if request.method == 'POST':
        email = request.form['email']
        code = request.form['code']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.verification_code == code:
            user.set_password(password)
            user.verification_code = None
            db.session.commit()
            flash('Password reset successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid reset code', 'error')
    
    return render_template('reset_password.html', email=email)

@app.route('/checkout/<int:dog_id>', methods=['GET', 'POST'])
@login_required
def checkout(dog_id):
    dog = Dog.query.get_or_404(dog_id)
    
    if request.method == 'POST':
        mpesa_number = request.form['mpesa_number']
        
        # Initialize payment with IntaSend
        order = Order(
            user_id=current_user.id,
            dog_id=dog.id,
            amount=dog.price,
            mpesa_number=mpesa_number
        )
        db.session.add(order)
        db.session.commit()
        
        # IntaSend payment integration
        intasend_api_key = "YOUR_INTASEND_API_KEY"
        headers = {
            "Authorization": f"Bearer {intasend_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "public_key": "ISPubKey_test_",
            "amount": dog.price,
            "currency": "KES",
            "phone_number": mpesa_number,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "order_id": order.id
        }
        
        try:
            response = requests.post(
                "https://payment.intasend.com/api/v1/payment/mpesa-stk-push/",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    order.transaction_id = data.get('invoice', {}).get('transaction_id')
                    db.session.commit()
                    flash('Payment initiated. Check your phone to complete payment.', 'success')
                    return redirect(url_for('order_confirmation', order_id=order.id))
                else:
                    flash('Payment initiation failed', 'error')
            else:
                flash('Payment service unavailable', 'error')
        except Exception as e:
            flash('Payment service error', 'error')
    
    return render_template('checkout.html', dog=dog)

@app.route('/order-confirmation/<order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('order_confirmation.html', order=order)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# User Account Routes
@app.route('/account')
@login_required
def account():
    # Get user's orders
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    # Calculate user statistics
    total_orders = len(orders)
    completed_orders = len([order for order in orders if order.status == 'completed'])
    total_spent = sum(order.amount for order in orders if order.status == 'completed')
    
    # For now, return empty wishlist until we implement it
    wishlist_dogs = []
    wishlist_count = 0
    
    return render_template('account.html', 
                         orders=orders, 
                         wishlist_dogs=wishlist_dogs,
                         wishlist_count=wishlist_count,
                         total_orders=total_orders,
                         completed_orders=completed_orders,
                         total_spent=total_spent)

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    current_user.first_name = request.form['first_name']
    current_user.last_name = request.form['last_name']
    current_user.phone = request.form['phone']
    
    # Handle profile picture upload
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"user_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            current_user.profile_picture = f"/static/uploads/profiles/{filename}"
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('account'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('account') + '#settings')
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('account') + '#settings')
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('account') + '#settings')
    
    current_user.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('account'))

# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    total_dogs = Dog.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    
    # Calculate total revenue
    completed_orders = Order.query.filter_by(status='completed').all()
    total_revenue = sum(order.amount for order in completed_orders)
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_dogs=total_dogs,
                         total_orders=total_orders,
                         total_users=total_users,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders)

@app.route('/admin/dogs')
@login_required
def admin_dogs():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    dogs = Dog.query.all()
    return render_template('admin/dogs.html', dogs=dogs)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    orders = Order.query.all()
    return render_template('admin/orders.html', orders=orders)

# Debug routes
@app.route('/debug/users')
def debug_users():
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'email': user.email,
            'is_verified': user.is_verified,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'has_profile_pic': bool(user.profile_picture)
        })
    return jsonify(result)

@app.route('/debug/check-login')
@login_required
def debug_check_login():
    return jsonify({
        'is_authenticated': current_user.is_authenticated,
        'user_id': current_user.id,
        'email': current_user.email,
        'is_verified': current_user.is_verified,
        'first_name': current_user.first_name
    })

@app.route('/debug/current-user')
def debug_current_user():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user_id': current_user.id,
            'email': current_user.email,
            'first_name': current_user.first_name
        })
    else:
        return jsonify({'authenticated': False})

# Test route to check if images are loading
@app.route('/test-images')
def test_images():
    """Test if images are loading correctly"""
    breeds = [
        'Labrador.jpg', 'german-shepherd.jpg', 'french-bulldog.jpg',
        'Golden_Retriever.jpg', 'beagle.jpg', 'bulldog.jpg', 'poodle.jpg'
    ]
    return render_template('test_images.html', breeds=breeds)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
def init_db():
    with app.app_context():
        # Drop all tables and recreate them (for development only)
        db.drop_all()
        db.create_all()
        
        # Add 30+ sample dogs covering all breeds
        sample_dogs = [
            # Family-Friendly Breeds (5 dogs)
            Dog(
                name="Max", breed="Labrador Retriever", age=2, 
                age_category="young", size="large", color="Golden", 
                energy_level="high", price=25000.0,
                description="Friendly and energetic Labrador Retriever. Great with families and children.",
                image_url="/static/images/breeds/Labrador.jpg"
            ),
            Dog(
                name="Luna", breed="Golden Retriever", age=1, 
                age_category="puppy", size="large", color="Cream", 
                energy_level="high", price=35000.0,
                description="Sweet and intelligent Golden Retriever puppy. Loves to play and learn new tricks.",
                image_url="/static/images/breeds/Golden_Retriever.jpg"
            ),
            Dog(
                name="Buddy", breed="Beagle", age=2, 
                age_category="young", size="medium", color="Tri-color", 
                energy_level="medium", price=22000.0,
                description="Curious and friendly Beagle with a great sense of smell. Perfect for active families.",
                image_url="/static/images/breeds/beagle.jpg"
            ),
            Dog(
                name="Duke", breed="Bulldog", age=4, 
                age_category="adult", size="medium", color="Brindle", 
                energy_level="low", price=35000.0,
                description="Gentle and low-energy Bulldog. Great companion for relaxed households.",
                image_url="/static/images/breeds/bulldog.jpg"
            ),
            Dog(
                name="Daisy", breed="Poodle", age=3, 
                age_category="adult", size="medium", color="White", 
                energy_level="medium", price=28000.0,
                description="Elegant and intelligent Poodle. Hypoallergenic and great for families with allergies.",
                image_url="/static/images/breeds/poodle.jpg"
            ),

            # Working & Guardian Breeds (5 dogs)
            Dog(
                name="Bella", breed="German Shepherd", age=3, 
                age_category="adult", size="large", color="Black and Tan", 
                energy_level="high", price=30000.0,
                description="Loyal and intelligent German Shepherd. Excellent guard dog and family companion.",
                image_url="/static/images/breeds/german-shepherd.jpg"
            ),
            Dog(
                name="Rocky", breed="Rottweiler", age=2, 
                age_category="young", size="large", color="Black and Mahogany", 
                energy_level="medium", price=32000.0,
                description="Confident and loyal Rottweiler. Natural protector with a gentle heart.",
                image_url="/static/images/breeds/rottweiler.jpg"
            ),
            Dog(
                name="Zeus", breed="Doberman Pinscher", age=4, 
                age_category="adult", size="large", color="Black and Rust", 
                energy_level="high", price=35000.0,
                description="Athletic and intelligent Doberman. Excellent working dog and loyal companion.",
                image_url="/static/images/breeds/doberman.jpg"
            ),
            Dog(
                name="Tyson", breed="Boxer", age=1, 
                age_category="puppy", size="large", color="Fawn", 
                energy_level="high", price=28000.0,
                description="Playful and energetic Boxer puppy. Loves to play and has a wonderful temperament.",
                image_url="/static/images/breeds/boxer.jpg"
            ),
            Dog(
                name="Apollo", breed="Great Dane", age=2, 
                age_category="young", size="large", color="Harlequin", 
                energy_level="medium", price=40000.0,
                description="Gentle giant with a sweet disposition. Majestic and family-friendly.",
                image_url="/static/images/breeds/great-dane.jpg"
            ),

            # Small & Companion Breeds (5 dogs)
            Dog(
                name="Charlie", breed="French Bulldog", age=1, 
                age_category="puppy", size="small", color="Brindle", 
                energy_level="medium", price=45000.0,
                description="Playful and affectionate French Bulldog. Perfect for apartment living.",
                image_url="/static/images/breeds/french-bulldog.jpg"
            ),
            Dog(
                name="Coco", breed="Yorkshire Terrier", age=1, 
                age_category="puppy", size="small", color="Black and Tan", 
                energy_level="medium", price=25000.0,
                description="Adorable Yorkshire Terrier with big personality. Perfect lap dog.",
                image_url="/static/images/breeds/yorkie.jpg"
            ),
            Dog(
                name="Peanut", breed="Chihuahua", age=2, 
                age_category="young", size="small", color="Fawn", 
                energy_level="medium", price=18000.0,
                description="Tiny Chihuahua with huge personality. Loyal and affectionate companion.",
                image_url="/static/images/breeds/chihuahua.jpg"
            ),
            Dog(
                name="Mimi", breed="Shih Tzu", age=3, 
                age_category="adult", size="small", color="White and Gold", 
                energy_level="low", price=22000.0,
                description="Charming Shih Tzu with a sweet nature. Great companion for all ages.",
                image_url="/static/images/breeds/shih-tzu.jpg"
            ),
            Dog(
                name="Snowball", breed="Maltese", age=2, 
                age_category="young", size="small", color="White", 
                energy_level="low", price=26000.0,
                description="Elegant Maltese with a gentle disposition. Perfect for city living.",
                image_url="/static/images/breeds/maltese.jpg"
            ),

            # Active & Herding Breeds (5 dogs)
            Dog(
                name="Rex", breed="Border Collie", age=2, 
                age_category="young", size="medium", color="Black and White", 
                energy_level="high", price=28000.0,
                description="Highly intelligent Border Collie. Needs active owners and mental stimulation.",
                image_url="/static/images/breeds/border-collie.jpg"
            ),
            Dog(
                name="Aussie", breed="Australian Shepherd", age=1, 
                age_category="puppy", size="medium", color="Blue Merle", 
                energy_level="high", price=32000.0,
                description="Beautiful Australian Shepherd puppy. Smart and eager to please.",
                image_url="/static/images/breeds/australian-shepherd.jpg"
            ),
            Dog(
                name="Blizzard", breed="Siberian Husky", age=3, 
                age_category="adult", size="large", color="Gray and White", 
                energy_level="high", price=30000.0,
                description="Stunning Siberian Husky with blue eyes. Energetic and friendly.",
                image_url="/static/images/breeds/siberian-husky.jpg"
            ),
            Dog(
                name="Shelly", breed="Shetland Sheepdog", age=2, 
                age_category="young", size="small", color="Sable and White", 
                energy_level="high", price=26000.0,
                description="Intelligent Shetland Sheepdog. Miniature collie with big heart.",
                image_url="/static/images/breeds/shetland-sheepdog.jpg"
            ),
            Dog(
                name="Ruby", breed="Irish Setter", age=1, 
                age_category="puppy", size="large", color="Mahogany", 
                energy_level="high", price=29000.0,
                description="Beautiful Irish Setter puppy. Energetic and outgoing personality.",
                image_url="/static/images/breeds/irish-setter.jpg"
            ),

            # Unique & Special Breeds (5 dogs)
            Dog(
                name="Winston", breed="Dachshund", age=3, 
                age_category="adult", size="small", color="Red", 
                energy_level="medium", price=20000.0,
                description="Curious Dachshund with long body and big personality. Great family dog.",
                image_url="/static/images/breeds/dachshund.jpg"
            ),
            Dog(
                name="Bailey", breed="Cocker Spaniel", age=2, 
                age_category="young", size="medium", color="Golden", 
                energy_level="medium", price=24000.0,
                description="Beautiful Cocker Spaniel with silky coat. Gentle and loving companion.",
                image_url="/static/images/breeds/cocker-spaniel.jpg"
            ),
            Dog(
                name="Bernard", breed="Saint Bernard", age=4, 
                age_category="adult", size="large", color="Red and White", 
                energy_level="low", price=38000.0,
                description="Gentle giant Saint Bernard. Famous rescue dog with sweet nature.",
                image_url="/static/images/breeds/saint-bernard.jpg"
            ),
            Dog(
                name="Mountain", breed="Bernese Mountain Dog", age=2, 
                age_category="young", size="large", color="Tri-color", 
                energy_level="medium", price=42000.0,
                description="Beautiful Bernese Mountain Dog. Calm and great with families.",
                image_url="/static/images/breeds/bernese-mountain.jpg"
            ),
            Dog(
                name="Speedy", breed="Greyhound", age=3, 
                age_category="adult", size="large", color="Fawn", 
                energy_level="low", price=27000.0,
                description="Surprisingly low-energy Greyhound. Fastest couch potato you'll meet.",
                image_url="/static/images/breeds/greyhound.jpg"
            ),

            # More Wonderful Breeds (5 dogs)
            Dog(
                name="Fluffy", breed="Bichon Frisé", age=1, 
                age_category="puppy", size="small", color="White", 
                energy_level="medium", price=23000.0,
                description="Cheerful Bichon Frisé puppy. Hypoallergenic and great for families.",
                image_url="/static/images/breeds/bichon.jpg"
            ),
            Dog(
                name="Kuma", breed="Akita", age=3, 
                age_category="adult", size="large", color="White", 
                energy_level="medium", price=35000.0,
                description="Majestic Akita with profound loyalty. Dignified and courageous companion.",
                image_url="/static/images/breeds/akita.jpg"
            ),
            Dog(
                name="Tank", breed="Pit Bull Terrier", age=2, 
                age_category="young", size="medium", color="Blue", 
                energy_level="high", price=22000.0,
                description="Misunderstood Pit Bull with incredible loyalty. Affectionate family dog.",
                image_url="/static/images/breeds/pitbull.jpg"
            ),
            Dog(
                name="Spot", breed="Dalmatian", age=1, 
                age_category="puppy", size="large", color="White with Black Spots", 
                energy_level="high", price=26000.0,
                description="Iconic Dalmatian puppy. Energetic and intelligent with unique appearance.",
                image_url="/static/images/breeds/dalmatian.jpg"
            ),
            Dog(
                name="Pugsley", breed="Pug", age=2, 
                age_category="young", size="small", color="Fawn", 
                energy_level="low", price=24000.0,
                description="Charming Pug with wonderful personality. Great companion for any home.",
                image_url="/static/images/breeds/pug.jpg"
            )
        ]
        
        for dog in sample_dogs:
            db.session.add(dog)
        
        # Create a test admin user
        admin_user = User(
            email="admin@woofcare.com",
            first_name="Admin",
            last_name="User",
            phone="254700000000",
            is_verified=True,
            is_admin=True
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        
        # Create a test regular user
        test_user = User(
            email="test@woofcare.com",
            first_name="Test",
            last_name="User",
            phone="254711111111",
            is_verified=True,
            is_admin=False
        )
        test_user.set_password("test123")
        db.session.add(test_user)
        
        db.session.commit()
        print("Database initialized successfully with 30+ dogs!")