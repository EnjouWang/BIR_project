document.addEventListener("DOMContentLoaded", function () {
  Object.keys(word2vecData).forEach((idx) => {
    const item = word2vecData[idx];

    // === 統一 CBOW 與 SG 的座標軸範圍 ===
    const allX = [...item.cbow.x, ...item.sg.x];
    const allY = [...item.cbow.y, ...item.sg.y];
    const xRange = [Math.min(...allX) - 15, Math.max(...allX) + 15];
    const yRange = [Math.min(...allY) - 25, Math.max(...allY) + 25];

    // CBOW 圖
    drawScatter(
      `cbowPlot_${parseInt(idx) + 1}`,
      item.cbow,
      `CBOW`,
        xRange,
        yRange,
        item.word
    );

    // Skip-Gram 圖
    drawScatter(
      `sgPlot_${parseInt(idx) + 1}`,
      item.sg,
      `Skip-Gram`,
        xRange,
        yRange,
        item.word
    );
  });
});

function drawScatter(containerId, modelData, title, xRange, yRange, mainWord) {
    // === 區分主要詞與相似詞 ===
    const mainIdx = modelData.words.indexOf(mainWord);

    const colors = modelData.words.map((_, i) =>
        i === mainIdx ? "crimson" : "royalblue"
    );

    const hoverTexts = modelData.words.map((w, i) => {
        if (modelData.similarities && modelData.similarities[i] !== undefined) {
        return `word: ${w}<br>similarity: ${modelData.similarities[i].toFixed(3)}`;
        } else {
        // 主詞或無相似度時
        return `word: ${w}`;
        }
    });

    const trace = {
    x: modelData.x,
    y: modelData.y,
    text: modelData.words,
    mode: "markers+text",
    textposition: "top center",
    hoverinfo: "text",
    hovertext: hoverTexts,
    marker: {
      size: 10,
      color: colors,
    },
    type: "scatter",
  };

  const layout = {
    title: title,
    xaxis: { title: "t-SNE X", showgrid: true, zeroline: false, range: xRange },
    yaxis: { title: "t-SNE Y", showgrid: true, zeroline: false, range: yRange },
    hovermode: "closest",
    plot_bgcolor: "#fafafa",
    paper_bgcolor: "#fafafa",
  };

  Plotly.newPlot(containerId, [trace], layout, { responsive: true });
}
