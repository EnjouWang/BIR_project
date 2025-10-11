import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def highlight(text, keyword):
    """
    在 text 當中找到 keyword，並用 <span class="highlight"> 包起來
    """
    if not keyword:
        return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    highlighted = pattern.sub(r'<span class="highlight">\g<0></span>', text)
    return mark_safe(highlighted)
