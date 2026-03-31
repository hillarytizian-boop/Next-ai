require('dotenv').config();
const express = require('express');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const session = require('express-session');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

console.log('🚀 Starting Tizian AI Backend...');
console.log('PORT:', process.env.PORT || 3000);
console.log('ENV VARS:', Object.keys(process.env).join(', '));

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(cookieParser());
app.use(session({
  secret: process.env.SESSION_SECRET || 'default-secret',
  resave: false,
  saveUninitialized: true
}));

// Initialize database safely
const dbPath = process.env.DB_PATH || '/tmp/data.db';
console.log('📁 Using DB path:', dbPath);

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('❌ Database connection failed:', err.message);
    process.exit(1);
  }
  console.log('✅ Database connected successfully');
});

// Simple test route
app.get('/', (req, res) => {
  res.send('✅ Tizian AI Backend is running!');
});

// Start server
app.listen(PORT, () => {
  console.log(`✅ Server listening on http://localhost:${PORT}`);
});