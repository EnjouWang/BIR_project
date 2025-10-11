const { createApp } = Vue;

function initVueApp(articlesData, keyword) {
  createApp({
    data() {
      return {
        keyword: keyword,
        articles: articlesData
      };
    },
    methods: {
      highlight(text) {
        if (!this.keyword) return text;
        const regex = new RegExp(`(${this.keyword})`, "gi");
        return text.replace(regex, '<span class="highlight">$1</span>');
      }
    }
  }).mount("#app");
}