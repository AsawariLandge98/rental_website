document.addEventListener('DOMContentLoaded', () => {
  initDashboardSidebar();
  initDashDropdown('dashNotifTrigger', 'dashNotifPanel');
  initDashDropdown('dashAccountTrigger', 'dashAccountMenu');
  initSettingsTabs();
});

function initDashboardSidebar() {
  const toggle = document.getElementById('dashSidebarToggle');
  const sidebar = document.getElementById('dashSidebar');
  const backdrop = document.getElementById('dashSidebarBackdrop');
  if (!toggle || !sidebar || !backdrop) return;

  function open() {
    sidebar.classList.add('is-open');
    backdrop.classList.add('is-open');
    document.body.classList.add('nav-open');
    toggle.setAttribute('aria-expanded', 'true');
  }
  function close() {
    sidebar.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    document.body.classList.remove('nav-open');
    toggle.setAttribute('aria-expanded', 'false');
  }

  toggle.addEventListener('click', () => {
    sidebar.classList.contains('is-open') ? close() : open();
  });
  backdrop.addEventListener('click', close);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar.classList.contains('is-open')) close();
  });
}

function initDashDropdown(triggerId, panelId) {
  const trigger = document.getElementById(triggerId);
  const panel = document.getElementById(panelId);
  if (!trigger || !panel) return;

  function close() {
    panel.classList.remove('is-open');
    trigger.setAttribute('aria-expanded', 'false');
  }
  function open() {
    document.querySelectorAll('.dash-notif__panel.is-open, .dash-account__menu.is-open').forEach((el) => {
      if (el !== panel) el.classList.remove('is-open');
    });
    panel.classList.add('is-open');
    trigger.setAttribute('aria-expanded', 'true');
  }

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    panel.classList.contains('is-open') ? close() : open();
  });
  document.addEventListener('click', (e) => {
    if (!panel.contains(e.target) && e.target !== trigger) close();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });
}

function initSettingsTabs() {
  const links = document.querySelectorAll('.settings-nav a');
  const panels = document.querySelectorAll('.settings-panel');
  if (!links.length || !panels.length) return;

  links.forEach((link) => {
    link.addEventListener('click', (e) => {
      const target = link.dataset.panel;
      if (!target) return;
      e.preventDefault();
      links.forEach((l) => l.classList.toggle('is-active', l === link));
      panels.forEach((p) => p.classList.toggle('is-active', p.id === target));
      history.replaceState(null, '', `#${target}`);
    });
  });

  const hash = window.location.hash.replace('#', '');
  const initial = document.getElementById(hash) ? hash : panels[0].id;
  panels.forEach((p) => p.classList.toggle('is-active', p.id === initial));
  links.forEach((l) => l.classList.toggle('is-active', l.dataset.panel === initial));
}
