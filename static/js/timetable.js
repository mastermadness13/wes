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

            const params = new URLSearchParams(window.location.search);
            const deptId = document.querySelector('input[name="department_id"]')?.value || params.get('department_id') || '';
            const startTime = document.getElementById('start_time')?.value || '';
            const endTime = document.getElementById('end_time')?.value || '';

            try {
                const roomParams = new URLSearchParams({ day, semester: sem, period_code: period, exclude_id: excludeId, department_id: deptId, start_time: startTime, end_time: endTime });
                const teachParams = new URLSearchParams({ day, semester: sem, period_code: period, exclude_id: excludeId, department_id: deptId, start_time: startTime, end_time: endTime });

                const [roomRes, teachRes] = await Promise.all([
                    fetch(`/timetable/api/available-rooms?${roomParams.toString()}`),
                    fetch(`/timetable/api/available-teachers?${teachParams.toString()}`)
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

        // Confirm when user attempts to submit with force_save checked
        timetableForm.addEventListener('submit', function(e) {
            try {
                const force = document.getElementById('force_save');
                if (force && force.checked) {
                    const ok = confirm('أنت على وشك تجاهل التعارضات وحفظ الحصة. هل تريد المتابعة؟');
                    if (!ok) {
                        e.preventDefault();
                        return false;
                    }
                }
            } catch (err) {
                // ignore
            }
        });

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

// ----------------------------
// Searchable dropdown component
// ----------------------------
function normalizeText(s) {
    try { return String(s).toLowerCase().normalize('NFC'); } catch (e) { return String(s).toLowerCase(); }
}

function initSearchableField(key, items, opts = {}) {
    const input = document.getElementById(key + '_input');
    const hidden = document.getElementById(key + '_id');
    const list = document.getElementById(key + '_list');
    const errorEl = document.getElementById(key + '_error');
    if (!input || !hidden || !list) return;

    let visibleItems = items || [];
    const renderList = (itemsToRender, highlightIndex = -1) => {
        if (!itemsToRender || itemsToRender.length === 0) { list.style.display = 'none'; list.innerHTML = ''; return; }
        list.style.display = 'block';
        list.innerHTML = itemsToRender.map((it, idx) => {
            const label = (it.name_ar || it.name || it.label || it.title || it.display || '').toString();
            const extra = it.code ? ` <small style="opacity:.7">(${it.code})</small>` : '';
            const disabled = it.is_available === false && String(hidden.value) !== String(it.id) ? 'data-disabled="1" aria-disabled="true"' : '';
            return `<div role="option" class="searchable-item" data-idx="${idx}" data-id="${it.id}" ${disabled} style="padding:.35rem .6rem;cursor:pointer;border-bottom:1px solid #eee;">${label}${extra}</div>`;
        }).join('');
        // highlight
        const el = list.querySelector(`[data-idx="${highlightIndex}"]`);
        if (el) el.classList.add('searchable-item-active');
    };

    const closeList = () => { list.style.display = 'none'; };

    const findMatchById = (id) => visibleItems.find(i => String(i.id) === String(id));
    const findExactByLabel = (val) => {
        const n = normalizeText(val).trim();
        return visibleItems.find(i => normalizeText((i.name_ar || i.name || '')).trim() === n || normalizeText(i.code || '').trim() === n);
    };

    input.addEventListener('input', function(e) {
        const q = normalizeText(e.target.value || '');
        if (!q) { renderList(visibleItems.slice(0, 50)); return; }
        const matches = visibleItems.filter(it => {
            const hay = normalizeText((it.name_ar || it.name || '') + ' ' + (it.code || ''));
            return hay.indexOf(q) !== -1;
        }).slice(0, 50);
        renderList(matches);
        if (errorEl) errorEl.style.display = 'none';
        hidden.value = '';
    });

    input.addEventListener('focus', function() { renderList(visibleItems.slice(0,50)); });

    input.addEventListener('keydown', function(e) {
        const visible = Array.from(list.querySelectorAll('.searchable-item:not([data-disabled])'));
        const active = list.querySelector('.searchable-item-active');
        let idx = visible.indexOf(active);
        if (e.key === 'ArrowDown') { e.preventDefault(); idx = Math.min(visible.length-1, Math.max(0, idx+1)); if (visible[idx]) { if (active) active.classList.remove('searchable-item-active'); visible[idx].classList.add('searchable-item-active'); visible[idx].scrollIntoView({block:'nearest'}); } }
        else if (e.key === 'ArrowUp') { e.preventDefault(); idx = Math.min(visible.length-1, Math.max(0, idx-1)); if (visible[idx]) { if (active) active.classList.remove('searchable-item-active'); visible[idx].classList.add('searchable-item-active'); visible[idx].scrollIntoView({block:'nearest'}); } }
        else if (e.key === 'Enter') { e.preventDefault(); const pick = active || visible[0]; if (pick) pick.click(); }
        else if (e.key === 'Escape') { closeList(); }
    });

    list.addEventListener('click', function(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const it = ev.target.closest('.searchable-item');
        if (!it) return;
        if (it.getAttribute('data-disabled')) {
            showError('القيمة غير موجودة');
            return;
        }
        const id = it.getAttribute('data-id');
        const idx = Number(it.getAttribute('data-idx')) || 0;
        const item = (visibleItems[idx]) || findMatchById(id);
        if (item) {
            input.value = (item.name_ar || item.name || item.label || item.title || '');
            hidden.value = item.id;
            if (errorEl) errorEl.style.display = 'none';
        }
        // Immediately hide and clear list to avoid lingering UI
        try { list.style.display = 'none'; list.innerHTML = ''; } catch (e) {}
        input.focus();
    });

    const showError = (msg) => { if (errorEl) { errorEl.textContent = msg; errorEl.style.display = 'block'; } };

    input.addEventListener('blur', function() {
        // Delay closing so click handler can fire
        setTimeout(() => {
            const hid = hidden.value;
            if (hid) {
                const found = findMatchById(hid);
                if (found) { input.value = (found.name_ar || found.name || ''); if (errorEl) errorEl.style.display='none'; return; }
            }
            // Try exact label match
            const exact = findExactByLabel(input.value || '');
            if (exact) { hidden.value = exact.id; if (errorEl) errorEl.style.display='none'; }
            else {
                if (input.value && input.value.trim() !== '') showError('القيمة غير موجودة');
                hidden.value = '';
            }
            closeList();
        }, 150);
    });

    // When form submits, ensure hidden id is valid
    const form = input.closest('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const hid = hidden.value;
            if (!hid) {
                showError('القيمة غير موجودة');
                e.preventDefault();
                input.focus();
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    try {
        if (window.APP_DATA && Array.isArray(window.APP_DATA.courses)) initSearchableField('course', window.APP_DATA.courses);
        if (window.APP_DATA && Array.isArray(window.APP_DATA.teachers)) initSearchableField('teacher', window.APP_DATA.teachers);
        if (window.APP_DATA && Array.isArray(window.APP_DATA.rooms)) initSearchableField('room', window.APP_DATA.rooms);

        // Pre-fill inputs from hidden values if present
        [['course','courses'], ['teacher','teachers'], ['room','rooms']].forEach(([key, arrName]) => {
            const hid = document.getElementById(key + '_id');
            const inp = document.getElementById(key + '_input');
            if (!hid || !inp) return;
            const val = hid.value;
            if (val && window.APP_DATA && Array.isArray(window.APP_DATA[arrName])) {
                const found = window.APP_DATA[arrName].find(i => String(i.id) === String(val));
                if (found) inp.value = (found.name_ar || found.name || found.label || found.title || '');
            }
        });
    } catch (e) { console.error('Searchable init error', e); }
});

// Close searchable lists when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest || !document.querySelectorAll) return;
    if (!e.target.closest('.searchable-wrapper')) {
        document.querySelectorAll('.searchable-list').forEach(l => { try { l.style.display = 'none'; } catch (e) {} });
    }
});