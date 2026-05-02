function initTeachersList() {
  const modal = document.getElementById('teacherDetailsModal');
  document.addEventListener('change', function (event) {
    if (!event.target.classList.contains('qualification-select')) return;
    updateRanks(event.target.closest('.modal'));
  });

  if (window.jQuery) {
    window.jQuery(document).on('shown.bs.modal', '.modal', function () {
      updateRanks(this);
    });
  }

  if (!modal || !window.jQuery) return;

  window.jQuery('#teacherDetailsModal').on('show.bs.modal', function (event) {
    var button = window.jQuery(event.relatedTarget);
    var name = button.data('name');
    var department = button.data('department');
    var numSubjects = button.data('num-subjects');
    var semesters = button.data('semesters');

    var detailsModal = window.jQuery(this);
    detailsModal.find('#teacherName').text(name);
    detailsModal.find('#teacherDepartment').text(department);
    detailsModal.find('#teacherNumSubjects').text(numSubjects);
    detailsModal.find('#teacherSemesters').text(semesters);
  });
}

function updateRanks(modal) {
  if (!modal) return;
  const qualificationSelect = modal.querySelector('.qualification-select');
  const rankSelect = modal.querySelector('.rank-select');
  if (!qualificationSelect || !rankSelect) return;

  const qualification = qualificationSelect.value;
  const current = rankSelect.value;
  const allowed = {
    'دبلوم': ['محاضر مساعد', 'أستاذ متعاون', 'معيد'],
    'بكالوريوس': ['محاضر مساعد', 'محاضر', 'أستاذ متعاون'],
    'ماجستير': ['محاضر', 'أستاذ مساعد', 'أستاذ متعاون'],
  }[qualification] || [
    'أستاذ',
    'أستاذ مشارك',
    'أستاذ مساعد',
    'محاضر',
    'محاضر مساعد',
    'أستاذ متعاون',
  ];

  Array.from(rankSelect.options).forEach((option) => {
    if (!option.value) return;
    option.style.display = allowed.includes(option.value) ? '' : 'none';
  });

  if (!allowed.includes(current) && current !== '') {
    rankSelect.value = '';
  }
}

document.addEventListener('DOMContentLoaded', function() {
  initTeachersList();
});
