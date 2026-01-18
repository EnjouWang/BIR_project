import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re
import math
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# 從 sentences 中切出 words，回傳有 stopword & 無 stopword 版本
def tokenize_text(text: str, remove_stopwords=True):
    # 下載 stopwords
    try:
        stop_words = set(stopwords.words('english'))
    except LookupError:
        nltk.download('stopwords')
        stop_words = set(stopwords.words('english'))
    
    # 下載 punkt_tab tokenizer
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab')

    text = re.sub(r"[^a-zA-Z\s]", "", text.lower())  # 移除符號與數字
    tokens = word_tokenize(text)
    if remove_stopwords:
        tokens = [w for w in tokens if w not in stop_words and len(w) > 2]

    return tokens

# --- 建立 corpus-level DF（document frequency） ---
def build_corpus_df(articles: List[str], remove_stopwords=True) -> Tuple[Dict[str, int], int]:
    """
    articles: list of article abstracts
    exclude_self: 若 later 想用 df_other (排除此篇) 可在計算時處理；此函式回傳包含所有文章的 df。
    remove_stopwords: 是否移除 stopwords
    回傳 (df_dict, N)
    """
    N = len(articles) # N 篇文章
    df = defaultdict(int)
    for abstracts in articles:
        if not abstracts:
            continue
        tokens = tokenize_text(abstracts, remove_stopwords)
        unique_tokens = set(tokens)
        for t in unique_tokens:
            df[t] += 1
    return dict(df), N

# --- 計算單篇文章每詞的 TF' * IDF （tf' 是 sublinear） ---
def compute_article_term_tfidf(article: str, corpus_df: Dict[str,int], corpus_N: int,
                                exclude_current_in_df: bool = False, remove_stopwords = True) -> Dict[str, float]:
    """
    article: 單篇文章（title+abstract 或 abstract）
    corpus_df: 由 build_corpus_df 產生（整個語料庫的 df）
    corpus_N: 語料庫總篇
    exclude_current_in_df: 若 True，用 df_other = max(df-1, 0) 計算 idf（排除當前文章）
    remove_stopwords: 是否移除 stopwords
    回傳: {token: score}
    """
    tokens = tokenize_text(article, remove_stopwords)
    tf_counts = Counter(tokens)  # raw term frequency in this article

    term_scores = {}
    for term, tf in tf_counts.items():
        # sublinear tf
        if tf <= 0:
            tf_sub = 0.0
        else:
            tf_sub = 1.0 + math.log(tf)
       # document frequency
        df = corpus_df.get(term, 0)
        if exclude_current_in_df:
            df_other = max(df - 1, 0)
        else:
            df_other = df

        # smooth idf: +1 inside log denom to avoid div by zero; +1 offset outside to keep positive
        idf = math.log((corpus_N) / (1 + df_other)) + 1.0

        score = tf_sub * idf
        term_scores[term] = score

    return term_scores

# --- 針對句子計算句子分數（平均 + 長度正規化） ---
def compute_sentences_tfidf(sentences: List[str], term_scores: Dict[str, float],
                                   length_normalization: str = "none", remove_stopwords = True) -> List[Dict]:
    """
    sentences: list of raw sentence strings from an article
    term_scores: {token: score} 來自 compute_article_term_tfidf
    length_normalization: "sqrt" 使用除以 sqrt(len_tokens)
                        "log" 使用除以 (1 + log(len_tokens))
                        "none" 無正規化
    remove_stopwords: 是否移除 stopwords
    回傳：list of dict { "sentence": s, "score": float, "tokens": [...], "token_scores": [...] }
    """
    results = []
    for s in sentences:
        toks = tokenize_text(s, remove_stopwords)
        if not toks:
            results.append({"sentence": s, "score": 0.0, "tokens": [], "token_scores": []})
            continue

        scores = [term_scores.get(t, 0.0) for t in toks]  # 詞若不在 article term_scores，視為 0
        avg = sum(scores) / len(scores)

        # 長度正規化
        L = len(toks)
        if length_normalization == "sqrt":
            norm = math.sqrt(L)
        elif length_normalization == "log":
            norm = 1.0 + math.log(L)
        else:
            norm = 1.0

        norm_score = avg / norm if norm > 0 else avg
        results.append({
            "sentence": s,
            "score": float(norm_score),
            "tokens": toks,
            "token_scores": [float(x) for x in scores]
        })

    # 排序（由大到小）
    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    return results_sorted

# --- 一個整合函式：給定 article 與整個 corpus texts，回傳 top-k 句子 ---
def sentences_tfidf(article: str, corpus_texts: List[str], sentences: List[str],
                                     k: int = 5, exclude_current_in_df: bool = False,
                                     length_normalization: str = "none", 
                                     remove_stopwords: bool = True) -> List[Dict]:
    df_dict, N = build_corpus_df(corpus_texts, remove_stopwords)
    term_scores = compute_article_term_tfidf(article, df_dict, N, 
                                             exclude_current_in_df, 
                                                remove_stopwords)
    scored_sentences = compute_sentences_tfidf(sentences, term_scores, length_normalization, remove_stopwords)
    return scored_sentences[:k]