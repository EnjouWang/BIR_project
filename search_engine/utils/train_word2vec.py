from gensim.models import Word2Vec
from search_engine.models import Article
import re, os
import numpy as np
import nltk
from tqdm import tqdm
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from django.conf import settings

MODEL_DIR = os.path.join(settings.BASE_DIR, "search_engine/word2vec_models")
os.makedirs(MODEL_DIR, exist_ok=True)

def preprocess_texts(texts):
    # 自動嘗試下載 stopwords（若已存在則不會重複下載）
    try:
        stop_words = set(stopwords.words('english'))
    except LookupError:
        nltk.download('stopwords')
        stop_words = set(stopwords.words('english'))
    
    # 自動嘗試下載 punkt_tab tokenizer（若已存在則不會重複下載）
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab')

    processed = []

    for text in texts:
        text = re.sub(r"[^a-zA-Z\s]", "", text.lower())  # 移除符號與數字
        tokens = [w for w in word_tokenize(text) if w not in stop_words and len(w) > 2]
        processed.append(tokens)

    return processed

def train_dual_word2vec():
    """訓練 CBOW 與 Skip-gram 兩種模型"""
    # 收集所有文章文字
    articles = Article.objects.all()
    texts = [(a.title or '') + " " + (a.abstract or '') for a in articles]
    corpus = preprocess_texts(texts)

    # ===== 訓練 CBOW 模型 (sg=0) =====
    model_cbow = Word2Vec(
        sentences=corpus,
        vector_size=100,
        window=5,
        min_count=2,
        sg=0,              # CBOW
        workers=4
    )
    model_cbow.save(os.path.join(MODEL_DIR, "word2vec_cbow.model"))

    # ===== 訓練 Skip-Gram 模型 (sg=1) =====
    model_sg = Word2Vec(
        sentences=corpus,
        vector_size=100,
        window=5,
        min_count=2,
        sg=1,              # Skip-Gram
        workers=4
    )
    model_sg.save(os.path.join(MODEL_DIR, "word2vec_sg.model"))

    print("兩個模型訓練完成，已儲存至 word2vec_models 資料夾。")

def compute_document_vector(model, tokens):
    """平均詞向量作為文章向量"""
    if any(isinstance(t, list) for t in tokens):
        tokens = [w for sub in tokens for w in sub]
        
    vectors = []
    for token in tokens:
        if token in model.wv:
            vectors.append(model.wv[token])
    if not vectors:
        return np.zeros(model.vector_size)
    return np.mean(vectors, axis=0)

def update_article_vectors_dual():
    """為所有文章分別生成CBOW與SG的向量"""
    model_cbow = Word2Vec.load(os.path.join(MODEL_DIR, "word2vec_cbow.model"))
    model_sg = Word2Vec.load(os.path.join(MODEL_DIR, "word2vec_sg.model"))

    for article in tqdm(Article.objects.all(), desc="Updating article vectors", unit="article"):
        tokens = preprocess_texts([(article.title or '') + " " + (article.abstract or '') + " "])[0]

        vec_cbow = compute_document_vector(model_cbow, tokens)
        vec_sg = compute_document_vector(model_sg, tokens)

        article.vector_cbow = vec_cbow.tolist()
        article.vector_sg = vec_sg.tolist()
        article.save()

    print("所有文章的CBOW與SG向量已更新。")

if __name__ == "__main__":
    train_dual_word2vec()
    update_article_vectors_dual()