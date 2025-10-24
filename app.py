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

def send_verification_email(user_email, verification_code, user_name):
    try:
        msg = Message('Woofcare - Email Verification', recipients=[user_email])
        
        # Create the email HTML with proper escaping for CSS in Python string
        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Woofcare - Email Verification</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Poppins', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                
                .email-container {{
                    max-width: 600px;
                    width: 100%;
                    background: white;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }}
                
                .header {{
                    background: linear-gradient(135deg, #8B7355 0%, #a88c6c 50%, #c5a57f 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }}
                
                .logo {{
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin-bottom: 10px;
                    display: inline-block;
                }}
                
                .header h1 {{
                    font-size: 2.2rem;
                    margin-bottom: 10px;
                    position: relative;
                    z-index: 2;
                }}
                
                .header p {{
                    font-size: 1.1rem;
                    opacity: 0.9;
                    position: relative;
                    z-index: 2;
                }}
                
                .content {{
                    padding: 40px 30px;
                    background: #f9f9f9;
                }}
                
                .welcome-message {{
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 20px;
                    border-radius: 15px;
                    margin-bottom: 25px;
                    text-align: center;
                }}
                
                .welcome-message h2 {{
                    font-size: 1.5rem;
                    margin-bottom: 10px;
                }}
                
                .user-name {{
                    font-weight: 600;
                    color: #FFD700;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                
                .verification-section {{
                    text-align: center;
                    margin: 30px 0;
                }}
                
                .verification-code {{
                    background: linear-gradient(135deg, #8B7355, #a88c6c);
                    color: white;
                    padding: 25px;
                    font-size: 2.5rem;
                    font-weight: bold;
                    text-align: center;
                    border-radius: 15px;
                    letter-spacing: 8px;
                    margin: 25px 0;
                    box-shadow: 0 10px 20px rgba(139, 115, 85, 0.3);
                    position: relative;
                    overflow: hidden;
                }}
                
                .instructions {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 25px 0;
                    border-left: 4px solid #8B7355;
                }}
                
                .steps {{
                    display: flex;
                    justify-content: space-between;
                    margin: 30px 0;
                }}
                
                .step {{
                    text-align: center;
                    flex: 1;
                    padding: 15px;
                }}
                
                .step-icon {{
                    width: 60px;
                    height: 60px;
                    background: #8B7355;
                    color: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 15px;
                    font-size: 1.5rem;
                }}
                
                .step-text {{
                    font-size: 0.9rem;
                    color: #666;
                }}
                
                .security-note {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: center;
                }}
                
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 30px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 0.9rem;
                }}
                
                .social-links {{
                    display: flex;
                    justify-content: center;
                    gap: 15px;
                    margin: 20px 0;
                }}
                
                .social-link {{
                    width: 40px;
                    height: 40px;
                    background: #8B7355;
                    color: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-decoration: none;
                }}
                
                @media (max-width: 768px) {{
                    .steps {{
                        flex-direction: column;
                        gap: 15px;
                    }}
                    
                    .verification-code {{
                        font-size: 2rem;
                        letter-spacing: 5px;
                        padding: 20px;
                    }}
                    
                    .header {{
                        padding: 30px 20px;
                    }}
                    
                    .content {{
                        padding: 30px 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div class="logo">🐕 Woofcare</div>
                    <h1>Find Your Perfect Companion</h1>
                    <p>Where tails wag and hearts connect</p>
                </div>
                
                <div class="content">
                    <!-- Welcome Message with User's Name -->
                    <div class="welcome-message">
                        <h2>Welcome to Woofcare, <span class="user-name">{user_name}</span>! 🎉</h2>
                        <p>We're thrilled to have you join our community of dog lovers</p>
                    </div>
                    
                    <h2 style="text-align: center; margin-bottom: 20px; color: #8B7355;">Verify Your Email Address</h2>
                    
                    <p style="text-align: center; margin-bottom: 25px; font-size: 1.1rem;">
                        Hello <strong>{user_name}</strong>! Thank you for choosing Woofcare to find your perfect furry friend. 
                        To complete your registration and start browsing our lovely dogs, please verify your email address.
                    </p>
                    
                    <div class="verification-section">
                        <p style="margin-bottom: 15px; font-weight: 500;">Your verification code is:</p>
                        
                        <div class="verification-code">
                            {verification_code}
                        </div>
                        
                        <p style="color: #666; font-size: 0.95rem;">
                            Enter this code on the verification page to activate your account
                        </p>
                    </div>
                    
                    <!-- Steps Instructions -->
                    <div class="steps">
                        <div class="step">
                            <div class="step-icon">1</div>
                            <div class="step-text">Copy the verification code</div>
                        </div>
                        <div class="step">
                            <div class="step-icon">2</div>
                            <div class="step-text">Return to Woofcare</div>
                        </div>
                        <div class="step">
                            <div class="step-icon">3</div>
                            <div class="step-text">Enter the code & start exploring!</div>
                        </div>
                    </div>
                    
                    <div class="instructions">
                        <p style="margin-bottom: 10px;"><strong>Quick Tip:</strong> Keep this code secure and don't share it with anyone.</p>
                        <p>Once verified, you'll be able to browse dogs, save favorites, and start your adoption journey!</p>
                    </div>
                    
                    <div class="security-note">
                        ⚠️ <strong>Security Notice:</strong> This code will expire in <strong>1 hour</strong> for your protection.
                    </div>
                    
                    <p style="text-align: center; margin: 25px 0; color: #666;">
                        If you didn't create an account with Woofcare, please ignore this email or 
                        <a href="mailto:support@woofcare.com" style="color: #8B7355;">contact our support team</a>.
                    </p>
                    
                    <p style="text-align: center; font-size: 1.1rem;">
                        Best regards,<br>
                        <strong>The Woofcare Team</strong> 🐶
                    </p>
                </div>
                
                <div class="footer">
                    <div class="social-links">
                        <a href="#" class="social-link">📘</a>
                        <a href="#" class="social-link">📷</a>
                        <a href="#" class="social-link">🐦</a>
                        <a href="#" class="social-link">💼</a>
                    </div>
                    <p>&copy; 2025 Woofcare. All rights reserved.</p>
                    <p>Nairobi, Kenya | <a href="#" style="color: #8B7355;">Unsubscribe</a></p>
                    <p style="margin-top: 10px; font-size: 0.8rem; opacity: 0.7;">
                        Bringing joy, one paw at a time 🐾
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.html = email_html
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_password_reset_email(user_email, reset_code, user_name):
    try:
        msg = Message('Woofcare - Password Reset Request', recipients=[user_email])
        
        # Create the password reset email HTML
        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Woofcare - Password Reset</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Poppins', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                
                .email-container {{
                    max-width: 600px;
                    width: 100%;
                    background: white;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }}
                
                .header {{
                    background: linear-gradient(135deg, #8B7355 0%, #a88c6c 50%, #c5a57f 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }}
                
                .logo {{
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin-bottom: 10px;
                    display: inline-block;
                }}
                
                .header h1 {{
                    font-size: 2.2rem;
                    margin-bottom: 10px;
                    position: relative;
                    z-index: 2;
                }}
                
                .header p {{
                    font-size: 1.1rem;
                    opacity: 0.9;
                    position: relative;
                    z-index: 2;
                }}
                
                .content {{
                    padding: 40px 30px;
                    background: #f9f9f9;
                }}
                
                .security-alert {{
                    background: linear-gradient(135deg, #ff6b6b, #ee5a52);
                    color: white;
                    padding: 20px;
                    border-radius: 15px;
                    margin-bottom: 25px;
                    text-align: center;
                }}
                
                .security-alert h2 {{
                    font-size: 1.5rem;
                    margin-bottom: 10px;
                }}
                
                .user-name {{
                    font-weight: 600;
                    color: #FFD700;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                
                .reset-section {{
                    text-align: center;
                    margin: 30px 0;
                }}
                
                .reset-code {{
                    background: linear-gradient(135deg, #8B7355, #a88c6c);
                    color: white;
                    padding: 25px;
                    font-size: 2.5rem;
                    font-weight: bold;
                    text-align: center;
                    border-radius: 15px;
                    letter-spacing: 8px;
                    margin: 25px 0;
                    box-shadow: 0 10px 20px rgba(139, 115, 85, 0.3);
                    position: relative;
                    overflow: hidden;
                }}
                
                .instructions {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 25px 0;
                    border-left: 4px solid #8B7355;
                }}
                
                .steps {{
                    display: flex;
                    justify-content: space-between;
                    margin: 30px 0;
                }}
                
                .step {{
                    text-align: center;
                    flex: 1;
                    padding: 15px;
                }}
                
                .step-icon {{
                    width: 60px;
                    height: 60px;
                    background: #8B7355;
                    color: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 15px;
                    font-size: 1.5rem;
                }}
                
                .step-text {{
                    font-size: 0.9rem;
                    color: #666;
                }}
                
                .security-note {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: center;
                }}
                
                .urgent-note {{
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: center;
                }}
                
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 30px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 0.9rem;
                }}
                
                .social-links {{
                    display: flex;
                    justify-content: center;
                    gap: 15px;
                    margin: 20px 0;
                }}
                
                .social-link {{
                    width: 40px;
                    height: 40px;
                    background: #8B7355;
                    color: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-decoration: none;
                }}
                
                .btn {{
                    display: inline-block;
                    background: linear-gradient(135deg, #8B7355, #a88c6c);
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: 600;
                    margin: 10px 5px;
                }}
                
                @media (max-width: 768px) {{
                    .steps {{
                        flex-direction: column;
                        gap: 15px;
                    }}
                    
                    .reset-code {{
                        font-size: 2rem;
                        letter-spacing: 5px;
                        padding: 20px;
                    }}
                    
                    .header {{
                        padding: 30px 20px;
                    }}
                    
                    .content {{
                        padding: 30px 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div class="logo">🐕 Woofcare</div>
                    <h1>Password Reset Request</h1>
                    <p>Secure your account and get back to finding your perfect companion</p>
                </div>
                
                <div class="content">
                    <!-- Security Alert -->
                    <div class="security-alert">
                        <h2>Security Alert 🔒</h2>
                        <p>A password reset was requested for your Woofcare account</p>
                    </div>
                    
                    <h2 style="text-align: center; margin-bottom: 20px; color: #8B7355;">Reset Your Password</h2>
                    
                    <p style="text-align: center; margin-bottom: 25px; font-size: 1.1rem;">
                        Hello <strong>{user_name}</strong>! We received a request to reset your Woofcare account password. 
                        Use the code below to securely reset your password and regain access to your account.
                    </p>
                    
                    <div class="reset-section">
                        <p style="margin-bottom: 15px; font-weight: 500;">Your password reset code is:</p>
                        
                        <div class="reset-code">
                            {reset_code}
                        </div>
                        
                        <p style="color: #666; font-size: 0.95rem;">
                            Enter this code on the password reset page to create a new password
                        </p>
                    </div>
                    
                    <!-- Steps Instructions -->
                    <div class="steps">
                        <div class="step">
                            <div class="step-icon">1</div>
                            <div class="step-text">Copy the reset code above</div>
                        </div>
                        <div class="step">
                            <div class="step-icon">2</div>
                            <div class="step-text">Return to Woofcare reset page</div>
                        </div>
                        <div class="step">
                            <div class="step-icon">3</div>
                            <div class="step-text">Enter code & create new password</div>
                        </div>
                    </div>
                    
                    <div class="instructions">
                        <p style="margin-bottom: 10px;"><strong>Need Help?</strong> If the button above doesn't work, copy and paste the reset code manually.</p>
                        <p>Make sure to create a strong password that you haven't used before for better security.</p>
                    </div>
                    
                    <div class="urgent-note">
                        ⚠️ <strong>Important:</strong> If you didn't request this password reset, please ignore this email and 
                        <a href="mailto:support@woofcare.com" style="color: #721c24; font-weight: bold;">contact our support team immediately</a>.
                    </div>
                    
                    <div class="security-note">
                        🔒 <strong>Security Notice:</strong> This reset code will expire in <strong>1 hour</strong> for your protection.
                        For security reasons, please do not share this code with anyone.
                    </div>
                    
                    <p style="text-align: center; margin: 25px 0; color: #666;">
                        Having trouble? <a href="mailto:support@woofcare.com" style="color: #8B7355;">Contact our support team</a> 
                        and we'll be happy to help you.
                    </p>
                    
                    <p style="text-align: center; font-size: 1.1rem;">
                        Stay secure,<br>
                        <strong>The Woofcare Security Team</strong> 🐶
                    </p>
                </div>
                
                <div class="footer">
                    <div class="social-links">
                        <a href="#" class="social-link">📘</a>
                        <a href="#" class="social-link">📷</a>
                        <a href="#" class="social-link">🐦</a>
                        <a href="#" class="social-link">💼</a>
                    </div>
                    <p>&copy; 2025 Woofcare. All rights reserved.</p>
                    <p>Nairobi, Kenya | <a href="#" style="color: #8B7355;">Privacy Policy</a></p>
                    <p style="margin-top: 10px; font-size: 0.8rem; opacity: 0.7;">
                        Protecting your account, one paw at a time 🐾
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.html = email_html
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False

def init_db():
    with app.app_context():
        # Drop all tables and recreate them (for development only)
        db.drop_all()
        db.create_all()
        
        # Add 30 sample dogs - one for each breed
        sample_dogs = [
            # Family-Friendly Breeds
            Dog(
                name="Max", breed="Labrador Retriever", age=2, 
                age_category="young", size="large", color="Golden", 
                energy_level="high", price=25000.0,
                description="Friendly and energetic Labrador Retriever. Great with families and children. Loves playing fetch and swimming.",
                image_url="/static/images/breeds/Labrador.jpg",
                is_available=True
            ),
            Dog(
                name="Bella", breed="German Shepherd", age=3, 
                age_category="adult", size="large", color="Black and Tan", 
                energy_level="high", price=30000.0,
                description="Loyal and intelligent German Shepherd. Excellent guard dog and family companion. Highly trainable and protective.",
                image_url="/static/images/breeds/german-shepherd.jpg",
                is_available=True
            ),
            Dog(
                name="Luna", breed="Golden Retriever", age=1, 
                age_category="puppy", size="large", color="Cream", 
                energy_level="high", price=35000.0,
                description="Sweet and intelligent Golden Retriever puppy. Loves to play and learn new tricks. Great with kids.",
                image_url="/static/images/breeds/Golden_Retriever.jpg",
                is_available=True
            ),
            Dog(
                name="Rocky", breed="Beagle", age=2, 
                age_category="young", size="medium", color="Tri-color", 
                energy_level="medium", price=22000.0,
                description="Curious and friendly Beagle with a great sense of smell. Perfect for active families and outdoor adventures.",
                image_url="/static/images/breeds/beagle.jpg",
                is_available=True
            ),
            Dog(
                name="Daisy", breed="Poodle", age=4, 
                age_category="adult", size="medium", color="White", 
                energy_level="medium", price=28000.0,
                description="Elegant and intelligent Poodle. Hypoallergenic and great for families with allergies. Very trainable.",
                image_url="/static/images/breeds/poodle.jpg",
                is_available=True
            ),
            Dog(
                name="Bruno", breed="Rottweiler", age=2, 
                age_category="young", size="large", color="Black and Tan", 
                energy_level="high", price=32000.0,
                description="Confident and courageous Rottweiler. Excellent guard dog with a loyal and protective nature.",
                image_url="/static/images/breeds/rottweiler.jpg",
                is_available=True
            ),
            Dog(
                name="Coco", breed="Yorkshire Terrier", age=1, 
                age_category="puppy", size="small", color="Blue and Tan", 
                energy_level="medium", price=25000.0,
                description="Small but brave Yorkshire Terrier with a big personality. Perfect for apartment living.",
                image_url="/static/images/breeds/yorkie.jpg",
                is_available=True
            ),
            Dog(
                name="Oscar", breed="Dachshund", age=3, 
                age_category="adult", size="small", color="Red", 
                energy_level="medium", price=20000.0,
                description="Curious and spunky Dachshund with a long body and big personality. Great for families.",
                image_url="/static/images/breeds/dachshund.jpg",
                is_available=True
            ),
            Dog(
                name="Zeus", breed="Boxer", age=2, 
                age_category="young", size="large", color="Fawn", 
                energy_level="high", price=28000.0,
                description="Playful and energetic Boxer. Great with children and makes an excellent family companion.",
                image_url="/static/images/breeds/boxer.jpg",
                is_available=True
            ),
            Dog(
                name="Lola", breed="Siberian Husky", age=2, 
                age_category="young", size="large", color="Gray and White", 
                energy_level="high", price=30000.0,
                description="Beautiful Husky with striking blue eyes. Energetic and loves cold weather. Great for active families.",
                image_url="/static/images/breeds/siberian-husky.jpg",
                is_available=True
            ),
            # Small & Companion Breeds
            Dog(
                name="Peanut", breed="Chihuahua", age=1, 
                age_category="puppy", size="small", color="Tan", 
                energy_level="medium", price=18000.0,
                description="Tiny Chihuahua with a huge personality. Loyal companion perfect for city living.",
                image_url="/static/images/breeds/chihuahua.jpg",
                is_available=True
            ),
            Dog(
                name="Duke", breed="Doberman Pinscher", age=2, 
                age_category="young", size="large", color="Black and Rust", 
                energy_level="high", price=35000.0,
                description="Athletic and intelligent Doberman. Excellent guard dog with unwavering loyalty to family.",
                image_url="/static/images/breeds/doberman.jpg",
                is_available=True
            ),
            Dog(
                name="Titan", breed="Great Dane", age=1, 
                age_category="puppy", size="large", color="Harlequin", 
                energy_level="medium", price=40000.0,
                description="Gentle giant Great Dane puppy. Despite their size, they are gentle and great with families.",
                image_url="/static/images/breeds/great-dane.jpg",
                is_available=True
            ),
            Dog(
                name="Milo", breed="Shih Tzu", age=2, 
                age_category="young", size="small", color="White and Gold", 
                energy_level="low", price=22000.0,
                description="Affectionate and outgoing Shih Tzu. Perfect lap dog with a charming personality.",
                image_url="/static/images/breeds/shih-tzu.jpg",
                is_available=True
            ),
            Dog(
                name="Cooper", breed="Border Collie", age=2, 
                age_category="young", size="medium", color="Black and White", 
                energy_level="high", price=28000.0,
                description="Highly intelligent Border Collie. The world's smartest dog breed, perfect for active owners.",
                image_url="/static/images/breeds/border-collie.jpg",
                is_available=True
            ),
            Dog(
                name="Ruby", breed="Australian Shepherd", age=1, 
                age_category="puppy", size="medium", color="Blue Merle", 
                energy_level="high", price=32000.0,
                description="Beautiful Australian Shepherd with stunning merle coat. Intelligent and energetic working dog.",
                image_url="/static/images/breeds/australian-shepherd.jpg",
                is_available=True
            ),
            Dog(
                name="Buddy", breed="Pug", age=3, 
                age_category="adult", size="small", color="Fawn", 
                energy_level="low", price=24000.0,
                description="Charming and mischievous Pug. 'Multum in parvo' - a lot of dog in a small space with big personality.",
                image_url="/static/images/breeds/pug.jpg",
                is_available=True
            ),
            Dog(
                name="Sophie", breed="Cocker Spaniel", age=2, 
                age_category="young", size="medium", color="Golden", 
                energy_level="medium", price=24000.0,
                description="Beautiful sporting dog with silky coat and sweet disposition. Great family companion.",
                image_url="/static/images/breeds/cocker-spaniel.jpg",
                is_available=True
            ),
            Dog(
                name="Snowball", breed="Maltese", age=1, 
                age_category="puppy", size="small", color="White", 
                energy_level="low", price=26000.0,
                description="Elegant and gentle Maltese. Perfect lap dog with a sweet and charming personality.",
                image_url="/static/images/breeds/maltese.jpg",
                is_available=True
            ),
            Dog(
                name="Gizmo", breed="French Bulldog", age=1, 
                age_category="puppy", size="small", color="Brindle", 
                energy_level="medium", price=45000.0,
                description="Playful and affectionate French Bulldog. Perfect for apartment living with their charming bat ears.",
                image_url="/static/images/breeds/french-bulldog.jpg",
                is_available=True
            ),
            # Working & Guardian Breeds
            Dog(
                name="Bear", breed="Saint Bernard", age=2, 
                age_category="young", size="large", color="Red and White", 
                energy_level="low", price=38000.0,
                description="Gentle giant Saint Bernard. Famous rescue dog known for massive size and gentle nature.",
                image_url="/static/images/breeds/saint-bernard.jpg",
                is_available=True
            ),
            Dog(
                name="Mountain", breed="Bernese Mountain Dog", age=1, 
                age_category="puppy", size="large", color="Tri-color", 
                energy_level="medium", price=42000.0,
                description="Beautiful tri-colored working dog from Swiss Alps. Calm and good-natured family companion.",
                image_url="/static/images/breeds/bernese-mountain.jpg",
                is_available=True
            ),
            Dog(
                name="Flash", breed="Greyhound", age=3, 
                age_category="adult", size="large", color="Fawn", 
                energy_level="low", price=27000.0,
                description="The world's fastest couch potato. Surprisingly low energy indoors despite racing background.",
                image_url="/static/images/breeds/greyhound.jpg",
                is_available=True
            ),
            Dog(
                name="Cotton", breed="Bichon Frisé", age=2, 
                age_category="young", size="small", color="White", 
                energy_level="medium", price=23000.0,
                description="Fluffy white companion known for happy-go-lucky attitude. Hypoallergenic and great for allergies.",
                image_url="/static/images/breeds/bichon.jpg",
                is_available=True
            ),
            Dog(
                name="Kuma", breed="Akita", age=2, 
                age_category="young", size="large", color="White", 
                energy_level="medium", price=35000.0,
                description="Majestic Japanese guardian known for unwavering loyalty. Dignified and profoundly loyal companion.",
                image_url="/static/images/breeds/akita.jpg",
                is_available=True
            ),
            Dog(
                name="Blue", breed="Pit Bull Terrier", age=2, 
                age_category="young", size="medium", color="Blue", 
                energy_level="high", price=22000.0,
                description="Misunderstood companion with incredible loyalty and affection. Strong and confident family dog.",
                image_url="/static/images/breeds/pitbull.jpg",
                is_available=True
            ),
            Dog(
                name="Spot", breed="Dalmatian", age=1, 
                age_category="puppy", size="large", color="White with Black Spots", 
                energy_level="high", price=26000.0,
                description="Iconic spotted dog known for endurance and unique appearance. Energetic and smart companion.",
                image_url="/static/images/breeds/dalmatian.jpg",
                is_available=True
            ),
            Dog(
                name="Shelly", breed="Shetland Sheepdog", age=2, 
                age_category="young", size="small", color="Sable and White", 
                energy_level="high", price=26000.0,
                description="Miniature collie with big heart and exceptional intelligence. Lively and highly trainable.",
                image_url="/static/images/breeds/shetland-sheepdog.jpg",
                is_available=True
            ),
            Dog(
                name="Rusty", breed="Irish Setter", age=1, 
                age_category="puppy", size="large", color="Mahogany", 
                energy_level="high", price=29000.0,
                description="Beautiful red-coated hunter with endless energy and charm. Perfect for active families.",
                image_url="/static/images/breeds/irish-setter.jpg",
                is_available=True
            ),
            Dog(
                name="Winston", breed="Bulldog", age=4, 
                age_category="adult", size="medium", color="Brindle", 
                energy_level="low", price=35000.0,
                description="Calm and courageous Bulldog. Gentle and low-energy companion perfect for relaxed households.",
                image_url="/static/images/breeds/bulldog.jpg",
                is_available=True
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
        print("Database initialized successfully with 30 dogs!")

# ==================== ROUTES ====================

@app.route('/')
def index():
    # Show 30 dogs on homepage (all available dogs)
    dogs = Dog.query.filter_by(is_available=True).limit(30).all()
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
        user_name = f"{first_name} {last_name}"
        
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
        
        if send_verification_email(email, verification_code, user_name):
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
        
        user_name = f"{user.first_name} {user.last_name}"
        if send_verification_email(email, verification_code, user_name):
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
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.is_verified:
                login_user(user, remember=remember_me)
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Please verify your email first. Check your email for the verification code.', 'error')
                return redirect(url_for('verify_email', email=email))
        else:
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
            
            user_name = f"{user.first_name} {user.last_name}"
            if send_password_reset_email(email, reset_code, user_name):
                flash('Password reset code sent to your email', 'success')
                return redirect(url_for('reset_password', email=email))
            else:
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
        
        order = Order(
            user_id=current_user.id,
            dog_id=dog.id,
            amount=dog.price,
            mpesa_number=mpesa_number
        )
        db.session.add(order)
        db.session.commit()
        
        flash('Order created successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
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
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    total_orders = len(orders)
    completed_orders = len([order for order in orders if order.status == 'completed'])
    total_spent = sum(order.amount for order in orders if order.status == 'completed')
    
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

# ==================== ADMIN ROUTES ====================

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    total_dogs = Dog.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    
    completed_orders = Order.query.filter_by(status='completed').all()
    total_revenue = sum(order.amount for order in completed_orders)
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_dogs=total_dogs,
                         total_orders=total_orders,
                         total_users=total_users,
                         pending_orders=pending_orders,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders,
                         recent_users=recent_users)

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
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # Calculate financial metrics
    total_orders = len(orders)
    completed_orders = [o for o in orders if o.status == 'completed']
    pending_orders = [o for o in orders if o.status == 'pending']
    
    # Calculate totals safely (handle None values)
    total_revenue = sum(order.amount for order in completed_orders if order.amount) or 0
    total_orders_value = sum(order.amount for order in orders if order.amount) or 0
    completed_orders_value = sum(order.amount for order in completed_orders if order.amount) or 0
    pending_orders_value = sum(order.amount for order in pending_orders if order.amount) or 0
    
    # Count M-Pesa orders
    mpesa_orders = total_orders
    
    # Get user statistics
    total_users = User.query.count()
    
    # Simulate visitor analytics
    visitor_count = random.randint(500, 1000)
    
    return render_template('admin/orders.html',
                         orders=orders,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         mpesa_orders=mpesa_orders,
                         pending_orders=len(pending_orders),
                         total_users=total_users,
                         visitor_count=visitor_count,
                         total_orders_value=total_orders_value,
                         completed_orders_count=len(completed_orders),
                         completed_orders_value=completed_orders_value,
                         pending_orders_count=len(pending_orders),
                         pending_orders_value=pending_orders_value)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/dog/<int:dog_id>/toggle', methods=['POST'])
@login_required
def toggle_dog_availability(dog_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    dog = Dog.query.get_or_404(dog_id)
    dog.is_available = not dog.is_available
    db.session.commit()
    
    status = "available" if dog.is_available else "unavailable"
    flash(f'Dog {dog.name} is now {status}', 'success')
    return redirect(url_for('admin_dogs'))

@app.route('/admin/order/<order_id>/update', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'completed', 'failed']:
        order.status = new_status
        db.session.commit()
        flash(f'Order status updated to {new_status}', 'success')
    
    return redirect(url_for('admin_orders'))

@app.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'error')
        return redirect(url_for('admin_users'))
    
    user.is_verified = not user.is_verified
    db.session.commit()
    
    status = "activated" if user.is_verified else "deactivated"
    flash(f'User {user.email} has been {status}', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/add-dog', methods=['GET', 'POST'])
@login_required
def add_dog():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        breed = request.form['breed']
        age = int(request.form['age'])
        size = request.form['size']
        color = request.form['color']
        energy_level = request.form['energy_level']
        price = float(request.form['price'])
        description = request.form['description']
        
        if age <= 1:
            age_category = 'puppy'
        elif age <= 3:
            age_category = 'young'
        elif age <= 7:
            age_category = 'adult'
        else:
            age_category = 'senior'
        
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"dog_{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file_path = os.path.join('static/uploads/dogs', filename)
                os.makedirs('static/uploads/dogs', exist_ok=True)
                file.save(file_path)
                image_url = f"/static/uploads/dogs/{filename}"
        
        dog = Dog(
            name=name,
            breed=breed,
            age=age,
            age_category=age_category,
            size=size,
            color=color,
            energy_level=energy_level,
            price=price,
            description=description,
            image_url=image_url,
            is_available=True
        )
        
        db.session.add(dog)
        db.session.commit()
        flash('Dog added successfully!', 'success')
        return redirect(url_for('admin_dogs'))
    
    return render_template('admin/add_dog.html', breeds=DOG_BREEDS)

# ==================== DEBUG ROUTES ====================

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

@app.route('/debug/routes')
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)

@app.route('/test-images')
def test_images():
    breeds = [
        'Labrador.jpg', 'german-shepherd.jpg', 'french-bulldog.jpg',
        'Golden_Retriever.jpg', 'beagle.jpg', 'bulldog.jpg', 'poodle.jpg'
    ]
    return render_template('test_images.html', breeds=breeds)

# API endpoint for order details (for the modal)
@app.route('/api/order/<order_id>')
@login_required
def get_order_details(order_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    order = Order.query.get_or_404(order_id)
    
    return jsonify({
        'id': order.id,
        'user': {
            'first_name': order.user.first_name,
            'last_name': order.user.last_name,
            'email': order.user.email,
            'phone': order.user.phone
        },
        'dog': {
            'name': order.dog.name,
            'breed': order.dog.breed,
            'price': order.dog.price
        },
        'amount': order.amount,
        'mpesa_number': order.mpesa_number,
        'status': order.status,
        'transaction_id': order.transaction_id,
        'created_at': order.created_at.isoformat()
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)