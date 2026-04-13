// auth.js - Handles authentication functionality

function initLoginForm() {
  const toggleButton = document.getElementById('togglePassword');
  const passwordField = document.getElementById('password');

  if (!toggleButton || !passwordField) return;

  toggleButton.addEventListener('click', function() {
    if (passwordField.type === 'password') {
      passwordField.type = 'text';
      toggleButton.textContent = 'إخفاء';
    } else {
      passwordField.type = 'password';
      toggleButton.textContent = 'إظهار';
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  initLoginForm();
});