document.addEventListener('DOMContentLoaded', () => {
  initPasswordToggles();
  initAccountTypeCards();
  initRoleToggle();
  initPasswordStrength();
});

function initPasswordToggles() {
  document.querySelectorAll('.js-password-toggle').forEach((btn) => {
    const wrap = btn.closest('.field-with-icon');
    const input = wrap ? wrap.querySelector('.js-password-input') : null;
    if (!input) return;

    btn.addEventListener('click', () => {
      const isHidden = input.type === 'password';
      input.type = isHidden ? 'text' : 'password';
      btn.innerHTML = '';
      btn.appendChild(makeIcon(isHidden ? 'eye-off' : 'eye'));
      btn.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
    });
  });
}

function makeIcon(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor');
  svg.setAttribute('stroke-width', '1.8');
  svg.setAttribute('stroke-linecap', 'round');
  svg.setAttribute('stroke-linejoin', 'round');
  svg.classList.add('icon-sm');
  const paths = {
    eye: ['M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'],
    'eye-off': [
      'M3 3l18 18',
      'M10.6 5.6A10.6 10.6 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a15 15 0 0 1-3 3.7M6.3 6.9C3.7 8.6 2.5 11 2.5 11S6 17.5 12 17.5c1.2 0 2.3-.2 3.3-.6',
      'M9.5 9.6a3 3 0 0 0 4.2 4.2',
    ],
  };
  (paths[name] || []).forEach((d) => {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', d);
    svg.appendChild(path);
  });
  return svg;
}

function initAccountTypeCards() {
  const cards = document.querySelectorAll('.js-account-type');
  if (!cards.length) return;
  const hiddenInput = document.getElementById('regAccountType');
  cards.forEach((card) => {
    card.addEventListener('click', () => {
      cards.forEach((c) => c.classList.remove('is-selected'));
      card.classList.add('is-selected');
      if (hiddenInput) hiddenInput.value = card.dataset.type;
    });
  });
}

function initRoleToggle() {
  const toggle = document.getElementById('roleToggle');
  if (!toggle) return;
  const hiddenInput = document.getElementById('adminRole');
  const buttons = Array.from(toggle.querySelectorAll('button'));
  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      buttons.forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      if (hiddenInput) hiddenInput.value = btn.dataset.role;
    });
  });
}

function initPasswordStrength() {
  const input = document.querySelector('.js-strength-input');
  const checklist = document.getElementById('fpChecklist');
  if (!input || !checklist) return;

  const rules = {
    length: (v) => v.length >= 8,
    case: (v) => /[a-z]/.test(v) && /[A-Z]/.test(v),
    number: (v) => /[0-9]/.test(v) || /[^A-Za-z0-9]/.test(v),
  };

  input.addEventListener('input', () => {
    const value = input.value;
    checklist.querySelectorAll('li[data-rule]').forEach((li) => {
      const rule = rules[li.dataset.rule];
      li.classList.toggle('is-valid', rule ? rule(value) : false);
    });
  });
}
