"""
Tizian AI Business Assistant — Flask Backend
Run: python app.py
"""

import os
import re
from datetime import datetime
from functools import wraps

import anthropic
from flask import (Flask, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

# ─── APP SETUP ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tizian-ai-secret-2025-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tizian_ai.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db = SQLAlchemy(app)

# ─── MODELS ───────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id           = db.Column(db.Integer, primary_key=True)
    email        = db.Column(db.String(150), unique=True, nullable=False)
    password_hash= db.Column(db.String(256), nullable=False)
    is_paid      = db.Column(db.Boolean, default=False, nullable=False)
    is_admin     = db.Column(db.Boolean, default=False, nullable=False)
    full_name    = db.Column(db.String(120), nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    activated_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name or '',
            'is_paid': self.is_paid,
            'is_admin': self.is_admin,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'activated_at': self.activated_at.strftime('%Y-%m-%d %H:%M') if self.activated_at else None,
        }

# ─── AI SYSTEM PROMPT ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are Aria, an elite AI Business Assistant for Tizian AI Solutions — a premium business automation company. You are professional, persuasive, emotionally intelligent, and laser-focused on helping businesses grow.

## YOUR ROLE
- Greet prospects warmly and ask smart qualifying questions about their business
- Understand their pain points (missed leads, slow responses, manual tasks)
- Present Tizian AI Solutions as the perfect answer to their problems
- Guide conversations naturally toward booking a consultation or upgrading
- Answer questions about AI automation, lead generation, and business efficiency

## SERVICES YOU REPRESENT
1. **AI Business Assistant** — 24/7 automated customer engagement and lead capture
2. **Lead Qualification Engine** — AI filters and scores prospects automatically  
3. **Business Automation Suite** — End-to-end workflow automation
4. **Custom Enterprise AI** — Bespoke AI solutions for large organisations

## PRICING
- Starter ($49/month): Basic AI assistant, 500 conversations/month, email support
- Professional ($149/month): Unlimited conversations, full automation, priority support
- Enterprise (Custom): White-label, API access, dedicated account manager

## PAYMENT & ACTIVATION
When users want to get started: direct them to pay via PayPal to kingtizian008@gmail.com, then WhatsApp +254742251656 for activation.

## COMMUNICATION STYLE
- Concise and sharp — 2-4 sentences per response unless more detail is needed
- Warm, human, and never robotic
- Use light formatting (bold key points) when helpful
- End with a clear, soft call-to-action
- Never be aggressive or spammy

Remember: you represent a premium brand. Every word should build trust."""

# ─── DECORATORS ───────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required', 'code': 'NOT_LOGGED_IN'}), 401
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def validate_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))

def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, 'Password must be at least 8 characters.'
    if not any(c.isupper() for c in password):
        return False, 'Password must contain at least one uppercase letter.'
    if not any(c.isdigit() for c in password):
        return False, 'Password must contain at least one number.'
    return True, ''

# ─── PAGE ROUTES ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', logged_in='user_id' in session)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    error = None
    if request.method == 'POST':
        email        = request.form.get('email', '').strip().lower()
        full_name    = request.form.get('full_name', '').strip()
        password     = request.form.get('password', '')
        confirm      = request.form.get('confirm_password', '')

        if not email or not password:
            error = 'Email and password are required.'
        elif not validate_email(email):
            error = 'Please enter a valid email address.'
        else:
            valid_pw, pw_msg = validate_password(password)
            if not valid_pw:
                error = pw_msg
            elif password != confirm:
                error = 'Passwords do not match.'
            elif User.query.filter_by(email=email).first():
                error = 'An account with this email already exists.'
            else:
                user = User(email=email, full_name=full_name)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                session['user_id']    = user.id
                session['user_email'] = user.email
                session['is_admin']   = user.is_admin
                return redirect(url_for('dashboard'))

    return render_template('signup.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            error = 'Invalid email or password.'
        else:
            session['user_id']    = user.id
            session['user_email'] = user.email
            session['is_admin']   = user.is_admin
            next_page = request.args.get('next', url_for('dashboard'))
            return redirect(next_page)

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = db.session.get(User, session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/admin')
@login_required
def admin_panel():
    user = db.session.get(User, session['user_id'])
    if not user or not user.is_admin:
        return redirect(url_for('dashboard'))
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin.html', users=users, current_user=user)

# ─── API ROUTES ───────────────────────────────────────────────────────────────
@app.route('/api/status')
@login_required
def api_status():
    user = db.session.get(User, session['user_id'])
    return jsonify(user.to_dict())

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    user = db.session.get(User, session['user_id'])

    if not user.is_paid:
        return jsonify({
            'error': 'Payment required',
            'code': 'NOT_PAID',
            'message': (
                'Your account is pending activation. Please complete payment via PayPal '
                'to kingtizian008@gmail.com, then contact WhatsApp +254742251656 for activation.'
            )
        }), 403

    data = request.get_json(silent=True)
    if not data or not data.get('message', '').strip():
        return jsonify({'error': 'Message is required'}), 400

    message  = data['message'].strip()[:2000]
    history  = data.get('history', [])

    # Build validated message history (last 12 turns)
    messages = []
    for entry in history[-12:]:
        role    = entry.get('role', '')
        content = str(entry.get('content', '')).strip()[:1500]
        if role in ('user', 'assistant') and content:
            messages.append({'role': role, 'content': content})
    messages.append({'role': 'user', 'content': message})

    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({'error': 'AI service not configured. Please contact support.'}), 503

        client   = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=700,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        reply = response.content[0].text
        return jsonify({'reply': reply})

    except anthropic.AuthenticationError:
        return jsonify({'error': 'AI service configuration error. Please contact support.'}), 503
    except anthropic.RateLimitError:
        return jsonify({'error': 'Too many requests. Please wait a moment and try again.'}), 429
    except Exception as e:
        app.logger.error(f'Chat error: {e}')
        return jsonify({'error': 'AI service temporarily unavailable. Please try again.'}), 500

# ─── ADMIN API ROUTES ─────────────────────────────────────────────────────────
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users])

@app.route('/api/admin/activate/<int:user_id>', methods=['POST'])
@admin_required
def admin_activate(user_id):
    user = db.get_or_404(User, user_id)
    user.is_paid      = True
    user.activated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()})

@app.route('/api/admin/deactivate/<int:user_id>', methods=['POST'])
@admin_required
def admin_deactivate(user_id):
    user = db.get_or_404(User, user_id)
    user.is_paid      = False
    user.activated_at = None
    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()})

@app.route('/api/admin/delete/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete(user_id):
    user = db.get_or_404(User, user_id)
    if user.is_admin:
        return jsonify({'error': 'Cannot delete admin users'}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

# ─── INIT ─────────────────────────────────────────────────────────────────────
def init_db():
    """Create tables and default admin account."""
    with app.app_context():
        db.create_all()
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@tizian.ai')
        admin_pass  = os.environ.get('ADMIN_PASSWORD', 'TizianAdmin2025!')
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                email     = admin_email,
                full_name = 'Admin',
                is_admin  = True,
                is_paid   = True,
            )
            admin.set_password(admin_pass)
            db.session.add(admin)
            db.session.commit()
            print(f'[+] Admin created: {admin_email} / {admin_pass}')
        print('[+] Database initialised.')

if __name__ == '__main__':
    init_db()
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
