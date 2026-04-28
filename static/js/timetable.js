﻿﻿﻿/**
 * Displays a prominent notification modal.
 * If called within an iframe, it attempts to display the modal in the parent window.
 */
function showNotificationModal(message, title = 'تنبيه', type = 'danger') {
    if (window.parent && typeof window.parent.showNotificationModal === 'function' && window.parent !== window) {
        window.parent.showNotificationModal(message, title, type);
        return;
    }

    const existing = document.getElementById('timetableNotificationModal');
    if (existing) existing.remove();

    const icon = type === 'success' ? '✅' : '⚠️';
    const html = `
        <div id="timetableNotificationModal" class="timetable-modal" style="z-index: 10005;">
            <div class="timetable-modal-dialog" style="width: min(480px, 95%); margin-top: 15vh;">
                <div class="timetable-modal-header ${type === 'success' ? 'notify-header-success' : 'notify-header-danger'} text-white">
                    <h3 class="mb-0" style="font-size: 1.25rem; color: white;">${icon} ${title}</h3>
                    <button type="button" class="timetable-modal-close text-white" id="closeNotifyModal" style="background:transparent; border:0; color:white;">&times;</button>
                </div>
                <div class="timetable-modal-body p-4 text-center">
                    <p class="mb-4" style="line-height: 1.6; color: var(--text); font-size: 1.1rem;">${message}</p>
                    <button type="button" class="btn btn-${type === 'success' ? 'success' : 'primary'} w-100" id="confirmNotifyModal">موافق</button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
    document.body.classList.add('modal-open');

    const modal = document.getElementById('timetableNotificationModal');
    const close = () => {
        modal.remove();
        if (!document.querySelector('.timetable-modal')) document.body.classList.remove('modal-open');
    };

    document.getElementById('closeNotifyModal').onclick = close;
    document.getElementById('confirmNotifyModal').onclick = close;
}

// Delegated print button handler — works even if the button is rendered later
document.addEventListener('click', function(e) {
    const btn = e.target.closest('[data-print-table]');
    if (!btn) return;
    e.preventDefault();
    printTimetable();
});

function printTimetable() {
    const container = document.querySelector('.timetable-card') || document.querySelector('.timetable-print-table') || document.querySelector('.timetable-layout');
    if (!container) {
        showNotificationModal('لا يوجد جدول للطباعة', 'طباعة', 'warning');
        return;
    }

    // Collect stylesheets and inline styles to preserve look
    const styles = [];
    document.querySelectorAll('link[rel="stylesheet"]').forEach(l => styles.push(l.outerHTML));
    document.querySelectorAll('style').forEach(s => styles.push(s.outerHTML));

    const w = window.open('', '_blank');
    if (!w) {
        showNotificationModal('تعذر فتح نافذة الطباعة. تحقق من إعدادات المتصفح.', 'خطأ', 'danger');
        return;
    }

    const html = `<!doctype html><html lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${styles.join('\n')}<title>طباعة الجدول</title></head><body>${container.outerHTML}</body></html>`;
    w.document.open();
    w.document.write(html);
    w.document.close();

    // Wait a short time for styles to load, then print
    const tryPrint = () => {
        try {
            w.focus();
            w.print();
            // close after print (some browsers block close if not user-initiated)
            try { w.close(); } catch (e) {}
        } catch (err) {
            // In case printing fails immediately, retry after small delay
            setTimeout(() => { tryPrint(); }, 250);
        }
    };

    setTimeout(tryPrint, 300);
}
window.showNotificationModal = showNotificationModal;

document.addEventListener('DOMContentLoaded', function() {
    // 1. MODAL TRIGGER LOGIC
    // Intercepts clicks on Add/Edit triggers and opens them in an iframe modal
    const listLayout = document.querySelector('.timetable-layout');
    if (listLayout) {
        document.addEventListener('click', function(e) {
            const trigger = e.target.closest('[data-create-url], [data-edit-url]');
            // Do not trigger modal if the delete button was clicked
            if (!trigger || e.target.closest('.delete-entry-btn')) return;

            e.preventDefault();
            const url = trigger.dataset.createUrl || trigger.dataset.editUrl;
            openTimetableModal(url);
        });

        // Handle deletion via API instead of standard link
        document.querySelectorAll('.delete-entry-btn').forEach(btn => {
            btn.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (!confirm('هل أنت متأكد من حذف هذه الحصة؟')) return;

                const id = this.dataset.id;
                try {
                    const res = await fetch('/timetable/api/delete-entry', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ lecture_id: id })
                    });
                    const data = await res.json();
                    if (data.ok) window.location.reload();
                    else showNotificationModal(data.message, 'فشل الحذف');
                } catch (err) { showNotificationModal('خطأ في الاتصال بالسيرفر'); }
            });
        });

        // Handle signals from the iframe (success or manual close)
        window.addEventListener('message', function(event) {
            if (event.data.type === 'timetable-modal-saved') {
                const modal = document.getElementById('timetableAppModal');
                if (modal) modal.remove();
                document.body.classList.remove('modal-open');
                window.location.reload();
            }
            if (event.data.type === 'close-timetable-modal') {
                const modal = document.getElementById('timetableAppModal');
                if (modal) modal.remove();
                document.body.classList.remove('modal-open');
            }
        });
    }

    // 1.1 FLASH TO MODAL CONVERTER
    // Automatically catches Flask flash errors and shows them in the prominent modal
    const errorAlerts = document.querySelectorAll('.alert-danger, .alert-warning');
    if (errorAlerts.length > 0) {
        const combinedMessage = Array.from(errorAlerts).map(a => a.innerHTML).join('<br>');
        errorAlerts.forEach(a => a.style.display = 'none'); // Hide the small alerts
        showNotificationModal(combinedMessage, 'تنبيه بوجود تعارض');
    }

    // 2. FORM INTERACTIVE LOGIC
    // Runs inside Create/Edit forms to update available rooms/teachers dynamically
    const timetableForm = document.getElementById('timetable-form') || document.getElementById('edit-timetable-form') || document.getElementById('create-timetable-form');
    if (timetableForm) {
        const daySelect = document.getElementById('day');
        const semSelect = document.getElementById('semester');
        const periodSelect = document.getElementById('period');
        
        const updateResources = async () => {
            const day = daySelect.value;
            const sem = semSelect.value;
            const period = periodSelect.value;
            const excludeId = window.APP_DATA.entryId || '';

            try {
                const [roomRes, teachRes] = await Promise.all([
                    fetch(`/timetable/api/available-rooms?day=${day}&semester=${sem}&period_code=${period}&exclude_id=${excludeId}`),
                    fetch(`/timetable/api/available-teachers?day=${day}&semester=${sem}&period_code=${period}&exclude_id=${excludeId}`)
                ]);

                const roomData = await roomRes.json();
                const teachData = await teachRes.json();

                const roomSelect = document.getElementById('room_id');
                roomSelect.innerHTML = roomData.rooms.map(r => ` 
                    <option value="${r.id}" ${!r.is_available && r.id != window.APP_DATA.originalRoomId ? 'disabled' : ''} ${r.id == roomSelect.value ? 'selected' : ''}>
                        ${r.name_ar || r.name} — ${r.conflict_msg ? r.conflict_msg : 'متاحة'}
                    </option>
                `).join('');

                const teachSelect = document.getElementById('teacher_id');
                teachSelect.innerHTML = teachData.teachers.map(t => `
                    <option value="${t.id}" ${!t.is_available && t.id != window.APP_DATA.originalTeacherId ? 'disabled' : ''} ${t.id == teachSelect.value ? 'selected' : ''}>
                        ${t.name} — ${t.conflict_msg ? t.conflict_msg : 'متاح'}
                    </option>
                `).join('');
            } catch (err) { console.error("Resource fetch error:", err); }
        };

        [daySelect, semSelect, periodSelect].forEach(el => el.addEventListener('change', updateResources));
        
        periodSelect.addEventListener('change', function() {
            const opt = this.options[this.selectedIndex];
            if (opt.dataset.start) document.getElementById('start_time').value = opt.dataset.start;
            if (opt.dataset.end) document.getElementById('end_time').value = opt.dataset.end;
        });

        // Track unsaved changes
        window.isFormDirty = false;
        const markDirty = () => { window.isFormDirty = true; };
        timetableForm.addEventListener('input', markDirty);
        timetableForm.addEventListener('change', markDirty);

        // Handle the close button inside the iframe
        const closeBtn = document.getElementById('closeModalBtn');
        if (closeBtn) {
            closeBtn.onclick = () => {
                if (window.isFormDirty && !confirm('لديك تغييرات غير محفوظة. هل أنت متأكد من الإغلاق؟')) return;
                window.parent.postMessage({ type: 'close-timetable-modal' }, '*');
            };
        }
    }

    // 3. AUTO-SUBMIT HANDLER
    document.addEventListener('change', function(e) {
        const target = e.target.closest('[data-autosubmit]');
        if (target) {
            const form = target.closest('form');
            if (form) form.submit();
        }
    });
});

function openTimetableModal(url) {
    const existing = document.getElementById('timetableAppModal');
    if (existing) existing.remove();

    const html = `
        <div id="timetableAppModal" class="timetable-modal">
            <div class="timetable-modal-dialog">
                <div class="timetable-modal-header">
                    <h3 class="mb-0">تفاصيل الحصة</h3>
                    <button type="button" class="timetable-modal-close" id="closeTimetableModal">&times;</button>
                </div>
                <div class="timetable-modal-body">
                    <div id="modalSpinner" class="modal-spinner-container">
                        <div class="spinner-border text-primary" role="status"></div>
                        <div class="mt-3">جاري التحميل...</div>
                    </div>
                    <iframe src="${url}" class="timetable-modal-frame"></iframe>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
    document.body.classList.add('modal-open');

    const modal = document.getElementById('timetableAppModal');
    const iframe = modal.querySelector('.timetable-modal-frame');
    const spinner = modal.querySelector('#modalSpinner');

    let isLoaded = false;
    const loadTimeout = setTimeout(() => {
        if (!isLoaded && document.getElementById('modalSpinner')) {
            spinner.innerHTML = `
                <div class="text-center p-3">
                    <div class="text-danger mb-2" style="font-size: 1.5rem;">⚠️</div>
                    <p class="small mb-2">فشل تحميل النموذج أو استغرق وقتاً طويلاً.</p>
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="window.location.reload()">تحديث الصفحة</button>
                </div>
            `;
        }
    }, 10000);

    const showSpecificError = (message, isCritical = false) => {
        let buttonsHtml = `<button type="button" class="btn btn-sm btn-outline-primary" onclick="window.location.reload()">تحديث الصفحة</button>`;
        
        if (isCritical) {
            buttonsHtml += ` <button type="button" id="reportErrorBtn" class="btn btn-sm btn-danger">تبليغ عن خطأ</button>`;
        }

        spinner.innerHTML = `
            <div class="text-center p-3">
                <div class="text-danger mb-2" style="font-size: 1.5rem;">⚠️</div>
                <p class="small mb-2">${message}</p>
                <div class="d-flex justify-content-center gap-2">
                    ${buttonsHtml}
                </div>
            </div>
        `;

        if (isCritical) {
            const btn = document.getElementById('reportErrorBtn');
            btn.onclick = async function() {
                btn.disabled = true;
                btn.textContent = 'جاري الإرسال...';
                try {
                    const res = await fetch('/timetable/api/report-error', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            message: message,
                            url: window.location.href, // Captures current URL inside iframe
                            timestamp: new Date().toISOString()
                        })
                    });
                    if (res.ok) {
                        btn.className = 'btn btn-sm btn-success';
                        btn.textContent = 'تم التبليغ ✅';
                    } else { throw new Error(); }
                } catch (e) {
                    btn.disabled = false;
                    btn.textContent = 'فشل الإرسال - حاول ثانية';
                }
            };
        }
        spinner.style.display = 'flex';
        iframe.style.opacity = '0';
    };

    iframe.addEventListener('load', function () {
        try {
            isLoaded = true;
            clearTimeout(loadTimeout);

            const doc = iframe.contentDocument || iframe.contentWindow.document;
            const title = doc.title || "";
            const bodyText = doc.body ? doc.body.innerText : "";

            if (title.includes("ERROR_CODE:404") || title.includes("404") || bodyText.includes("Not Found")) {
                showSpecificError("خطأ 404: الصفحة غير موجودة. قد يكون تم حذف السجل.");
            } else if (title.includes("ERROR_CODE:500") || title.includes("500") || bodyText.includes("Internal Server Error")) {
                showSpecificError("خطأ 500: حدث خطأ في النظام الداخلي. يرجى المحاولة لاحقاً.", true);
            } else if (title.includes("ERROR_CODE:403") || title.includes("403") || bodyText.includes("Forbidden")) {
                showSpecificError("خطأ 403: ليس لديك الصلاحية للوصول لهذه الصفحة.");
            } else {
                spinner.style.display = 'none';
                iframe.style.opacity = '1';
            }
        } catch (e) {
            // Fallback for unexpected security or loading issues
            spinner.style.display = 'none';
            iframe.style.opacity = '1';
        }
    });

    document.getElementById('closeTimetableModal').onclick = () => {
        try {
            const iframeWin = iframe.contentWindow;
            if (iframeWin && iframeWin.isFormDirty) {
                if (!confirm('لديك تغييرات غير محفوظة. هل أنت متأكد من الإغلاق؟')) return;
            }
        } catch (e) { /* ignore potential cross-origin or access issues */ }

        clearTimeout(loadTimeout);
        modal.remove();
        document.body.classList.remove('modal-open');
    };
}