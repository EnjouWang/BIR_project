## Biomedical Information Retrieval Project #4
### 一、系統概要
本次作業新增的功能主要是使用 TF IDF，針對整篇文章中的所有句子進行語意相關性排序，並提供多種不同的 TF IDF 計算公式以進行比較。此功能的目的是對一篇文章進行主題摘要。
## 二、TF IDF 公式設計 
本次作業中主要討論三個面向的設計：
### Term Frequency（TF）：
使用 Sublinear TF（log scaling），避免高詞頻詞彙的過度放大現象。
$$
TF_{sub}=1+log⁡(TF)
$$
### Inverse Document Frequency（IDF）：
分別測試使用系統全部文章（約2500篇癌症主題文章）以及指使用特定主題文章（例如：乳癌）作為 DF 統計的範圍。
### Sentence TF-IDF 分數計算：
首先以句子當中詞的平均 TF IDF 分數作為該語句的TF IDF 分數。接著分別測試兩種長度正規化的方法對摘要結果的影響。
- SQRT 正規化：$$score=\frac{TF-IDF}{\sqrt{length}}$$
- LOG 正規化：$$score=\frac{TF-IDF}{\log{⁡(length)}+1}$$
 
## 三、實際例子分析
以乳癌（breast cancer）作為測試的子主題，對以下幾種方法進行分析：


| 方法                        | 是否使用系統全部文章 | 是否移除Stopwords | 是否加入長度正規化 | 正規化形式 |
| --------------------------- | -------------------- | ----------------- | ------------------ | ---------- |
| All Corpus                  |✓|✓|✗|            |
| All Corpus (Stopwords)      |✓|✗|✗|            |
| All Corpus (Norm: SQRT)     |✓|✓|✓|$$\sqrt{len}$$|
| All Corpus (Norm: LOG)      |✓|✓|✓|$$log⁡(len)+1$$|
| Search Results              |✗|✓|✗|            |
| Search Results (Stopwords)  |✗|✗|✗|            |
| Search Results (Norm: SQRT) |✗|✓|✓|$$\sqrt{len}$$|
|  Search Results (Norm: LOG) |✗|✓|✓|$$log⁡(len)+1$$|


- All Corpus：長句優勢最大；易受高 TF 詞影響
- All Corpus (Stopwords)：主題詞更突出；冗詞降低
- All Corpus (Norm: SQRT)：長句影響降低，短句更容易上升
- All Corpus (Norm: LOG)：正規化強度小於 SQRT；長句仍略占優
- Search Results：僅看查詢詞；最像關鍵詞比對
- Search Results (Stopwords)：更凸顯主題詞出現比例
- Search Results (Norm: SQRT)：關鍵詞密度高的短句更容易上升
- Search Results (Norm: LOG)：對長句懲罰較弱；結果介於 SQRT 與無正規化之間

