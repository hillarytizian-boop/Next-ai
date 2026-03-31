require('dotenv').config();
const express = require('express');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const session = require('express-session');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// --- DEBUG LOGGING START ---
console.log('🚀 Starting Tizian AI Backend...');
console.log('PORT:', process.env.PORT || '5000');
console.log('ENV VARS:', Object.keys(process.env).join(', '));
// --- DEBUG LOGGING END ---

const app = express();
const PORT = process.env.PORT || 5000; // Use Render's port or default to 5000

// Middleware
app.use(cors());
app.use(cookieParser());
app.use(session({
  secret: process.env.SESSION_SECRET || 'default-secret-key',
  resave: false,
  saveUninitialized: true,
  cookie: { secure: false } // Set to true if using HTTPS in production
}));

// --- DATABASE SETUP (Safe for Render) ---
// We use /tmp because Render's free tier doesn't allow writing to the project folder directly
const dbPath = process.env.DB_PATH || '/tmp/data.db';
console.log('📁 Initializing Database at:', dbPath);

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('❌ ERROR: Failed to connect to database:', err.message);
    // Exit immediately so Render knows something is wrong
    process.exit(1); 
  }
  console.log('✅ Database connected successfully');
  
  // Optional: Create a test table here if needed
  // db.run("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)");
});

// --- ROUTES ---
app.get('/', (req, res) => {
  res.send('✅ Tizian AI Backend is running!');
});

// Add your other routes here...
// Example:
// app.get('/api/test', (req, res) => { ... });

// --- START SERVER ---
app.listen(PORT, () => {
  console.log(`✅ Server is listening on port ${PORT}`);
});