document.addEventListener('DOMContentLoaded', function() {
    const theme = localStorage.getItem('theme') || 'dark';
    const font = localStorage.getItem('fontSize') || 'font-medium';
    const timeFormat = localStorage.getItem('timeFormat') || '24';
    applyTheme(theme);
    applyFont(font);
    applyTimeFormat(timeFormat);
    initTooltips();
    initIdleHints();
    initEmptyCellClicks();
});

function applyTheme(theme) {
    document.body.classList.remove('light', 'dark', 'colorful');
    document.body.classList.add(theme);
}

function applyFont(font) {
    document.body.classList.remove('font-small', 'font-medium', 'font-large');
    document.body.classList.add(font);
}

function applyTimeFormat(format) {
    // Store for later use in displaying times
    window.timeFormat = format;
}

function setTheme(theme) {
    localStorage.setItem('theme', theme);
    applyTheme(theme);
}

function setFontSize(font) {
    localStorage.setItem('fontSize', font);
    applyFont(font);
}

function formatTime(timeStr) {
    if (window.timeFormat === '12') {
        const [hours, minutes] = timeStr.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour % 12 || 12;
        return `${displayHour}:${minutes} ${ampm}`;
    }
    return timeStr;
}

function initTooltips() {
    // Tooltips are handled by CSS hover
}

function initEmptyCellClicks() {
    document.addEventListener('click', function(event) {
        const cell = event.target.closest('.empty-cell');
        if (cell) {
            const td = cell.closest('td');
            const tr = td.closest('tr');
            const day = tr.querySelector('.day-label').textContent.trim();
            const thIndex = Array.from(tr.children).indexOf(td);
            const period = document.querySelectorAll('.timetable-print-table thead th')[thIndex].textContent.trim().split(' ')[0];
            // Open modal with day and period
            openAddModal(day, period);
        }
    });
}

function openAddModal(day, period) {
    // Assuming there's a modal for adding timetable entry
    // Populate the form with day and period
    const modal = document.getElementById('addTimetableModal');
    if (modal) {
        document.getElementById('day').value = day;
        document.getElementById('section').value = period;
        $(modal).modal('show');
    } else {
        // If no modal, redirect to create page with params
        window.location.href = `/timetable/create?day=${encodeURIComponent(day)}&section=${encodeURIComponent(period)}`;
    }
}
