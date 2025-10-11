from django.db import models

# Create your models here.
# 儲存原始 XML 檔案
class UploadedXML(models.Model):
    file_name = models.CharField(max_length=255)
    xml_content = models.TextField()  # 存整個 XML 原始內容
    # uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name


# 解析後的文章資料
class Article(models.Model):
    uploaded_file = models.ForeignKey(
        UploadedXML,
        on_delete=models.CASCADE,  # 當 UploadedXML 被刪除時，相關 Article 也會被刪掉
        related_name='articles',   # 可用 uploaded_xml.articles.all() 取得相關文章
        null=True,
    )

    pmid = models.CharField(max_length=50, unique=True, null=True, blank=True)  # PubMed ID
    title = models.TextField()
    abstract = models.TextField(null=True, blank=True)
    authors = models.TextField(null=True, blank=True)   # "LastName, FirstName; LastName, FirstName"
    journal = models.CharField(max_length=255, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)

    # 方便搜尋：回傳前幾個字作為顯示
    def __str__(self):
        return f"{self.title[:50]}..."

    class Meta:
        ordering = ["-year"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["year"]),
            # models.Index(fields=["created_at"]),
        ]