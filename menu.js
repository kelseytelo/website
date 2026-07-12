const menuToggles = document.querySelectorAll(".menu-toggle");

for (const toggle of menuToggles) {
  const group = toggle.closest(".menu-group");
  const currentItem = group.querySelector('[aria-current="page"]');

  if (currentItem) {
    group.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
  }

  toggle.addEventListener("click", () => {
    const isOpen = group.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
}
