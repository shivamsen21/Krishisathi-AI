/* ============================================================
   AgroVision AI — auth.js
   Login, Register, Forgot Password frontend logic
   ============================================================ */

// ---- Password Visibility Toggle ----
function initPasswordToggle() {
  document.querySelectorAll('.toggle-password').forEach(btn => {
    btn.addEventListener('click', function () {
      const input = this.closest('.input-wrapper').querySelector('input');
      const isText = input.type === 'text';
      input.type = isText ? 'password' : 'text';
      this.innerHTML = isText
        ? '<i class="fas fa-eye"></i>'
        : '<i class="fas fa-eye-slash"></i>';
    });
  });
}

// ---- Password Strength Indicator ----
function initPasswordStrength() {
  const passwordInput = document.getElementById('password');
  const strengthBar   = document.getElementById('strengthBar');
  const strengthLabel = document.getElementById('strengthLabel');
  if (!passwordInput || !strengthBar) return;

  const rules = {
    length:  document.getElementById('rule-length'),
    upper:   document.getElementById('rule-upper'),
    lower:   document.getElementById('rule-lower'),
    number:  document.getElementById('rule-number'),
    special: document.getElementById('rule-special'),
  };

  passwordInput.addEventListener('input', function () {
    const val = this.value;
    let score = 0;

    const checks = {
      length:  val.length >= 8,
      upper:   /[A-Z]/.test(val),
      lower:   /[a-z]/.test(val),
      number:  /\d/.test(val),
      special: /[^A-Za-z0-9]/.test(val),
    };

    Object.entries(checks).forEach(([key, ok]) => {
      if (ok) score++;
      const el = rules[key];
      if (el) {
        el.classList.toggle('valid', ok);
        el.querySelector('i').className = ok ? 'fas fa-check-circle' : 'far fa-circle';
      }
    });

    const segs = strengthBar.querySelectorAll('.strength-seg');
    segs.forEach((s, i) => {
      s.classList.remove('weak', 'medium', 'strong');
      if (i < score) {
        if (score <= 2) s.classList.add('weak');
        else if (score <= 3) s.classList.add('medium');
        else s.classList.add('strong');
      }
    });

    if (strengthLabel) {
      const labels = ['', 'Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
      const colors = ['', '#EF4444', '#EF4444', '#F59E0B', '#10B981', '#10B981'];
      strengthLabel.textContent = labels[score] || '';
      strengthLabel.style.color = colors[score] || '';
    }
  });
}

// ---- Confirm Password Validation ----
function initConfirmPassword() {
  const password = document.getElementById('password');
  const confirm  = document.getElementById('confirmPassword');
  const error    = document.getElementById('confirmError');
  if (!password || !confirm) return;

  function validate() {
    if (confirm.value && confirm.value !== password.value) {
      confirm.classList.add('error');
      if (error) { error.textContent = '⚠ Passwords do not match'; error.style.display = 'flex'; }
      return false;
    } else {
      confirm.classList.remove('error');
      if (error) error.style.display = 'none';
      return true;
    }
  }
  confirm.addEventListener('input', validate);
  password.addEventListener('input', validate);
  return validate;
}

// ---- Form Validation ----
function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function setFieldError(fieldId, message) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  field.classList.add('error');
  let errEl = field.closest('.form-group')?.querySelector('.form-error');
  if (errEl) errEl.textContent = message;
}

function clearFieldError(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  field.classList.remove('error');
  let errEl = field.closest('.form-group')?.querySelector('.form-error');
  if (errEl) errEl.textContent = '';
}

// ---- Login Form ----
function initLoginForm() {
  const form = document.getElementById('loginForm');
  if (!form) return;

  // Clear errors on input
  form.querySelectorAll('input').forEach(input => {
    input.addEventListener('input', () => clearFieldError(input.id));
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const btn      = form.querySelector('.auth-submit-btn');
    let valid = true;

    if (!email) { setFieldError('email', '⚠ Email is required'); valid = false; }
    else if (!validateEmail(email)) { setFieldError('email', '⚠ Please enter a valid email'); valid = false; }
    if (!password) { setFieldError('password', '⚠ Password is required'); valid = false; }

    if (!valid) return;

    btn.disabled = true;
    btn.innerHTML = '<div class="spinner"></div> Logging in...';

    try {
      const res = await AgroVisionAPI.login(email, password);
      showToast('Login successful! Redirecting...', 'success');
      setTimeout(() => {
        if (res.user && res.user.role === 'admin') {
          window.location.href = 'admin-dashboard.html';
        } else {
          window.location.href = 'dashboard.html';
        }
      }, 700);
    } catch (err) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
      const msg = err.message || 'Invalid email or password.';
      setFieldError('password', `⚠ ${msg}`);
      showToast(msg, 'error');
    }
  });
}

// ---- Register Form ----
function initRegisterForm() {
  const form = document.getElementById('registerForm');
  if (!form) return;
  const confirmValidator = initConfirmPassword();

  form.querySelectorAll('input').forEach(input => {
    input.addEventListener('input', () => clearFieldError(input.id));
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name     = document.getElementById('fullName').value.trim();
    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirm  = document.getElementById('confirmPassword').value;
    const btn      = form.querySelector('.auth-submit-btn');
    let valid = true;

    if (!name) { setFieldError('fullName', '⚠ Full name is required'); valid = false; }
    if (!email) { setFieldError('email', '⚠ Email is required'); valid = false; }
    else if (!validateEmail(email)) { setFieldError('email', '⚠ Enter a valid email address'); valid = false; }
    if (!password || password.length < 8) { setFieldError('password', '⚠ Password must be at least 8 characters'); valid = false; }
    if (confirm !== password) { valid = false; }

    if (!valid) return;

    btn.disabled = true;
    btn.innerHTML = '<div class="spinner"></div> Creating Account...';

    try {
      await AgroVisionAPI.register(name, email, password);
      showToast('Account created successfully! Redirecting...', 'success');
      setTimeout(() => { window.location.href = 'dashboard.html'; }, 800);
    } catch (err) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
      const msg = err.message || 'Registration failed.';
      showToast(msg, 'error');
      setFieldError('email', `⚠ ${msg}`);
    }
  });
}

// ---- Forgot Password Form ----
function initForgotForm() {
  const form    = document.getElementById('forgotForm');
  const section = document.getElementById('forgotFormSection');
  const success = document.getElementById('successMessage');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value.trim();
    const btn   = form.querySelector('.auth-submit-btn');
    if (!email || !validateEmail(email)) {
      setFieldError('email', '⚠ Enter a valid email address'); return;
    }
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner"></div> Sending...';

    try {
      await AgroVisionAPI.forgotPassword(email);
      if (section) section.style.display = 'none';
      else form.style.display = 'none';
      if (success) success.classList.remove('hidden');
    } catch (err) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Reset Link';
      showToast(err.message || 'Failed to send reset email.', 'error');
    }
  });
}


document.addEventListener('DOMContentLoaded', () => {
  initPasswordToggle();
  initPasswordStrength();
  initLoginForm();
  initRegisterForm();
  initForgotForm();
});
