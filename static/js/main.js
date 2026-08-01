document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initHeroSlider();
  initHeroMobileSlider();
  initSaveToggle();
  initPropertyGallery();
  initReadMore();
  initFilterAccordion();
  initMobileFilterDrawer();
  initBudgetRangeSlider();
});

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

function initHeroMobileSlider() {
  const slider = document.querySelector('.js-hero-mobile-slider');
  if (!slider) return;

  const track = slider.querySelector('.hero-mobile__track');
  if (!track) return;

  const slides = Array.from(track.children);
  const dots = Array.from(slider.querySelectorAll('.hero__media-dots button'));
  const prevBtn = slider.querySelector('.js-hero-mobile-prev');
  const nextBtn = slider.querySelector('.js-hero-mobile-next');
  let current = 0;
  let ticking = false;

  function currentIndex() {
    return Math.round(track.scrollLeft / track.clientWidth);
  }

  function setActiveDot() {
    current = currentIndex();
    dots.forEach((dot, i) => dot.classList.toggle('is-active', i === current));
    ticking = false;
  }

  function goTo(index) {
    const clamped = (index + slides.length) % slides.length;
    slides[clamped].scrollIntoView({ behavior: 'smooth', inline: 'start', block: 'nearest' });
  }

  track.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(setActiveDot);
      ticking = true;
    }
  });

  dots.forEach((dot, i) => {
    dot.addEventListener('click', () => { goTo(i); restartAutoplay(); });
  });

  if (prevBtn) prevBtn.addEventListener('click', () => { goTo(currentIndex() - 1); restartAutoplay(); });
  if (nextBtn) nextBtn.addEventListener('click', () => { goTo(currentIndex() + 1); restartAutoplay(); });

  // Auto-advance every 4s; pause while the user is actively swiping/touching,
  // and stop entirely once they leave the tab so it doesn't run needlessly.
  let autoplayTimer = null;
  function startAutoplay() {
    stopAutoplay();
    autoplayTimer = setInterval(() => goTo(currentIndex() + 1), 4000);
  }
  function stopAutoplay() {
    if (autoplayTimer) clearInterval(autoplayTimer);
    autoplayTimer = null;
  }
  function restartAutoplay() {
    stopAutoplay();
    startAutoplay();
  }

  track.addEventListener('touchstart', stopAutoplay, { passive: true });
  track.addEventListener('touchend', restartAutoplay, { passive: true });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stopAutoplay();
    else startAutoplay();
  });

  startAutoplay();
}

function initSaveToggle() {
  document.querySelectorAll('.js-save-toggle').forEach((btn) => {
    btn.addEventListener('click', () => {
      btn.classList.toggle('is-saved');
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
