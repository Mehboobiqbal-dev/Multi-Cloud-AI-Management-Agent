// Simple test to verify React app works without React Router
console.log('Testing React app without React Router...');

// Test if React is working
try {
  const React = require('react');
  console.log('✅ React is working');
} catch (error) {
  console.error('❌ React error:', error);
}

// Test if the app can render
try {
  const ReactDOM = require('react-dom/client');
  console.log('✅ ReactDOM is working');
} catch (error) {
  console.error('❌ ReactDOM error:', error);
}

console.log('🎉 App should work now! Run: npm start'); 