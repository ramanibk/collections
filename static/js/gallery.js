(() => {
  const triggers = document.querySelectorAll("[data-photo-dialog]");

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const dialog = document.querySelector(`#photo-${trigger.dataset.photoDialog}`);
      if (dialog instanceof HTMLDialogElement) dialog.showModal();
    });
  });

  document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => button.closest("dialog")?.close());
  });

  document.querySelectorAll("dialog").forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  });
})();
