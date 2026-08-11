const slideshow = document.querySelector("[data-landing-slideshow]");
const images = window.luckImages || [];

if (slideshow && images.length > 0) {
  const layers = Array.from(slideshow.querySelectorAll(".landing-slide"));
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let visibleLayer = 0;
  let currentImage = images[0];
  let queue = [];

  const shuffle = (items) => {
    const shuffled = [...items];

    for (let index = shuffled.length - 1; index > 0; index -= 1) {
      const randomIndex = Math.floor(Math.random() * (index + 1));
      [shuffled[index], shuffled[randomIndex]] = [shuffled[randomIndex], shuffled[index]];
    }

    return shuffled;
  };

  const refillQueue = () => {
    queue = shuffle(images.filter((image) => image.src !== currentImage.src));
  };

  images.slice(1).forEach((image) => {
    const preload = new Image();
    preload.src = image.src;
  });

  if (!reducedMotion && images.length > 1) {
    refillQueue();

    window.setInterval(() => {
      if (queue.length === 0) {
        refillQueue();
      }

      const nextImage = queue.shift();
      const nextLayer = visibleLayer === 0 ? 1 : 0;

      const image = layers[nextLayer].querySelector(".landing-image");
      const fortune = layers[nextLayer].querySelector(".landing-fortune");

      image.src = nextImage.src;
      image.alt = nextImage.alt;
      fortune.textContent = nextImage.fortune;
      layers[nextLayer].classList.add("is-visible");
      layers[nextLayer].setAttribute("aria-hidden", "false");
      layers[visibleLayer].classList.remove("is-visible");
      layers[visibleLayer].setAttribute("aria-hidden", "true");

      currentImage = nextImage;
      visibleLayer = nextLayer;
    }, 6500);
  }
}
