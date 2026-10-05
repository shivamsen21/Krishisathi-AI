/* ============================================================
   AgroVision AI — profile.js
   Profile page: load user data, update profile, session check
   ============================================================ */

function initProfilePage() {
  const user = AgroVisionAPI.getUser();

  if (!AgroVisionAPI.isAuthenticated() || !user) {
    window.location.href = 'login.html';
    return;
  }

  // Populate display fields
  const name = user.full_name || 'Farmer';
  const email = user.email || '';
  const role = user.role || 'user';
  const initial = name.charAt(0).toUpperCase();

  // Avatar initials
  document.querySelectorAll('.profile-avatar-initial, .sidebar-avatar').forEach(el => {
    el.textContent = initial;
  });

  // Name fields
  document.querySelectorAll('.profile-user-name, .sidebar-user-name').forEach(el => {
    el.textContent = name;
  });

  // Email fields
  document.querySelectorAll('.profile-user-email').forEach(el => {
    el.textContent = email;
  });

  // Role badge
  document.querySelectorAll('.profile-user-role').forEach(el => {
    el.textContent = role === 'admin' ? 'Administrator' : 'Farmer';
  });

  // Pre-fill the edit form
  const fullNameInput = document.getElementById('editFullName');
  const emailInput = document.getElementById('editEmail');
  if (fullNameInput) fullNameInput.value = name;
  if (emailInput) {
    emailInput.value = email;
    emailInput.readOnly = true; // email changes require Supabase Auth flow
  }

  // Hydrate from backend (live fetch)
  AgroVisionAPI.getMe().then(fresh => {
    if (fresh && fresh.full_name && fullNameInput) {
      fullNameInput.value = fresh.full_name;
    }
  }).catch(() => { /* use cached */ });
}

function initProfileForm() {
  const form = document.getElementById('profileEditForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fullName = document.getElementById('editFullName')?.value.trim();
    const btn = form.querySelector('button[type="submit"]');

    if (!fullName || fullName.length < 2) {
      showToast('Please enter a valid full name (minimum 2 characters).', 'warning');
      return;
    }

    btn.disabled = true;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<div class="spinner"></div> Saving...';

    try {
      await AgroVisionAPI.updateProfile({ full_name: fullName });
      showToast('Profile updated successfully!', 'success');

      // Update displayed name
      document.querySelectorAll('.profile-user-name, .sidebar-user-name').forEach(el => {
        el.textContent = fullName;
      });
      document.querySelectorAll('.profile-avatar-initial, .sidebar-avatar').forEach(el => {
        el.textContent = fullName.charAt(0).toUpperCase();
      });
    } catch (err) {
      showToast(err.message || 'Failed to update profile.', 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initProfilePage();
  initProfileForm();
});
