from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UploadedXML, Article
from .forms import UploadXMLForm
from .utils.xml_parser import parse_pubmed_xml
from .utils.text_stat import compute_text_stat
import re

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
        form = UploadXMLForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data["xml_file"]

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
                return redirect("upload_xml")  # 重新導向到同一頁

            except UnicodeDecodeError:
                messages.error(request, "檔案解碼失敗，請確認是否為 UTF-8 格式")
        else:
            messages.error(request, "上傳失敗，請檢查檔案格式或大小")
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
    articles = Article.objects.all()
    if query:
        articles = articles.filter(title__icontains=query) | articles.filter(abstract__icontains=query)
    if year:
        articles = articles.filter(year=year)
    if journal:
        articles = articles.filter(journal=journal)

    # 加入文字統計
    for article in articles:
        stats = compute_text_stat(article.abstract or '', query)

        combined_text = (article.title or '') + " " + (article.abstract or '')
        keyword_count = len(re.findall(re.escape(query), combined_text, re.IGNORECASE))
        
        stats["keyword_counts"] = keyword_count # 覆蓋 stats["keyword_counts"]，其他項目維持摘要為主
        article.stats = stats

    # 給年份下拉選單用
    years = Article.objects.values_list('year', flat=True).distinct().order_by('-year')
    journals = Article.objects.values_list("journal", flat=True).distinct().order_by("journal")

    return render(request, "search_engine/result.html", {
        "articles": articles,
        "query": query,
        "year": year,
        "journal": journal,
        "years": years,
        "journals": journals,
    })
