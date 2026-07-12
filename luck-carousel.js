const carousel = document.querySelector("[data-luck-carousel]");
const luckImages = window.luckImages || [];

if (carousel && luckImages.length) {
  const image = carousel.querySelector(".carousel-image");
  const previous = carousel.querySelector(".carousel-button-previous");
  const next = carousel.querySelector(".carousel-button-next");
  let currentIndex = 0;

  const showImage = () => {
    const current = luckImages[currentIndex];
    image.src = current.src;
    image.alt = "";
  };

  previous.addEventListener("click", () => {
    currentIndex = (currentIndex - 1 + luckImages.length) % luckImages.length;
    showImage();
  });

  next.addEventListener("click", () => {
    currentIndex = (currentIndex + 1) % luckImages.length;
    showImage();
  });

  if (luckImages.length < 2) {
    previous.hidden = true;
    next.hidden = true;
  }

  showImage();
} else if (carousel) {
  carousel.hidden = true;
}
