# Tizian AI Business Assistant

A production-ready AI Business Assistant web application with manual PayPal payment system, user authentication, and admin dashboard.

---

## 📁 Project Structure

```
tizian-ai/
├── app.py                  # Flask backend (all routes + API)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── templates/
│   ├── index.html          # Landing page
│   ├── login.html          # Sign in page
│   ├── signup.html         # Registration page
│   ├── dashboard.html      # User dashboard + AI chat
│   └── admin.html          # Admin user management panel
└── static/                 # (add CSS/JS/images as needed)
```

---

## ⚙️ Setup Instructions

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Or create `.env` manually:

```env
SECRET_KEY=your-long-random-secret-key-here
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
ADMIN_EMAIL=admin@tizian.ai
ADMIN_PASSWORD=YourSecureAdminPassword123!
FLASK_DEBUG=false
PORT=5000
```

### 3. Get your Anthropic API key

1. Go to https://console.anthropic.com
2. Create an account and generate an API key
3. Add it to your `.env` file

### 4. Initialize and run the app

```bash
python app.py
```

On first run, this will:
- Create the SQLite database (`tizian_ai.db`)
- Create the default admin account
- Start the server on http://localhost:5000

---

## 🚀 Deployment on a VPS (Ubuntu/Debian)

### Install system dependencies

```bash
sudo apt update && sudo apt install python3-pip python3-venv nginx -y
```

### Clone and set up the project

```bash
git clone https://github.com/yourrepo/tizian-ai.git
cd tizian-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Create `.env` and configure

```bash
nano .env
# Fill in your keys
```

### Run with Gunicorn (production)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Set up Nginx as reverse proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Run as a systemd service

Create `/etc/systemd/system/tizian-ai.service`:

```ini
[Unit]
Description=Tizian AI Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/tizian-ai
Environment="PATH=/path/to/tizian-ai/venv/bin"
EnvironmentFile=/path/to/tizian-ai/.env
ExecStart=/path/to/tizian-ai/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable tizian-ai
sudo systemctl start tizian-ai
```

---

## 🔐 Admin Access

| URL | Description |
|-----|-------------|
| `/admin` | Admin user management panel |
| `/api/admin/users` | List all users (JSON) |
| `/api/admin/activate/<id>` | Activate user (POST) |
| `/api/admin/deactivate/<id>` | Deactivate user (POST) |
| `/api/admin/delete/<id>` | Delete user (DELETE) |

Default admin credentials (change in `.env`):
- 
- 

---

## 💳 Payment Flow

1. User signs up → account created with `is_paid = False`
2. User is shown locked dashboard with payment instructions
3. User pays via PayPal to **kingtizian008@gmail.com**
4. User sends proof via WhatsApp to **+254 742 251 656**
5. Admin logs in to `/admin` → clicks "Activate" next to the user
6. User's `is_paid` is set to `True` → full dashboard access granted

---

## 🤖 AI Assistant

The AI assistant uses Claude claude-sonnet-4-20250514 via the Anthropic API.
- System prompt makes it act as "Aria" — an elite business assistant
- Persuasive, lead-qualifying, conversion-focused responses
- Conversation history maintained per session (last 12 turns)
- 700 token limit per response for concise answers

---

## 🔒 Security Features

- Passwords hashed with Werkzeug (PBKDF2)
- Input validation on all forms
- Session-based authentication with HTTP-only cookies
- Route protection via `@login_required` and `@admin_required` decorators
- Input length limits to prevent abuse
- AI conversation history capped at 12 turns

---

## 📞 Business Contact

- **WhatsApp:** +254 742 251 656
- **PayPal:** kingtizian008@gmail.com
- **Support:** https://wa.me/254742251656
