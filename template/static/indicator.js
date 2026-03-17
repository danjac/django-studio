document.addEventListener('alpine:init', () => {
  Alpine.data('hxIndicator', () => ({
    width: 0,
    init() {
      setInterval(() => {
        if (this.$el.classList.contains('htmx-request')) {
          this.width = this.width + (Math.random() / 100) + 1;
          this.width = this.width > 30 ? -30 : this.width;
        } else {
          this.width = 0;
        }
        this.$el.style.width = this.width > 0 ? `${10 + this.width * 90}%` : '0px';
      }, 36);
    },
  }));
});
