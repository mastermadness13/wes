document.addEventListener('DOMContentLoaded', function () {
    const theme = localStorage.getItem('theme') || 'dark';
    const font = localStorage.getItem('fontSize') || 'font-medium';
    const timeFormat = localStorage.getItem('timeFormat') || '24';

    applyTheme(theme, false);
    applyFont(font);
    applyTimeFormat(timeFormat);
    initHaptics();
    initTooltips();
    initIdleHints();
    initScrollNav();
    initBackToTop();
    initAlertAutoDismiss();
});

function applyTheme(theme, animate = false) {
    if (animate) {
        document.body.classList.add('theme-transition');
    }
    document.body.classList.remove('light', 'dark', 'colorful');
    document.body.classList.add(theme);
    if (animate) {
        setTimeout(() => document.body.classList.remove('theme-transition'), 450);
    }
}

function applyFont(font) {
    document.body.classList.remove('font-small', 'font-medium', 'font-large');
    document.body.classList.add(font);
}

function applyTimeFormat(format) {
    window.timeFormat = format;
    const labels = [document.getElementById('timeFormatLabel'), document.getElementById('timeFormatLabelMobile')];
    labels.forEach((label) => {
        if (label) {
            label.textContent = format === '24' ? '24H' : '12H';
        }
    });
}

async function toggleTimeFormat() {
    const newFormat = window.timeFormat === '24' ? '12' : '24';
    const timeElements = document.querySelectorAll('.metadata-only, .time-display');

    timeElements.forEach((element) => element.classList.add('time-updating'));
    document.getElementById('timeFormatLabel')?.classList.add('time-updating');
    document.getElementById('timeFormatLabelMobile')?.classList.add('time-updating');

    localStorage.setItem('timeFormat', newFormat);
    window.timeFormat = newFormat;
    fetch(`/settings/time-format/${newFormat}`, { method: 'POST' });

    setTimeout(() => {
        applyTimeFormat(newFormat);

        timeElements.forEach((element) => {
            const text = element.textContent;
            const timePattern = /(\d{1,2}:\d{2})/g;
            if (timePattern.test(text)) {
                element.textContent = text.replace(timePattern, (match) => formatTime(match));
            }
            element.classList.remove('time-updating');
        });

        document.getElementById('timeFormatLabel')?.classList.remove('time-updating');
        document.getElementById('timeFormatLabelMobile')?.classList.remove('time-updating');
    }, 300);
}

function setTheme(theme) {
    localStorage.setItem('theme', theme);
    applyTheme(theme, true);
}

function setFontSize(font) {
    localStorage.setItem('fontSize', font);
    applyFont(font);
}

function formatTime(timeStr) {
    if (window.timeFormat === '12') {
        const [hours, minutes] = timeStr.split(':');
        const hour = parseInt(hours, 10);
        const ampm = hour >= 12 ? 'م' : 'ص';
        const displayHour = hour % 12 || 12;
        return `${displayHour}:${minutes} ${ampm}`;
    }
    return timeStr;
}

function triggerHapticFeedback(level = 'soft') {
    if (!navigator.vibrate) return;

    const patterns = {
        soft: 12,
        medium: 24,
        strong: [18, 20, 18],
    };
    navigator.vibrate(patterns[level] || patterns.soft);
}

function initHaptics() {
    document.addEventListener('click', function (event) {
        const target = event.target.closest('[data-haptic], .mobile-nav-item, .btn, .nav-link, .dropdown-item');
        if (!target) return;
        if (target.matches('input, select, textarea')) return;
        triggerHapticFeedback(target.dataset.haptic || 'soft');
    }, { passive: true });
}

function initTooltips() {
}

function initIdleHints() {
}

function initScrollNav() {
    let lastScrollY = window.scrollY;
    const nav = document.querySelector('.mobile-bottom-nav');
    if (!nav) return;

    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        if (currentScrollY > lastScrollY && currentScrollY > 80) {
            nav.classList.add('nav-hidden');
        } else {
            nav.classList.remove('nav-hidden');
        }
        lastScrollY = currentScrollY;
    });
}

function initBackToTop() {
    const btn = document.getElementById('backToTop');
    if (!btn) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    });

    btn.addEventListener('click', () => {
        triggerHapticFeedback('medium');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

/**
 * Automatically removes alert messages after 5 seconds to keep the UI clean globally.
 */
function initAlertAutoDismiss() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        // We use a timeout to give the user time to read the message
        setTimeout(function() {
            alert.style.transition = "opacity 0.6s ease, transform 0.6s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-10px)";
            
            // Completely remove from DOM after transition finishes
            setTimeout(() => alert.remove(), 600);
        }, 5000);
    });
}
