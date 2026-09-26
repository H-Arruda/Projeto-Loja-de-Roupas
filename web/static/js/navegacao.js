// Somente experiência de navegação. Regras e valores da venda permanecem no servidor.
const toggle = document.getElementById("menu-toggle");
const sidebar = document.getElementById("sidebar");
const backdrop = document.querySelector(".menu-backdrop");
if (toggle && sidebar && backdrop) {
  const closeMenu = (returnFocus = false) => {
    document.body.classList.remove("menu-open");
    toggle.setAttribute("aria-expanded", "false");
    backdrop.hidden = true;
    if (returnFocus) toggle.focus();
  };
  toggle.addEventListener("click", () => {
    const open = document.body.classList.toggle("menu-open");
    toggle.setAttribute("aria-expanded", String(open));
    backdrop.hidden = !open;
    if (open) sidebar.querySelector("nav a")?.focus();
  });
  backdrop.addEventListener("click", () => closeMenu(true));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && document.body.classList.contains("menu-open")) closeMenu(true);
  });
  sidebar.addEventListener("click", event => {
    if (event.target.closest("a")) closeMenu();
  });
  window.matchMedia("(min-width: 1051px)").addEventListener("change", () => closeMenu());
}
