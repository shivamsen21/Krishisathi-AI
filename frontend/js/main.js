/* ============================================================
   AgroVision AI — main.js
   Global utilities: sidebar toggle, toast, navbar scroll
   ============================================================ */

// ---- Toast Notifications ----
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-text">${message}</span>
    <span class="toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideInRight 0.3s ease reverse';
    setTimeout(() => toast.remove(), 280);
  }, 3800);
}

// ---- Sidebar Toggle ----
function initSidebar() {
  const sidebar  = document.querySelector('.sidebar');
  const overlay  = document.querySelector('.sidebar-overlay');
  const hamburger = document.querySelector('.hamburger');
  if (!sidebar) return;

  function openSidebar() {
    sidebar.classList.add('open');
    if (overlay) overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (hamburger) hamburger.addEventListener('click', openSidebar);
  if (overlay)   overlay.addEventListener('click', closeSidebar);

  // Close on nav link click (mobile)
  document.querySelectorAll('.sidebar-link').forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 768) closeSidebar();
    });
  });
}

// ---- Landing Navbar Scroll Effect ----
function initNavScroll() {
  const nav = document.querySelector('.site-nav');
  if (!nav) return;
  function update() {
    nav.classList.toggle('scrolled', window.scrollY > 50);
  }
  update();
  window.addEventListener('scroll', update, { passive: true });
}

// ---- Mobile Menu (Landing) ----
function initMobileMenu() {
  const hamburger = document.querySelector('.nav-hamburger');
  const menu = document.querySelector('.mobile-menu');
  if (!hamburger || !menu) return;
  hamburger.addEventListener('click', () => menu.classList.toggle('open'));
  document.addEventListener('click', (e) => {
    if (!hamburger.contains(e.target) && !menu.contains(e.target)) {
      menu.classList.remove('open');
    }
  });
}

// ---- Smooth Scroll for Anchor Links ----
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const offset = 80;
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
        document.querySelector('.mobile-menu')?.classList.remove('open');
      }
    });
  });
}

// ---- Animate on Scroll ----
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
}

// ---- Active sidebar link ----
function setActiveSidebarLink() {
  const path = window.location.pathname.split('/').pop();
  document.querySelectorAll('.sidebar-link').forEach(link => {
    link.classList.remove('active');
    if (link.getAttribute('href') === path) link.classList.add('active');
  });
}

// ---- App Nav User Menu ----
function initUserMenu() {
  const trigger = document.querySelector('.nav-user-trigger');
  const menu    = document.querySelector('.nav-user-menu');
  if (!trigger || !menu) return;
  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    menu.classList.toggle('open');
  });
  document.addEventListener('click', () => menu.classList.remove('open'));
}

function initAuthHeader() {
  if (typeof AgroVisionAPI !== 'undefined') {
    const user = AgroVisionAPI.getUser();
    if (user && user.full_name) {
      const name = user.full_name;
      const initial = name.charAt(0).toUpperCase();
      document.querySelectorAll('.sidebar-user-name').forEach(el => el.textContent = name);
      document.querySelectorAll('.sidebar-avatar').forEach(el => {
        if (!el.closest('.sidebar-bottom') && el.querySelector('a')) {
          el.querySelector('a').textContent = initial;
        } else {
          el.textContent = initial;
        }
      });
    }

    // Bind logout links — call API logout then redirect
    document.querySelectorAll('a').forEach(link => {
      const text = (link.textContent || '').toLowerCase().trim();
      const hasLogoutIcon = !!link.querySelector('.fa-sign-out-alt');
      if (text.includes('logout') || hasLogoutIcon) {
        link.addEventListener('click', async (e) => {
          e.preventDefault();
          try {
            await AgroVisionAPI.logout();
          } catch (_) {
            AgroVisionAPI.clearAuth();
          }
          const isAdmin = document.querySelector('[data-admin-page]') !== null;
          window.location.href = isAdmin ? 'admin-login.html' : 'login.html';
        });
      }
    });
  }
}

// ---- DOMContentLoaded ----
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initNavScroll();
  initMobileMenu();
  initSmoothScroll();
  initScrollAnimations();
  setActiveSidebarLink();
  initUserMenu();
  initAuthHeader();
});
