function initCoursesList() {
  const searchInput = document.getElementById('courseSearch');
  const rows = Array.from(document.querySelectorAll('#coursesTable tbody tr.course-row'));
  const modalEl = document.getElementById('courseModal');
  const editForm = document.getElementById('courseEditForm');
  const deleteBtn = document.getElementById('courseDeleteBtn');

  if (!searchInput || !rows.length || !modalEl || !editForm || !deleteBtn) return;

  const modal = window.jQuery ? window.jQuery(modalEl) : null;
  const clearActiveRows = () => rows.forEach((row) => row.classList.remove('active-row'));

  function fillModal(row) {
    const courseId = row.dataset.courseId;
    const name = row.dataset.courseName || '';
    const code = row.dataset.courseCode || '';
    const department = row.dataset.courseDepartment || '';
    const year = row.dataset.courseYear || '1';
    const notes = row.dataset.courseNotes || '';

    document.getElementById('modalCourseName').value = name;
    document.getElementById('modalCourseCode').value = code;
    document.getElementById('modalCourseDepartment').value = department;
    document.getElementById('modalCourseYear').value = year;
    document.getElementById('modalCourseNotes').value = notes;
    document.getElementById('courseModalMeta').textContent = `ID: ${courseId}`;
    editForm.action = `${window.location.origin}/courses/${courseId}/edit`;
    deleteBtn.dataset.courseId = courseId;
  }

  function openModal(row) {
    clearActiveRows();
    row.classList.add('active-row');
    fillModal(row);
    if (modal) {
      modal.modal('show');
    }
  }

  searchInput.addEventListener('input', function () {
    const query = this.value.trim().toLowerCase();
    rows.forEach(function (row) {
      row.style.display = row.innerText.toLowerCase().includes(query) ? '' : 'none';
    });
  });

  rows.forEach(function (row) {
    row.addEventListener('click', function () {
      openModal(row);
    });
    row.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openModal(row);
      }
    });
  });

  deleteBtn.addEventListener('click', function () {
    const courseId = deleteBtn.dataset.courseId;
    if (!courseId) return;
    if (!confirm('هل تريد حذف هذه المادة؟')) return;

    editForm.action = `${window.location.origin}/courses/${courseId}/delete`;
    editForm.submit();
  });
}

function initCourseCodeGeneration(courseId = null) {
  const departmentInput = document.getElementById('department');
  const yearInput = document.getElementById('year');
  const codeInput = document.getElementById('code');
  const generateButton = document.getElementById('generateCodeBtn');

  if (!departmentInput || !yearInput || !codeInput || !generateButton) return;

  generateButton.addEventListener('click', async function () {
    if (!departmentInput.value || !yearInput.value) {
      alert('يرجى اختيار القسم والسنة أولاً.');
      return;
    }

    const url = new URL(window.location.origin + '/courses/generate-code');
    url.searchParams.set('department', departmentInput.value);
    url.searchParams.set('year', yearInput.value);
    if (courseId) {
      url.searchParams.set('course_id', courseId);
    }

    const response = await fetch(url.toString(), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    const payload = await response.json();
    if (response.ok && payload.code) {
      codeInput.value = payload.code;
    } else {
      alert('تعذر إنشاء رمز تلقائي حالياً.');
    }
  });
}

document.addEventListener('DOMContentLoaded', function () {
  if (document.getElementById('coursesTable')) {
    initCoursesList();
  }
  if (document.getElementById('generateCodeBtn')) {
    const courseId = window.courseId || null;
    initCourseCodeGeneration(courseId);
  }
});

