document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initBackButtons();
  initHeroSlider();
  initSaveToggle();
  initPropertyGallery();
  initReadMore();
  initFilterAccordion();
  initMobileFilterDrawer();
  initBudgetRangeSlider();
  initSingleRangeSliders();
  initContactSheet();
  initVisitSheet();
  initScrollReveal();
  initSortSelect();
});

function initSortSelect() {
  const select = document.getElementById('sortSelect');
  if (!select) return;
  select.addEventListener('change', () => {
    const params = new URLSearchParams(window.location.search);
    params.set('sort', select.value);
    params.delete('page');
    window.location.search = params.toString();
  });
}

function initScrollReveal() {
  const targets = document.querySelectorAll('[data-reveal]');
  if (!targets.length) return;

  if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    targets.forEach((el) => el.classList.add('is-visible'));
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

  targets.forEach((el) => observer.observe(el));

  // Safety net: content must never stay invisible if something goes wrong
  // (a slow/odd scroll container, a browser quirk, etc.) — force everything
  // visible after a few seconds no matter what.
  setTimeout(() => targets.forEach((el) => el.classList.add('is-visible')), 4000);
}

function getCsrfToken() {
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
}

function initMobileNav() {
  const toggle = document.getElementById('navToggle');
  const nav = document.getElementById('mobileNav');
  const backdrop = document.getElementById('mobileNavBackdrop');
  const closeBtn = document.getElementById('mobileNavClose');
  if (!toggle || !nav || !backdrop) return;

  function open() {
    nav.classList.add('is-open');
    backdrop.hidden = false;
    requestAnimationFrame(() => backdrop.classList.add('is-open'));
    document.body.classList.add('nav-open');
    toggle.setAttribute('aria-expanded', 'true');
  }

  function close() {
    nav.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    document.body.classList.remove('nav-open');
    toggle.setAttribute('aria-expanded', 'false');
    setTimeout(() => { backdrop.hidden = true; }, 250);
  }

  toggle.addEventListener('click', () => {
    nav.classList.contains('is-open') ? close() : open();
  });
  if (closeBtn) closeBtn.addEventListener('click', close);
  backdrop.addEventListener('click', close);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && nav.classList.contains('is-open')) close();
  });
}

function initBackButtons() {
  document.querySelectorAll('.js-back-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const fallback = btn.dataset.fallback;
      const cameFromSameSite = document.referrer && document.referrer.startsWith(window.location.origin);
      if (cameFromSameSite && window.history.length > 1) {
        window.history.back();
      } else if (fallback) {
        window.location.href = fallback;
      } else {
        window.history.back();
      }
    });
  });
}

function initContactSheet() {
  const sheet = document.getElementById('contactSheet');
  const backdrop = document.getElementById('contactSheetBackdrop');
  const closeBtn = document.getElementById('contactSheetClose');
  const triggers = document.querySelectorAll('.js-contact-trigger');
  if (!sheet || !backdrop || !triggers.length) return;

  let inquiryLogged = false;
  function open() {
    sheet.classList.add('is-open');
    backdrop.classList.add('is-open');
    document.body.classList.add('nav-open');
    if (!inquiryLogged) {
      const inquiryUrl = triggers[0].dataset.inquiryUrl;
      if (inquiryUrl) {
        inquiryLogged = true;
        fetch(inquiryUrl, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCsrfToken(), 'Content-Type': 'application/x-www-form-urlencoded' },
          body: '',
        }).catch(() => {});
      }
    }
  }
  function close() {
    sheet.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    document.body.classList.remove('nav-open');
  }

  triggers.forEach((btn) => btn.addEventListener('click', open));
  backdrop.addEventListener('click', close);
  if (closeBtn) closeBtn.addEventListener('click', close);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sheet.classList.contains('is-open')) close();
  });
}

function initVisitSheet() {
  const sheet = document.getElementById('visitSheet');
  const backdrop = document.getElementById('visitSheetBackdrop');
  const closeBtn = document.getElementById('visitSheetClose');
  const triggers = document.querySelectorAll('.js-visit-trigger');
  if (!sheet || !backdrop || !triggers.length) return;

  function open() {
    sheet.classList.add('is-open');
    backdrop.classList.add('is-open');
    document.body.classList.add('nav-open');
  }
  function close() {
    sheet.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    document.body.classList.remove('nav-open');
  }

  triggers.forEach((btn) => btn.addEventListener('click', open));
  backdrop.addEventListener('click', close);
  if (closeBtn) closeBtn.addEventListener('click', close);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sheet.classList.contains('is-open')) close();
  });
}

function initHeroSlider() {
  const slider = document.querySelector('.js-hero-slider');
  if (!slider) return;

  const images = [
    'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=70',
    'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=70',
    'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=70',
    'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=70',
    'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=70',
  ];

  const img = slider.querySelector('img');
  const counter = slider.querySelector('.hero__media-counter');
  const prevBtn = slider.querySelector('.hero__media-arrow--prev');
  const nextBtn = slider.querySelector('.hero__media-arrow--next');
  let index = 0;

  function render() {
    img.src = images[index];
    counter.textContent = `${index + 1} / ${images.length}`;
  }

  prevBtn.addEventListener('click', () => {
    index = (index - 1 + images.length) % images.length;
    render();
  });
  nextBtn.addEventListener('click', () => {
    index = (index + 1) % images.length;
    render();
  });
}

