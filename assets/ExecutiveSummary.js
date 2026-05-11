// Resumo Executivo — light theme, paleta do dashboard
document.addEventListener('DOMContentLoaded', () => {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        window.lucide.createIcons();
    }

    // Reveal on scroll
    const revealElements = document.querySelectorAll('[data-reveal]');
    if (!('IntersectionObserver' in window)) {
        revealElements.forEach(el => el.classList.add('reveal-visible'));
    } else {
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const delay = parseInt(entry.target.getAttribute('data-delay') || '0', 10);
                    setTimeout(() => entry.target.classList.add('reveal-visible'), delay);
                    revealObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.05, rootMargin: '0px 0px -40px 0px' });
        revealElements.forEach(el => revealObserver.observe(el));
        // Safety net: reveal anything still hidden after 1.5s (mitigates layout race conditions)
        setTimeout(() => {
            revealElements.forEach(el => {
                if (!el.classList.contains('reveal-visible')) el.classList.add('reveal-visible');
            });
        }, 1500);
    }

    // Smooth scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#' || targetId.length < 2) return;
            const targetElement = document.querySelector(targetId);
            if (!targetElement) return;
            e.preventDefault();
            window.scrollTo({ top: targetElement.offsetTop - 72, behavior: 'smooth' });
        });
    });

    // Sticky nav state (light theme)
    const header = document.getElementById('main-nav');
    if (header) {
        const applyNavState = () => {
            if (window.scrollY > 24) header.classList.add('scrolled');
            else header.classList.remove('scrolled');
        };
        applyNavState();
        window.addEventListener('scroll', applyNavState, { passive: true });
    }
});
