(() => {
  const list = document.querySelector("#all-posts-list");
  const buttons = [...document.querySelectorAll("[data-sort]")];
  if (!list || buttons.length === 0) return;

  const rows = [...list.children];
  const compareText = (left, right) =>
    left.localeCompare(right, undefined, { numeric: true, sensitivity: "base" });

  const sortRows = (mode) => {
    rows.sort((left, right) => {
      if (mode === "title") {
        return compareText(left.dataset.title, right.dataset.title) ||
          right.dataset.date.localeCompare(left.dataset.date) ||
          compareText(left.dataset.id, right.dataset.id);
      }
      return right.dataset.date.localeCompare(left.dataset.date) ||
        compareText(left.dataset.title, right.dataset.title) ||
        compareText(left.dataset.id, right.dataset.id);
    });
    list.append(...rows);
    buttons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.sort === mode));
    });
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => sortRows(button.dataset.sort));
  });
})();
