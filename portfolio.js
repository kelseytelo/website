const backToTopButton = document.querySelector("[data-back-to-top]");

if (backToTopButton) {
  const updateVisibility = () => {
    backToTopButton.hidden = window.scrollY < 800;
  };

  backToTopButton.addEventListener("click", () => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    window.scrollTo({
      top: 0,
      behavior: reducedMotion ? "auto" : "smooth"
    });
  });

  window.addEventListener("scroll", updateVisibility, { passive: true });
  updateVisibility();
}
