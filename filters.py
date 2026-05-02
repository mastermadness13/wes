import re
from datetime import datetime
from flask import session
from markupsafe import Markup

def highlight_filter(text, search_term):
    if not search_term or not text:
        return text
    # استخدام regex للبحث عن المطابقات مع تجاهل حالة الأحرف وتغليفها بوسم <mark>
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f'<mark class="search-highlight">{m.group()}</mark>', str(text))
    return Markup(highlighted)

def arabic_date_filter(value):
    if not value:
        return ""
    
    # معالجة المدخلات النصية (شائع مع طوابع SQLite الزمنية)
    if isinstance(value, str):
        try:
            # تنسيق SQLite القياسي: 'YYYY-MM-DD HH:MM:SS'
            dt = datetime.strptime(value.split('.')[0], '%Y-%m-%d %H:%M:%S')
        except (ValueError, IndexError):
            try:
                dt = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
    else:
        dt = value

    days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    months_ar = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", 
                 "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    
    day_name = days_ar[dt.weekday()]
    
    return f"{day_name}، {dt.day} {months_ar[dt.month - 1]} {dt.year}"

def format_time_filter(value, format_type=None):
    if not value:
        return ""
    if not format_type:
        format_type = session.get('timeFormat', '24')
        
    if isinstance(value, str):
        try:
            dt = datetime.strptime(value, '%H:%M')
        except ValueError:
            return value
    else:
        dt = value

    if str(format_type) == '12':
        return dt.strftime('%I:%M %p').replace('AM', 'ص').replace('PM', 'م').lstrip('0')
    return dt.strftime('%H:%M')

def register_filters(app):
    app.template_filter('highlight')(highlight_filter)
    app.template_filter('arabic_date')(arabic_date_filter)
    app.template_filter('format_time')(format_time_filter)