import re
from nltk.stem import PorterStemmer
from django import template
from django.utils.safestring import mark_safe

register = template.Library()
stemmer = PorterStemmer()

@register.filter
def highlight(text, context):
    """
    高亮顯示文章中的實際匹配詞（matched_word），
    若無則退回原始使用者輸入的 query。
    context: {'query': str, 'matched': str | None}
    """
    if not context:
        return text

    query = context.get("query", "")
    matched_word = context.get("matched", "") or query

    if not matched_word:
        return text
    
    # 完全匹配
    pattern = re.compile(re.escape(matched_word), re.IGNORECASE)
    highlighted = pattern.sub(r'<span class="highlight">\g<0></span>', text)

    return mark_safe(highlighted)

@register.filter
def highlight_stem(text, stemmed_words):
    """
    高亮詞幹匹配 (stem match) 的字詞，顯示為淺粉紅背景。
    stemmed_words 應該是一個 list，例如：["run", "walk", "jump"]
    """
    if not stemmed_words:
        return text

    # 逐一標亮每個詞幹
    highlighted = text
    for word in stemmed_words:
        pattern = re.compile(r'(?<![>\w])' + re.escape(word) + r'\w*(?![^<]*>)', re.IGNORECASE)
        highlighted = pattern.sub(r'<span class="highlight-stem">\g<0></span>', highlighted)
    return mark_safe(highlighted)