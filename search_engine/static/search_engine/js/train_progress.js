document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("trainModelBtn");
  const progress = document.getElementById("trainProgress");
  const bar = document.getElementById("trainProgressBar");
  const text = document.getElementById("progressText");

  // 1. 在這裡設定您預期的訓練總時間（單位：秒）
  const ESTIMATED_TRAINING_TIME_SECONDS = 10; // 例如 300 秒 = 5 分鐘

  btn.addEventListener("click", () => {
    // 顯示進度條
    progress.style.display = "block";
    bar.classList.add("progress-bar-animated");
    bar.classList.remove("bg-danger");
    bar.style.width = "0%";
    text.textContent = "Training...";
    text.style.color = "#333";

    // 2. 根據預期總時間，動態計算動畫的間隔
    // 我們讓進度條在預期時間內跑到 95%
    const intervalTime = (ESTIMATED_TRAINING_TIME_SECONDS * 1000) / 95;

    let percent = 0;
    // 3. 使用計算出來的 intervalTime 作為動畫間隔
    const interval = setInterval(() => {
      if (percent < 95) {
        percent += 1;
        bar.style.width = percent + "%";
        text.textContent = `Training... ${percent}%`;
        if (percent > 40) {
          text.style.color = "white";
        }
      } else {
        clearInterval(interval);
      }
    }, intervalTime);

    // 發送請求給後端
    fetch("/train_model/", {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
    })
      .then(response => response.json())
      .then(data => {
        clearInterval(interval);
        bar.classList.remove("progress-bar-animated");

        const finishInterval = setInterval(() => {
          if (percent < 100) {
            percent++;
            bar.style.width = percent + "%";
            text.textContent = `Finalizing... ${percent}%`;
            text.style.color = "white";
          } else {
            clearInterval(finishInterval);
            text.textContent = "✅ Train Completed!";
            setTimeout(() => {
              progress.style.display = "none";
            }, 1500);
          }
        }, 20);
      })
      .catch(error => {
        clearInterval(interval);
        bar.classList.remove("progress-bar-animated");
        bar.classList.add("bg-danger");

        const finishInterval = setInterval(() => {
          if (percent < 100) {
            percent++;
            bar.style.width = percent + "%";
          } else {
            clearInterval(finishInterval);
            text.textContent = "❌ Training Failed";
            text.style.color = "white";
          }
        }, 20);
        console.error(error);
      });
  });

  // getCookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});