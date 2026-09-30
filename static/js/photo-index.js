(() => {
  const form = document.querySelector("[data-index-filters]");
  const body = document.querySelector("[data-index-rows]");
  const status = document.querySelector("[data-filter-status]");
  const summary = document.querySelector("[data-tag-summary]");
  if (!form || !body || !status || !summary) return;

  const rows = [...body.querySelectorAll("tr")];
  const checkboxes = [...form.querySelectorAll('input[name="tags"]')];

  const applyFilter = () => {
    const selected = checkboxes.filter((input) => input.checked).map((input) => input.value);
    let visible = 0;

    rows.forEach((row) => {
      const tags = new Set(JSON.parse(row.dataset.tags || "[]"));
      // Multiple selections deliberately narrow results instead of broadening them.
      const show = selected.length > 0 && selected.every((tag) => tags.has(tag));
      row.hidden = !show;
      if (show) visible += 1;
    });

    if (selected.length === 0) {
      summary.textContent = "Select tags";
      status.textContent = "Select one or more tags to view the archive.";
      return;
    }

    summary.textContent = `${selected.length} tag${selected.length === 1 ? "" : "s"} selected`;
    status.textContent = `${visible} record${visible === 1 ? "" : "s"}`;
  };

  form.addEventListener("change", applyFilter);
  form.addEventListener("reset", () => requestAnimationFrame(applyFilter));
  applyFilter();
})();
