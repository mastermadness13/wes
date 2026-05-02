function initLoginForm() {
  const toggleButton = document.getElementById('togglePassword');
  const passwordField = document.getElementById('password');
  const loginForm = document.getElementById('loginForm');

  if (toggleButton && passwordField) {
    toggleButton.addEventListener('click', function () {
      const isPassword = passwordField.type === 'password';
      passwordField.type = isPassword ? 'text' : 'password';
      toggleButton.setAttribute('aria-label', isPassword ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور');
      const label = toggleButton.querySelector('.password-toggle-label');
      if (label) {
        label.textContent = isPassword ? 'إخفاء' : 'إظهار';
      }
      if (typeof triggerHapticFeedback === 'function') {
        triggerHapticFeedback('soft');
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', function () {
      if (typeof triggerHapticFeedback === 'function') {
        triggerHapticFeedback('medium');
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', function () {
  initLoginForm();
});
