document.addEventListener("DOMContentLoaded", function () {
  const backToTopBtn = document.getElementById("backToTopBtn");

  // 監聽捲動事件，決定按鈕是否顯示
  window.addEventListener("scroll", () => {
    if (document.documentElement.scrollTop > 300 || document.body.scrollTop > 300) {
      backToTopBtn.style.display = "flex";
    } else {
      backToTopBtn.style.display = "none";
    }
  });

  // 點擊按鈕後平滑回頂端
  backToTopBtn.addEventListener("click", () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  });
});