import xml.etree.ElementTree as ET
from search_engine.models import Article

def parse_pubmed_xml(xml_content, uploaded_file):
    root = ET.fromstring(xml_content)
    print("Root tag:", root.tag)
    # print(ET.tostring(root, encoding="utf-8").decode())

    articles = [root] if root.tag == "PubmedArticle" else root.findall(".//PubmedArticle")
    for article in articles:
        print("Parsing article...")
        try:
            pmid = article.findtext(".//PMID")
            print(f"find: {pmid}")
            title = article.findtext(".//ArticleTitle")
            abstract_texts = []
            for abstract_elem in article.findall(".//Abstract/AbstractText"):
                text_with_children = "".join(abstract_elem.itertext())
                if abstract_elem.text:
                    abstract_texts.append(text_with_children.strip())
            abstract = " ".join(abstract_texts)
            
            # authors
            authors = []
            for author in article.findall(".//Author"):
                lastname = author.findtext("LastName")
                firstname = author.findtext("FirstName")
                if lastname and firstname:
                    authors.append(f"{lastname}, {firstname}")
            authors_str = "; ".join(authors)

            journal = article.findtext(".//Journal/Title")
            year = article.findtext(".//PubDate/Year")

            # save to DB
            Article.objects.update_or_create(
                pmid = pmid,
                defaults={
                    "title": title or "",
                    "abstract": abstract or "",
                    "authors": authors_str,
                    "journal": journal,
                    "year": year,
                    "uploaded_file": uploaded_file,
                }
            )

        except Exception as e:
            print(f"Failed to parse: {e}")

def clean_empty_abstracts():
    null_deleted, _ = Article.objects.filter(abstract__isnull=True).delete()
    empty_deleted, _ = Article.objects.filter(abstract='').delete()
    print(f"清理完成：刪除 {null_deleted + empty_deleted} 筆沒有摘要的資料。")