// Somente navegação responsiva; nenhuma regra de venda é executada no navegador.
const toggle = document.getElementById("menu-toggle");
const sidebar = document.getElementById("sidebar");
if (toggle && sidebar) {
  const closeMenu = () => {
    document.body.classList.remove("menu-open");
    toggle.setAttribute("aria-expanded", "false");
  };
  toggle.addEventListener("click", () => {
    const open = document.body.classList.toggle("menu-open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && document.body.classList.contains("menu-open")) {
      closeMenu();
      toggle.focus();
    }
  });
  document.addEventListener("click", event => {
    if (!sidebar.contains(event.target) && !toggle.contains(event.target)) closeMenu();
  });
}
