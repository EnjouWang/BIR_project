function loadTFIDFSentences(articleId) {
    fetch(`/tfidf/get_sentences/${articleId}/`)
        .then(response => response.json())
        .then(data => {
            // 標題
            document.getElementById("modalTitle").innerText = data.title;

            // 摘要
            document.getElementById("modalAbstract").innerText = data.abstract || "(No abstract)";

            // 統計資訊 - 改用網格佈局
            let statsHTML = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-label">Characters (with spaces)</div>
                        <div class="stat-value">${data.stats.characters_including_spaces}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Characters (no spaces)</div>
                        <div class="stat-value">${data.stats.characters_excluding_spaces}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Words</div>
                        <div class="stat-value">${data.stats.words}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Sentences</div>
                        <div class="stat-value">${data.stats.sentences}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Non-ASCII chars</div>
                        <div class="stat-value">${data.stats.non_ascii_characters}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Non-ASCII words</div>
                        <div class="stat-value">${data.stats.non_ascii_words}</div>
                    </div>
                </div>
            `;
            document.getElementById("modalStats").innerHTML = statsHTML;

            // 填充四個不同方法的句子列表
            populateSentenceList("sentences-all", data.method_all);
            populateSentenceList("sentences-search", data.method_search);
            populateSentenceList("sentences-all-stop", data.method_all_stop);
            populateSentenceList("sentences-search-stop", data.method_search_stop);
            populateSentenceList("sentences-all-norm-sqrt", data.method_all_norm_sqrt);
            populateSentenceList("sentences-search-norm-sqrt", data.method_search_norm_sqrt);
            populateSentenceList("sentences-all-norm-log", data.method_all_norm_log);
            populateSentenceList("sentences-search-norm-log", data.method_search_norm_log);
        })
        .catch(error => {
            console.error('Error loading TF-IDF sentences:', error);
        });
}

// 輔助函數：填充句子列表
function populateSentenceList(elementId, sentences) {
    const list = document.getElementById(elementId);
    list.innerHTML = "";
    list.className = "sentence-list";

    if (!sentences || sentences.length === 0) {
        list.innerHTML = '<p class="text-muted">No sentences available</p>';
        return;
    }

    sentences.forEach((item, index) => {
        let li = document.createElement("li");
        li.className = "sentence-item";
        li.setAttribute("data-rank", index + 1);
        li.innerHTML = `
            <span class="sentence-score">Score: ${item.score.toFixed(4)}</span>
            <p class="sentence-text">${item.sentence}</p>
        `;
        list.appendChild(li);
    });
}