from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UploadedXML, Article
from .forms import UploadXMLForm
from .utils.xml_parser import parse_pubmed_xml
from .utils.text_stat import compute_text_stat
from .utils.zipf_analysis import clean_text, get_word_frequencies, compute_zipf_distribution
from .utils.edit_distance import find_similar_words
from nltk.stem import PorterStemmer
from collections import Counter
import re
import json

# Create your views here.
def home(request):
    # 給年份下拉選單用
    years = Article.objects.values_list('year', flat=True).distinct().order_by('-year')
    journals = Article.objects.values_list("journal", flat=True).distinct().order_by("journal")

    return render(request, "search_engine/home.html", {
        "years": years,
        "journals": journals,
    })

def upload_xml(request):
    if request.method == "POST":
        files = request.FILES.getlist("xml_file")

        if not files:
            messages.error(request, "未選擇任何檔案。")
            return redirect("upload_xml")
        
        for uploaded_file in files:
            # uploaded_file = form.cleaned_data["xml_file"]
            try:
                xml_content = uploaded_file.read().decode("utf-8")

                # 存入 UploadedXML
                uploaded = UploadedXML.objects.create(
                    file_name=uploaded_file.name,
                    xml_content=xml_content
                )

                # 呼叫 parser 建立 Article 資料
                parse_pubmed_xml(xml_content, uploaded)

                messages.success(request, f"{uploaded_file.name} 上傳並解析成功！") 

            except UnicodeDecodeError:
                messages.error(request, "檔案解碼失敗，請確認是否為 UTF-8 格式")
            except Exception as e:
                messages.error(request, f"{uploaded_file.name} 上傳時發生錯誤：{str(e)}")

        return redirect("upload_xml")  # 重新導向到同一頁
    else:
        form = UploadXMLForm()

    files = UploadedXML.objects.all()
    return render(request, "search_engine/upload.html", {"form": form, "files": files})

def delete_file(request, file_id):
    if request.method == "POST":
        file_obj = get_object_or_404(UploadedXML, id=file_id)
        file_obj.delete()
        messages.success(request, f"{file_obj.file_name} 已刪除！")
    return redirect("upload_xml")

def search_result(request):
    query = request.GET.get('q', '').strip()
    year = request.GET.get('year', '')
    journal = request.GET.get("journal", "")

    stemmer = PorterStemmer()
    stemmed_list = []
    use_stemmer = request.GET.get("use_stemmer", "off")  # 新增：使用者選項，是否開啟stemmer search

    articles = Article.objects.all()
    closest_word = ''
    stem_matches = set()

    if query:
        # ====== (1) 先進行原始搜尋 ======
        results = articles.filter(title__icontains=query) | articles.filter(abstract__icontains=query)
        
        # ====== (2) 若無結果，使用 Edit Distance ======        
        if not results.exists():
            # 從所有文章標題與摘要中提取單詞
            all_texts = list(Article.objects.values_list('title', flat=True)) + list(Article.objects.values_list('abstract', flat=True))
            all_words = set()
            for text in all_texts:
                if text:
                    for word in re.findall(r'\b\w+\b', text.lower()):  # 使用 \b\w+\b 抓出英文字詞
                        all_words.add(word)
            similar_candidates = find_similar_words(query, all_words, threshold=2)

            if similar_candidates:
                closest_word = similar_candidates[0][0]
                results = articles.filter(title__icontains=closest_word) | articles.filter(abstract__icontains=closest_word)
                messages.info(request, f"顯示與「{query}」相近的搜尋結果（最接近詞：{closest_word}）")

        # ====== (3) 若使用者選擇啟用 Stemmer ======
        # if use_stemmer == "on":
        #     query_stem = stemmer.stem(query.lower())
        #     all_articles = Article.objects.all()

        #     for article in all_articles:
        #         combined_text = (article.title or '') + " " + (article.abstract or '')
        #         words = re.findall(r'\b\w+\b', combined_text.lower())
        #         stemmed_words = [stemmer.stem(w) for w in words]
        #         if query_stem in stemmed_words:
        #             stem_matches.add(article.id)

        #     if stem_matches:
        #         stem_results = articles.filter(id__in=stem_matches)
        #         results = (results | stem_results).distinct()  # 合併結果避免重複
        #         messages.success(request, f"已啟用詞幹搜尋（Porter Stemmer Mode）")

        #     stemmed_list = [query_stem]  # 傳給模板用於高亮顯示

        articles = results

    # ====== (4) 篩選年份、期刊 ======
    if year:
        articles = articles.filter(year=year)
    if journal:
        articles = articles.filter(journal=journal)

    # ====== (5) 統計與排序 ======
    articles_with_stats = [] # 排序顯示文章
    actual_keyword = closest_word if 'closest_word' in locals() and closest_word else query
    for article in articles:
        stats = compute_text_stat(article.abstract or '', actual_keyword)

        combined_text = (article.title or '') + " " + (article.abstract or '')
        keyword_count = len(re.findall(re.escape(actual_keyword), combined_text, re.IGNORECASE))
        
        stats["keyword_counts"] = keyword_count # 覆蓋 stats["keyword_counts"]，其他項目維持摘要為主
        article.stats = stats
        articles_with_stats.append(article)

    # 依 keyword_counts 排序（降冪）
    articles = sorted(articles_with_stats, key=lambda x: x.stats["keyword_counts"], reverse=True)

    # 給年份下拉選單用
    years = Article.objects.values_list('year', flat=True).distinct().order_by('-year')
    journals = Article.objects.values_list("journal", flat=True).distinct().order_by("journal")

    return render(request, "search_engine/result.html", {
        "articles": articles,
        "query": query,
        "closest_word": closest_word,
        "highlight_context": {"query": query, "matched": closest_word},
        "stemmed_list": stemmed_list,
        "year": year,
        "journal": journal,
        "years": years,
        "journals": journals,
    })

def zipf_analysis(request):
    ps = PorterStemmer()
    abstracts = list(Article.objects.values_list("abstract", flat=True))

    if not abstracts:
        return render(request, "zipf_analysis.html", {
            "error_message": "目前資料庫中沒有任何文章摘要可供分析。"
        })

    # 原始詞頻
    raw_counter = get_word_frequencies(abstracts)

    # Porter 詞幹化
    stemmed_counter = Counter()
    for text in abstracts:
        cleaned = clean_text(text)
        stemmed_words = [ps.stem(w) for w in cleaned.split()]
        stemmed_counter.update(stemmed_words)

    # 計算 Zipf 分佈
    raw_ranks, raw_words, raw_freqs, raw_norm, _ = compute_zipf_distribution(raw_counter)
    stem_ranks, stem_words, stem_freqs, stem_norm, _ = compute_zipf_distribution(stemmed_counter)

    # 取前 500 名詞彙（避免資料太多導致圖表 lag）
    max_points = 500
    raw_ranks, raw_words, raw_freqs, raw_norm = raw_ranks[:max_points], raw_words[:max_points], raw_freqs[:max_points], raw_norm[:max_points]
    stem_ranks, stem_words, stem_freqs, stem_norm = stem_ranks[:max_points], stem_words[:max_points], stem_freqs[:max_points], stem_norm[:max_points]

    context = {
        "raw_data": json.dumps({
            "ranks": raw_ranks,
            "words": raw_words,
            "freqs": raw_freqs,
            "norm_freqs": raw_norm,
        }),
        "stem_data": json.dumps({
            "ranks": stem_ranks,
            "words": stem_words,
            "freqs": stem_freqs,
            "norm_freqs": stem_norm,
        })
    }
    return render(request, "search_engine/zipf_analysis.html", context)