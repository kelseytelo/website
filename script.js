const grid = document.querySelector("[data-photo-grid]");
const photos = window.archivePhotos || [];

for (const photo of photos) {
  const card = document.createElement("figure");
  card.className = "photo-card";

  if (photo.src) {
    const image = document.createElement("img");
    image.className = "photo-holder";
    image.src = photo.src;
    image.alt = photo.caption || "";
    card.append(image);
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
