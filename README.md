## Biomedical Information Retrieval Project #1
### 一、系統簡介
本次作業實作了一個簡易的搜尋引擎，針對 PubMed 格式的 XML 檔案進行解析、儲存與檢索。
系統重點在於提供使用者一個直覺的搜尋介面，並搭配文字統計功能，讓使用者能快速掌握文獻特徵。
### 二、主要功能
1. 檔案上傳與解析
    - 使用者可以上傳 PubMed XML 檔案。
    - 系統會自動解析文獻內容，包括：PMID、標題 (Title)、摘要 (Abstract)、期刊名稱 (Journal)、年份 (Year)
    - 上傳後的檔案會存入資料庫，並可被後續搜尋使用。
2. 搜尋與過濾
    - 在搜尋框輸入關鍵字，系統會在文獻標題與摘要中搜尋關鍵字
    - 搜尋框支援依年份 (Year) 及期刊 (Journal) 過濾
    - 搜尋結果每篇文獻獨立顯示，若標題或摘要包含關鍵字，會自動以藍綠色為底色標註。
3. 文字統計功能
    針對搜尋結果的每篇文章，系統會提供文字統計資訊：
    - Characters (with spaces)：摘要字元總數 (包含空白)。
    - Characters (no spaces)：摘要字元總數 (不含空白)。
    - Words：摘要中的單字數。
    - Sentences：摘要的句子數。
    - Non-ASCII Characters：非 ASCII 字元數 (如中文、希臘字母)。
    - Non-ASCII Words：包含非 ASCII 字元的單字數。
    - Keyword Counts：關鍵字在 標題 + 摘要 中的出現次數。
### 三、介面設計
- 首頁 (Home)：提供搜尋框，並顯示可選的年份與期刊過濾器。
- 結果頁 (Result)：顯示搜尋結果，並附上文字統計。
- 上傳頁 (Upload)：上傳並管理 XML 檔案，支援刪除功能。
