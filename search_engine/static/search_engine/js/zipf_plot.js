document.addEventListener("DOMContentLoaded", function () {
  const viewMode = document.getElementById("viewMode");

  // ===== Hover 提示文字產生函式 =====
  function makeHoverText(data) {
    return data.words.map((w, i) =>
      `Word: <b>${w}</b><br>` +
      `Rank: ${data.ranks[i]}<br>` +
      `Frequency: ${data.freqs[i]}<br>`
    );
  }

  function makeHoverTextNorm(data) {
    return data.words.map((w, i) =>
      `Word: <b>${w}</b><br>` +
      `Rank: ${data.ranks[i]}<br>` +
      `Normalized: ${data.norm_freqs[i].toFixed(6)}`
    );
  }

  // 建立兩組資料
  const traceRawFreq = {
    x: rawData.ranks,
    y: rawData.freqs,
    text: makeHoverText(rawData),
    hovertemplate: "%{text}<extra>Original</extra>",
    type: "scatter",
    mode: "lines+markers",
    name: "Original (Raw)",
    line: { color: "royalblue" },
  };

  const traceStemFreq = {
    x: stemData.ranks,
    y: stemData.freqs,
    text: makeHoverText(stemData),
    hovertemplate: "%{text}<extra>Stemmed</extra>",
    type: "scatter",
    mode: "lines+markers",
    name: "Stemmed (Raw)",
    line: { color: "deeppink" },
  };

  const traceRawNorm = {
    x: rawData.ranks,
    y: rawData.norm_freqs,
    text: makeHoverTextNorm(rawData),
    hovertemplate: "%{text}<extra>Original</extra>",
    type: "scatter",
    mode: "lines+markers",
    name: "Original (Normalized)",
    line: { color: "royalblue" },
  };

  const traceStemNorm = {
    x: stemData.ranks,
    y: stemData.norm_freqs,
    text: makeHoverTextNorm(stemData),
    hovertemplate: "%{text}<extra>Stemmed</extra>",
    type: "scatter",
    mode: "lines+markers",
    name: "Stemmed (Normalized)",
    line: { color: "deeppink" },
  };

  const layout = {
    xaxis: { title: "Rank", type: "log" },
    yaxis: { title: "Frequency", type: "log" },
    title: "Zipf Distribution (log-log scale)",
    legend: { x: 0.75, y: 0.95 },
  };

  function updatePlot(mode) {
    let data, yTitle;
    if (mode === "freq") {
      data = [traceRawFreq, traceStemFreq];
      yTitle = "Frequency";
    } else {
      data = [traceRawNorm, traceStemNorm];
      yTitle = "Normalized Frequency";
    }
    layout.yaxis.title = yTitle;
    Plotly.newPlot("zipfPlot", data, layout);
  }

  // 初始顯示
  updatePlot("freq");

  // 當使用者切換顯示模式
  viewMode.addEventListener("change", (e) => {
    updatePlot(e.target.value);
  });
});
