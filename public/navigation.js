(() => {
  const $ = (id) => document.getElementById(id);
const themeToggle = $("themeToggle");
let savedTheme;
try {
  savedTheme = localStorage.getItem("c02-theme");
} catch {
  // The browser may block local storage; the toggle still works for this page.
}
function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const dark = theme === "dark";
  themeToggle.textContent = dark
    ? "Switch to light mode"
    : "Switch to dark mode";
  themeToggle.setAttribute("aria-pressed", String(dark));
}
setTheme(savedTheme === "dark" || savedTheme === "light" ? savedTheme : "light");
themeToggle.addEventListener("click", () => {
  const theme =
    document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  setTheme(theme);
  try {
    localStorage.setItem("c02-theme", theme);
  } catch {}
});
function highlightSection() {
  const selected = location.pathname === "/guide.html"
    ? "/guide.html" + (location.hash || "#learning")
    : location.pathname === "/architecture.html" ? "/architecture.html" : "/#comparison-lab";
  for (const link of document.querySelectorAll('.student-nav a')) {
    if (link.getAttribute('href') === selected) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
}
highlightSection();
window.addEventListener('hashchange', highlightSection);
})();
