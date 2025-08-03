import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';
import reportWebVitals from './reportWebVitals';

// Add global error handler for WebSocket connection issues
window.addEventListener('error', (event) => {
  if (event.message && (
    event.message.includes('WebSocket connection') ||
    event.message.includes('WebSocket is already in CLOSING or CLOSED state') ||
    event.message.includes('Failed to construct \'WebSocket\'') ||
    event.message.includes('Error in connection establishment')
  )) {
    console.warn('WebSocket connection issue detected:', event.message);
    // Prevent the error from showing in console
    event.preventDefault();
    return true;
  }
});

// Also handle unhandled promise rejections related to WebSocket
window.addEventListener('unhandledrejection', (event) => {
  if (event.reason && event.reason.message && (
    event.reason.message.includes('WebSocket') ||
    event.reason.message.includes('ws://') ||
    event.reason.message.includes('wss://')
  )) {
    console.warn('WebSocket promise rejection:', event.reason.message);
    // Prevent the error from showing in console
    event.preventDefault();
    return true;
  }
});

const theme = createTheme();

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://cra.link/PWA
// Using unregister() to avoid WebSocket connection issues
serviceWorkerRegistration.unregister();

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
