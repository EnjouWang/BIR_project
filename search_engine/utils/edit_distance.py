def edit_distance(s1, s2):
    """
    使用動態規劃計算兩字串的 Edit Distance（Levenshtein Distance）
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # 初始化
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # 動態規劃
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1].lower() == s2[j - 1].lower() else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,     # 刪除
                dp[i][j - 1] + 1,     # 插入
                dp[i - 1][j - 1] + cost  # 取代
            )

    return dp[m][n]


def find_similar_words(word, vocab_list, threshold=2):
    """
    在字詞表 vocab_list 中，找出與 word 編輯距離 <= threshold 的候選字
    """
    similar = []
    for v in vocab_list:
        dist = edit_distance(word, v)
        if dist <= threshold:
            similar.append((v, dist))
    # 依距離排序
    similar.sort(key=lambda x: x[1])
    return similar
