from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from gensim.models import Word2Vec
from .models import UploadedXML, Article
from .forms import UploadXMLForm
from .utils.xml_parser import parse_pubmed_xml, clean_empty_abstracts
from .utils.text_stat import compute_text_stat
from .utils.zipf_analysis import clean_text, get_word_frequencies, compute_zipf_distribution
from .utils.edit_distance import find_similar_words
from .utils.train_word2vec import train_dual_word2vec, update_article_vectors_dual
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
from collections import Counter
import re, os
import json

CBOW_MODEL_PATH = os.path.join("search_engine/word2vec_models", "word2vec_cbow.model")
SG_MODEL_PATH = os.path.join("search_engine/word2vec_models", "word2vec_sg.model")

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
                clean_empty_abstracts()

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
    semantic = request.GET.get("semantic", "none")  # 語意搜尋選項

    stemmer = PorterStemmer()
    stemmed_list = []
    use_stemmer = request.GET.get("use_stemmer", "off")  # 使用者選項，是否開啟stemmer search

    articles = Article.objects.all()
    closest_word = ''
    stem_matches = set()

    if not query:
        messages.error(request, "請輸入搜尋關鍵字。")
        return render(request, "search_engine/home.html", {"articles": []})

    if semantic == "none":
        # ====== (1) 先進行原始搜尋 (完整詞匹配) ======
        pattern = rf"\b{re.escape(query)}\b"
        results = [a for a in Article.objects.all() if (
            (a.title and re.search(pattern, a.title, re.IGNORECASE)) or
            (a.abstract and re.search(pattern, a.abstract, re.IGNORECASE))
        )]
        
        # ====== (2) 若無結果，使用 Edit Distance ======        
        if not results:
            # 從所有文章標題與摘要中提取單詞
            all_texts = list(Article.objects.values_list('title', flat=True)) + list(Article.objects.values_list('abstract', flat=True))
            all_words = {w for text in all_texts if text for w in re.findall(r'\b\w+\b', text.lower())}
            similar_candidates = find_similar_words(query, all_words, threshold=2)

            if similar_candidates:
                closest_word = similar_candidates[0][0]
                results = articles.filter(title__icontains=closest_word) | articles.filter(abstract__icontains=closest_word)
                messages.info(request, f"顯示與「{query}」相近的搜尋結果（最接近詞：{closest_word}）")
        
        # 排序結果 by 關鍵字出現次數
        results_with_count = []
        for article in results:
            combined_text = (article.title or '') + " " + (article.abstract or '')
            keyword_count = len(re.findall(re.escape(query), combined_text, re.IGNORECASE))
            article.keyword_count = keyword_count
            results_with_count.append(article)

        results = sorted(results_with_count, key=lambda x: x.keyword_count, reverse=True)

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
    elif semantic in ["cbow", "sg"]:
        model_path = CBOW_MODEL_PATH if semantic == "cbow" else SG_MODEL_PATH
        mode_name = "CBOW" if semantic == "cbow" else "Skip-Gram"

        if not os.path.exists(model_path):
            messages.error(request, f"尚未訓練 {mode_name} 模型，請先在 Upload 頁面中重新訓練。")
            articles = []
        else:
            model = Word2Vec.load(model_path)

            # 預處理查詢詞
            query_tokens = [w.lower() for w in word_tokenize(query) if w.isalpha()]
            query_vectors = [model.wv[w] for w in query_tokens if w in model.wv]

            if not query_vectors:
                messages.error(request, f"無法在 {mode_name} 模型中找到「{query}」相關詞彙。")
                articles = []
            else:
                query_vector = np.mean(query_vectors, axis=0).reshape(1, -1)

                # 計算語意相似度
                scored_articles = []
                threshold_cbow = 0.9
                threshold_sg = 0.8
                for article in Article.objects.all():
                    vec_field = article.vector_cbow if semantic == "cbow" else article.vector_sg
                    if not vec_field or len(vec_field) == 0:
                        continue
                    
                    doc_vector = np.array(vec_field).reshape(1, -1)
                    similarity = cosine_similarity(query_vector, doc_vector)[0][0]
                    threshold = threshold_cbow if semantic == "cbow" else threshold_sg
                    if similarity >= threshold:
                        scored_articles.append((article, similarity))

                scored_articles.sort(key=lambda x: x[1], reverse=True)
                articles = [a for a, _ in scored_articles]

                messages.success(request, f"{mode_name} 語意搜尋完成，共找到 {len(articles)} 筆相關結果。")

    # ====== (4) 篩選年份、期刊 ======
    if year:
        articles = [a for a in articles if str(a.year) == str(year)]
    if journal:
        articles = [a for a in articles if a.journal == journal]

    # ====== (5) 文字統計 ======
    actual_keyword = closest_word if 'closest_word' in locals() and closest_word else query
    for article in articles:
        stats = compute_text_stat(article.abstract or '', actual_keyword)

        combined_text = (article.title or '') + " " + (article.abstract or '')
        keyword_count = len(re.findall(re.escape(actual_keyword), combined_text, re.IGNORECASE))
        
        stats["keyword_counts"] = keyword_count # 覆蓋 stats["keyword_counts"]，其他項目維持摘要為主
        article.stats = stats

    # 給下拉選單用
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
        "semantic": semantic,
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

@csrf_exempt
def train_model(request):
    if request.method == "POST":
        train_dual_word2vec()
        update_article_vectors_dual()
        return JsonResponse({"status": "success", "message": "Model trained successfully."})
    
def word2vec_analysis(request):
    """顯示語料中最常見的詞與其相似詞（CBOW + SG）"""
    # === 準備語料 ===
    texts = list(Article.objects.values_list("abstract", flat=True))
    if not texts:
        return render(request, "search_engine/word2vec_analysis.html", {
            "error_message": "目前資料庫中沒有文章可供分析。"
        })

    # === 清理文字並統計詞頻 ===
    stop_words = set(stopwords.words("english"))
    tokens = []
    for text in texts:
        words = [w.lower() for w in word_tokenize(text) if w.isalpha() and w.lower() not in stop_words]
        tokens.extend(words)

    counter = Counter(tokens)
    top_words = [w for w, _ in counter.most_common(5)]  # 前5高頻詞

    # === 載入已訓練好的模型 ===
    model_cbow = Word2Vec.load(CBOW_MODEL_PATH)
    model_sg = Word2Vec.load(SG_MODEL_PATH)

    # === 生成每個 top word 的相似詞資料 ===
    word2vec_data = {}

    for i, word in enumerate(top_words):
        cbow_data, sg_data = {}, {}

        for model_name, model, target in [
            ("cbow", model_cbow, cbow_data),
            ("sg", model_sg, sg_data),
        ]:
            if word not in model.wv:
                continue

            similar = model.wv.most_similar(word, topn=10)
            words = [word] + [w for w, _ in similar]
            similarities = [1.0] + [sim for _, sim in similar]
            vectors = np.array([model.wv[w] for w in words])

            # t-SNE降維，確保 perplexity < n_samples
            perplexity = min(5, len(words) - 1)
            tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)
            reduced = tsne.fit_transform(vectors)

            target["x"] = reduced[:, 0].tolist()
            target["y"] = reduced[:, 1].tolist()
            target["words"] = words
            target["similarities"] = similarities

        word2vec_data[i] = {
            "word": word,
            "cbow": cbow_data,
            "sg": sg_data,
        }

    context = {
        "top_words": [{"word": w} for w in top_words],
        "word2vec_data": json.dumps(word2vec_data),
    }
    return render(request, "search_engine/word2vec.html", context)