const grid = document.querySelector("[data-photo-grid]");
const photos = window.archivePhotos || [];

for (const photo of photos) {
  const card = document.createElement("figure");
  card.className = "photo-card";

  if (photo.src) {
    const media = document.createElement("div");
    media.className = "photo-media";

    const image = document.createElement("img");
    image.className = "photo-holder book-front";
    image.src = photo.src;
    image.alt = photo.caption || "";
    media.append(image);

    if (photo.backSrc) {
      const backImage = document.createElement("img");
      backImage.className = "photo-holder book-back";
      backImage.src = photo.backSrc;
      backImage.alt = `${photo.caption || "Book"} back cover`;
      media.append(backImage);
    }

    card.append(media);
  } else {
    const holder = document.createElement("div");
    holder.className = "photo-holder";
    card.append(holder);
  }

  const caption = document.createElement("figcaption");
  caption.textContent = photo.caption || "";
  card.append(caption);

  grid.append(card);
}
