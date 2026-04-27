function formatTime(timeStr) {
  if (window.timeFormat === '12') {
    const [hours, minutes] = timeStr.split(':');
    const hour = parseInt(hours, 10);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  }
  return timeStr;
}

function toggleCollapsible(id) {
  const element = document.getElementById(id);
  if (element) {
    element.classList.toggle('open');
  }
}

function initTimetableList() {
  document.querySelectorAll('.metadata-only').forEach((element) => {
    const text = element.textContent || '';
    const match = text.match(/(\d{2}:\d{2}) - (\d{2}:\d{2})/);
    if (match) {
      element.textContent = `${formatTime(match[1])} - ${formatTime(match[2])}`;
    }
  });

  document.addEventListener('click', (event) => {
    const toggleButton = event.target.closest('button[data-toggle]');
    if (toggleButton) {
      const id = toggleButton.getAttribute('data-toggle');
      if (id) {
        toggleCollapsible(id);
      }
    }
  });

  document.addEventListener('click', async (event) => {
    const button = event.target.closest('.delete-entry-btn');
    if (!button) return;
    if (!confirm('Delete this timetable entry?')) return;

    const response = await fetch(`${window.location.origin}/timetable/delete-entry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lecture_id: Number(button.dataset.id) }),
    });

    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      alert(payload.message || 'Unable to delete entry.');
      return;
    }

    window.location.reload();
  });

  const scheduleItems = Array.from(document.querySelectorAll('.schedule-item'));
  scheduleItems.forEach((item) => {
    const editUrl = item.dataset.editUrl;
    if (!editUrl) return;

    item.style.cursor = 'pointer';

    item.addEventListener('dblclick', () => {
      window.location.href = editUrl;
    });

    item.addEventListener('click', (event) => {
      if (event.target.closest('.schedule-actions')) return;
      scheduleItems.forEach((el) => el.classList.remove('active'));
      item.classList.add('active');
    });
  });

  document.addEventListener('click', (event) => {
    if (!event.target.closest('.schedule-item')) {
      scheduleItems.forEach((el) => el.classList.remove('active'));
    }
  });

  document.addEventListener('click', (event) => {
    const emptyCell = event.target.closest('.empty-cell');
    if (!emptyCell) return;

    const cell = emptyCell.closest('td');
    if (!cell) return;
    const row = cell.closest('tr');
    const table = cell.closest('table');
    const semesterSection = table.closest('.timetable-subsection');
    const dayCell = row ? row.querySelector('td:first-child') : null;
    const day = dayCell ? dayCell.textContent.trim() : '';
    const semester = semesterSection ? semesterSection.dataset.semester : '';
    const periodIndex = Array.from(cell.parentNode.children).indexOf(cell);
    const headerCells = table ? Array.from(table.querySelectorAll('thead th')) : [];
    const periodHeader = headerCells[periodIndex];
    const periodCode = periodHeader ? (periodHeader.dataset.periodCode || '') : '';

    if (!day || !semester || !periodCode) return;

    const url = new URL(`${window.location.origin}/timetable/create`);
    url.searchParams.set('day', day);
    url.searchParams.set('semester', semester);
    url.searchParams.set('section', periodCode);
    url.searchParams.set('next', `${window.location.pathname}${window.location.search}`);
    window.location.href = url.toString();
  });
}

function renderRoomOptions(select, rooms, selectedValue) {
  select.innerHTML = '';
  if (!rooms.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'لا توجد قاعات مسجلة.';
    select.appendChild(option);
    return false;
  }

  rooms.forEach((room) => {
    const option = document.createElement('option');
    option.value = String(room.id);
    option.textContent = `${room.name_ar || room.name}${room.is_available ? '' : ' - محجوزة'}`;
    option.disabled = !room.is_available && String(room.id) !== String(selectedValue || '');
    select.appendChild(option);
  });

  if (selectedValue && select.querySelector(`option[value="${selectedValue}"]`)) {
    select.value = selectedValue;
  }

  return Boolean(select.value);
}

function renderTeacherOptions(select, teachers, selectedValue) {
  select.innerHTML = '';
  if (!teachers.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'لا يوجد مدرسون متاحون.';
    select.appendChild(option);
    return false;
  }

  teachers.forEach((teacher) => {
    const option = document.createElement('option');
    option.value = String(teacher.id);
    option.textContent = teacher.name;
    select.appendChild(option);
  });

  if (selectedValue && select.querySelector(`option[value="${selectedValue}"]`)) {
    select.value = selectedValue;
  }

  return Boolean(select.value);
}

function initTimetableForm(allCourses = [], allTeachers = [], entryId = null, originalRoomId = null, originalTeacherId = null, originalCourseId = null) {
  const day = document.getElementById('day');
  const semester = document.getElementById('semester');
  const period = document.getElementById('period');
  const courseSelect = document.getElementById('course_id');
  const roomSelect = document.getElementById('room_id');
  const teacherSelect = document.getElementById('teacher_id');
  const submitBtn = document.getElementById('submitBtn');

  if (!day || !semester || !period || !courseSelect || !roomSelect || !teacherSelect || !submitBtn) return;

  function refreshCourseOptions() {
    courseSelect.innerHTML = '';
    if (!allCourses.length) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'No courses available.';
      courseSelect.appendChild(option);
      return false;
    }

    allCourses.forEach((course) => {
      const option = document.createElement('option');
      option.value = course.id;
      option.textContent = `${course.name} — ${course.code}`;
      courseSelect.appendChild(option);
    });

    if (originalCourseId && courseSelect.querySelector(`option[value="${originalCourseId}"]`)) {
      courseSelect.value = originalCourseId;
    }

    return Boolean(courseSelect.value);
  }

  async function refreshRoomOptions() {
    const params = new URLSearchParams({
      day: day.value,
      semester: semester.value,
      section: period.value,
    });
    if (entryId) {
      params.set('exclude_id', entryId);
    }

    const response = await fetch(`${window.location.origin}/timetable/available-rooms?${params.toString()}`);
    const payload = await response.json();
    return renderRoomOptions(roomSelect, payload.rooms || [], originalRoomId);
  }

  async function refreshTeacherOptions() {
    const params = new URLSearchParams({
      day: day.value,
      semester: semester.value,
      section: period.value,
    });
    if (entryId) {
      params.set('exclude_id', entryId);
    }

    const response = await fetch(`${window.location.origin}/timetable/available-teachers?${params.toString()}`);
    const payload = await response.json();
    return renderTeacherOptions(teacherSelect, payload.teachers || [], originalTeacherId);
  }

  async function refreshAvailability() {
    submitBtn.disabled = true;
    const courseOk = refreshCourseOptions();
    const roomOk = await refreshRoomOptions();
    const teacherOk = await refreshTeacherOptions();
    submitBtn.disabled = !(courseOk && roomOk && teacherOk);
  }

  [day, semester, period].forEach((element) => {
    if (element) {
      element.addEventListener('change', refreshAvailability);
    }
  });

  refreshAvailability();
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.timetable-card')) {
    initTimetableList();
  }

  const allCourses = window.allCourses || [];
  const allTeachers = window.allTeachers || [];
  const entryId = window.entryId || null;
  const originalRoomId = window.originalRoomId || null;
  const originalTeacherId = window.originalTeacherId || null;
  const originalCourseId = window.originalCourseId || null;

  if (document.getElementById('day') && document.getElementById('semester')) {
    initTimetableForm(allCourses, allTeachers, entryId, originalRoomId, originalTeacherId, originalCourseId);
  }
});
