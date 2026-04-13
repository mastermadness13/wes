// teachers.js - Handles teachers list functionality

function initTeachersList() {
  const modal = document.getElementById('teacherDetailsModal');
  if (!modal) return;

  $('#teacherDetailsModal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget);
    var name = button.data('name');
    var department = button.data('department');
    var numSubjects = button.data('num-subjects');
    var semesters = button.data('semesters');

    var modal = $(this);
    modal.find('#teacherName').text(name);
    modal.find('#teacherDepartment').text(department);
    modal.find('#teacherNumSubjects').text(numSubjects);
    modal.find('#teacherSemesters').text(semesters);
  });
}

document.addEventListener('DOMContentLoaded', function() {
  initTeachersList();
});