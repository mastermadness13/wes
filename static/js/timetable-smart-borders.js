// Smart Timetable Cell Border Logic
// This script should be included on the timetable list page after the table is rendered.
// It adds .shift-left or .shift-right classes to cells based on your visual rules.

document.addEventListener('DOMContentLoaded', function () {
  // Find all timetable rows
  document.querySelectorAll('.timetable-print-table tbody tr').forEach(function (row) {
    const cells = Array.from(row.querySelectorAll('td[data-day][data-semester][data-period]'));
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      const prev = cells[i - 1];
      const next = cells[i + 1];
      const hasEntry = cell.querySelector('.schedule-item');
      // Check left neighbor
      if (!hasEntry && prev && prev.querySelector('.schedule-item')) {
        cell.classList.add('shift-left');
      }
      // Check right neighbor
      if (!hasEntry && next && next.querySelector('.schedule-item')) {
        cell.classList.add('shift-right');
      }
    }
  });
});
