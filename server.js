require('dotenv').config();
const express = require('express');
const path = require('path');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cookieParser = require('cookie-parser');
const cors = require('cors');
const db = require('./database');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(cors());
app.use(express.static('public'));

// Set EJS as template engine (or serve HTML directly)
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Auth middleware to check JWT token
const authenticateToken = (req, res, next) => {
  const token = req.cookies.token || req.headers.authorization?.split(' ')[1];
  
  if (!token) {
    req.user = null;
    return next();
  }

  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) req.user = null;
    else req.user = user;
    next();
  });
};

// Make user available to all templates
app.use(authenticateToken);
app.use((req, res, next) => {
  res.locals.logged_in = !!req.user;
  res.locals.user = req.user;
  next();
});

// ========== ROUTES ==========

// Serve your index.html (modified to work with backend)
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'index.html'));
});

// Signup page
app.get('/signup', (req, res) => {
  if (req.user) return res.redirect('/dashboard');
  res.sendFile(path.join(__dirname, 'views', 'signup.html'));
});

// Login page
app.get('/login', (req, res) => {
  if (req.user) return res.redirect('/dashboard');
  res.sendFile(path.join(__dirname, 'views', 'login.html'));
});

// Dashboard
app.get('/dashboard', authenticateToken, (req, res) => {
  if (!req.user) return res.redirect('/login');
  
  db.get('SELECT * FROM users WHERE id = ?', [req.user.id], (err, user) => {
    if (err || !user) return res.redirect('/login');
    
    // Get user's payments
    db.all('SELECT * FROM payments WHERE user_id = ? ORDER BY id DESC', [user.id], (err, payments) => {
      res.render('dashboard', { user, payments });
    });
  });
});

// API: Signup
app.post('/api/signup', async (req, res) => {
  const { name, email, password, plan = 'starter' } = req.body;
  
  if (!name || !email || !password) {
    return res.status(400).json({ error: 'All fields are required' });
  }

  try {
    const hashedPassword = await bcrypt.hash(password, 10);
    
    db.run(
      'INSERT INTO users (name, email, password, plan, status) VALUES (?, ?, ?, ?, ?)',
      [name, email, hashedPassword, plan, 'pending'],
      function(err) {
        if (err) {
          if (err.message.includes('UNIQUE')) {
            return res.status(400).json({ error: 'Email already registered' });
          }
          return res.status(500).json({ error: err.message });
        }
        
        // Create token
        const token = jwt.sign(
          { id: this.lastID, email, name, plan },
          process.env.JWT_SECRET,
          { expiresIn: '7d' }
        );
        
        res.cookie('token', token, { httpOnly: true, maxAge: 7 * 24 * 60 * 60 * 1000 });
        res.json({ success: true, redirect: '/dashboard' });
      }
    );
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

// API: Login
app.post('/api/login', (req, res) => {
  const { email, password } = req.body;
  
  db.get('SELECT * FROM users WHERE email = ?', [email], async (err, user) => {
    if (err || !user) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }
    
    const validPassword = await bcrypt.compare(password, user.password);
    if (!validPassword) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }
    
    const token = jwt.sign(
      { id: user.id, email: user.email, name: user.name, plan: user.plan },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );
    
    res.cookie('token', token, { httpOnly: true, maxAge: 7 * 24 * 60 * 60 * 1000 });
    res.json({ success: true, redirect: '/dashboard' });
  });
});

// API: Logout
app.post('/api/logout', (req, res) => {
  res.clearCookie('token');
  res.json({ success: true });
});

// API: Submit payment proof
app.post('/api/payment-proof', authenticateToken, (req, res) => {
  if (!req.user) return res.status(401).json({ error: 'Unauthorized' });
  
  const { amount, plan, paypal_email } = req.body;
  
  db.run(
    'INSERT INTO payments (user_id, amount, plan, paypal_email, status) VALUES (?, ?, ?, ?, ?)',
    [req.user.id, amount, plan, paypal_email, 'pending'],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, message: 'Payment proof submitted. We will verify within 2-4 hours.' });
    }
  );
});

// API: Save contact message
app.post('/api/contact', (req, res) => {
  const { name, email, message } = req.body;
  
  if (!name || !email || !message) {
    return res.status(400).json({ error: 'All fields are required' });
  }
  
  db.run(
    'INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)',
    [name, email, message],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, message: 'Message received! We will respond via WhatsApp.' });
    }
  );
});

// Admin: Get pending payments (protected - you should add admin check)
app.get('/api/admin/payments', authenticateToken, (req, res) => {
  if (!req.user || req.user.email !== 'admin@tizian.ai') {
    return res.status(403).json({ error: 'Admin access required' });
  }
  
  db.all(`
    SELECT p.*, u.name, u.email 
    FROM payments p 
    JOIN users u ON p.user_id = u.id 
    WHERE p.status = 'pending'
    ORDER BY p.proof_sent_at DESC
  `, (err, payments) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ payments });
  });
});

// Admin: Verify payment and activate user
app.post('/api/admin/verify-payment/:paymentId', authenticateToken, (req, res) => {
  if (!req.user || req.user.email !== 'admin@tizian.ai') {
    return res.status(403).json({ error: 'Admin access required' });
  }
  
  const { paymentId } = req.params;
  
  db.get('SELECT * FROM payments WHERE id = ?', [paymentId], (err, payment) => {
    if (err || !payment) return res.status(404).json({ error: 'Payment not found' });
    
    // Update payment status
    db.run(
      'UPDATE payments SET status = ?, verified_by = ?, verified_at = CURRENT_TIMESTAMP WHERE id = ?',
      ['verified', req.user.email, paymentId],
      (err) => {
        if (err) return res.status(500).json({ error: err.message });
        
        // Activate user
        db.run(
          'UPDATE users SET status = ?, activated_at = CURRENT_TIMESTAMP WHERE id = ?',
          ['active', payment.user_id],
          (err) => {
            if (err) return res.status(500).json({ error: err.message });
            res.json({ success: true, message: 'User activated successfully' });
          }
        );
      }
    );
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`✅ Server running on http://localhost:${PORT}`);
  console.log(`📧 Admin login: admin@tizian.ai / admin123`);
});