import re
from collections import Counter
import matplotlib.pyplot as plt
from nltk.stem import PorterStemmer
from search_engine.models import Article  # 假設你的模型名稱是 Article

def clean_text(text):
    """
    移除非文字符號、轉小寫，並保留英文字母與數字。
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_word_frequencies(texts):
    """
    傳入多篇文章文字列表，回傳整體詞頻 Counter。
    """
    counter = Counter()
    for text in texts:
        cleaned = clean_text(text)
        words = cleaned.split()
        counter.update(words)
    return counter

def compute_zipf_distribution(counter):
    """
    給定詞頻 Counter，回傳 (rank, frequency, normalized frequency)。
    """
    total = sum(counter.values())
    sorted_words = counter.most_common()
    ranks = list(range(1, len(sorted_words) + 1))
    words = [word for word, _ in sorted_words]
    freqs = [freq for _, freq in sorted_words]
    norm_freqs = [f / total for f in freqs]
    return ranks, words, freqs, norm_freqs, sorted_words

def analyze_zipf_distribution():
    """
    主流程：分析資料庫中所有文章的摘要，並繪製 Zipf 分佈圖。
    """
    ps = PorterStemmer()
    abstracts = list(Article.objects.values_list("abstract", flat=True))

    print(f"讀取到 {len(abstracts)} 篇文章摘要。")

    # === (1) 原始文字詞頻統計 ===
    raw_counter = get_word_frequencies(abstracts)

    # === (2) Porter 詞幹化 (Stemming) 統計 ===
    stemmed_counter = Counter()
    for text in abstracts:
        cleaned = clean_text(text)
        stemmed_words = [ps.stem(w) for w in cleaned.split()]
        stemmed_counter.update(stemmed_words)

    # === (3) 分別計算 Zipf 分佈 ===
    raw_ranks, raw_freqs, raw_norm, raw_words = compute_zipf_distribution(raw_counter)
    stem_ranks, stem_freqs, stem_norm, stem_words = compute_zipf_distribution(stemmed_counter)

    # === (4) 顯示前 10 名詞彙比較 ===
    print("\n[原始文字前10名]")
    for w, f in raw_words[:10]:
        print(f"{w}: {f}")

    print("\n[Porter 詞幹後前10名]")
    for w, f in stem_words[:10]:
        print(f"{w}: {f}")

    # === (5) 畫 Zipf 分佈圖 ===
    plt.figure(figsize=(8,6))
    plt.loglog(raw_ranks, raw_freqs, label="Original", marker='o')
    plt.loglog(stem_ranks, stem_freqs, label="Stemmed", marker='x')
    plt.xlabel("Rank (排名)")
    plt.ylabel("Frequency (詞頻)")
    plt.title("Zipf Distribution (原始 vs Porter Stemmed)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    analyze_zipf_distribution()