function initSaveToggle() {
  document.querySelectorAll('.js-save-toggle').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const url = btn.dataset.saveUrl;
      if (!url) {
        btn.classList.toggle('is-saved');
        return;
      }
      btn.disabled = true;
      fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken(), 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `next=${encodeURIComponent(window.location.pathname + window.location.search)}`,
      })
        .then(() => { btn.classList.toggle('is-saved'); })
        .catch(() => {})
        .finally(() => { btn.disabled = false; });
    });
  });
}

function initPropertyGallery() {
  const gallery = document.querySelector('.js-gallery');
  if (!gallery) return;

  const heroImg = gallery.querySelector('#galleryHeroImg');
  const thumbs = Array.from(gallery.querySelectorAll('.js-gallery-thumb'));
  if (!heroImg || thumbs.length === 0) return;

  const images = thumbs.map((t) => t.dataset.src);
  let index = 0;

  function render() {
    heroImg.src = images[index];
    thumbs.forEach((t, i) => t.classList.toggle('is-active', i === index));
  }

  gallery.querySelector('.gallery__arrow--prev').addEventListener('click', () => {
    index = (index - 1 + images.length) % images.length;
    render();
  });
  gallery.querySelector('.gallery__arrow--next').addEventListener('click', () => {
    index = (index + 1) % images.length;
    render();
  });
  thumbs.forEach((thumb, i) => {
    thumb.addEventListener('click', () => {
      index = i;
      render();
    });
  });
}

function initReadMore() {
  const text = document.getElementById('aboutText');
  const toggle = document.getElementById('readMoreToggle');
  if (!text || !toggle) return;

  toggle.addEventListener('click', () => {
    const expanded = text.classList.toggle('is-clamped') === false;
    toggle.firstChild.textContent = expanded ? 'Show less ' : 'Read more ';
    toggle.classList.toggle('is-open', expanded);
  });
}

function initFilterAccordion() {
  document.querySelectorAll('.filter-group__head').forEach((head) => {
    head.addEventListener('click', () => {
      head.closest('.filter-group').classList.toggle('is-collapsed');
    });
  });
}

function initMobileFilterDrawer() {
  const panel = document.getElementById('filtersPanel');
  const backdrop = document.getElementById('filtersBackdrop');
  const trigger = document.getElementById('filtersTrigger');
  const closeBtn = document.getElementById('filtersClose');
  const applyBtn = document.getElementById('filtersApply');
  if (!panel || !backdrop || !trigger) return;

  function open() {
    panel.classList.add('is-open');
    backdrop.classList.add('is-open');
  }
  function close() {
    panel.classList.remove('is-open');
    backdrop.classList.remove('is-open');
  }

  trigger.addEventListener('click', open);
  backdrop.addEventListener('click', close);
  if (closeBtn) closeBtn.addEventListener('click', close);
  if (applyBtn) applyBtn.addEventListener('click', close);
}

function initBudgetRangeSlider() {
  const wrap = document.getElementById('budgetSlider');
  if (!wrap) return;

  const minInput = document.getElementById('budgetMin');
  const maxInput = document.getElementById('budgetMax');
  const fill = wrap.querySelector('.range-slider__fill');
  const minLabel = document.getElementById('budgetMinLabel');
  const maxLabel = document.getElementById('budgetMaxLabel');
  const rupees = (n) => '₹' + Number(n).toLocaleString('en-IN');

  function render() {
    let min = parseInt(minInput.value, 10);
    let max = parseInt(maxInput.value, 10);
    if (min > max) { [min, max] = [max, min]; }

    const range = Number(minInput.max) - Number(minInput.min);
    const left = ((min - minInput.min) / range) * 100;
    const right = ((max - minInput.min) / range) * 100;
    fill.style.left = left + '%';
    fill.style.width = (right - left) + '%';

    minLabel.textContent = rupees(min);
    maxLabel.textContent = max >= Number(maxInput.max) ? rupees(max) + '+' : rupees(max);
  }

  minInput.addEventListener('input', render);
  maxInput.addEventListener('input', render);
  render();
}

function initSingleRangeSliders() {
  document.querySelectorAll('.range-slider--single').forEach((wrap) => {
    const input = wrap.querySelector('input[type="range"]');
    const fill = wrap.querySelector('.range-slider__fill');
    if (!input || !fill) return;

    function render() {
      const min = Number(input.min) || 0;
      const max = Number(input.max) || 100;
      const pct = ((Number(input.value) - min) / (max - min)) * 100;
      fill.style.left = '0';
      fill.style.width = pct + '%';
    }

    input.addEventListener('input', render);
    render();
  });
}
