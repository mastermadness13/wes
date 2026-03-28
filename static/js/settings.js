document.addEventListener('DOMContentLoaded', function() {
    const theme = localStorage.getItem('theme') || 'light';
    const font = localStorage.getItem('fontSize') || 'font-medium';
    applyTheme(theme);
    applyFont(font);
});

function applyTheme(theme) {
    document.body.classList.remove('light', 'dark');
    document.body.classList.add(theme);
}

function applyFont(font) {
    document.body.classList.remove('font-small', 'font-medium', 'font-large');
    document.body.classList.add(font);
}

function setTheme(theme) {
    localStorage.setItem('theme', theme);
    applyTheme(theme);
}

function setFontSize(font) {
    localStorage.setItem('fontSize', font);
    applyFont(font);
}
