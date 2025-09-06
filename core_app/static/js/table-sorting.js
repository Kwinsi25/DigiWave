function enableTableSorting(tableId) {
  const table = document.getElementById(tableId);
  if (!table) return;

  table.querySelectorAll("th[data-sort]").forEach((header, index) => {
    header.style.cursor = "pointer";
    let asc = true; // toggle sort direction

    header.addEventListener("click", () => {
      const tbody = table.querySelector("tbody");
      const rows = Array.from(tbody.querySelectorAll("tr"));

      rows.sort((a, b) => {
        let aText = a.children[index].innerText.trim();
        let bText = b.children[index].innerText.trim();

        // detect type
        switch (header.getAttribute("data-sort")) {
          case "number":
            aText = parseFloat(aText) || 0;
            bText = parseFloat(bText) || 0;
            break;
          case "date":
            aText = new Date(aText);
            bText = new Date(bText);
            break;
          default:
            aText = aText.toLowerCase();
            bText = bText.toLowerCase();
        }

        if (aText > bText) return asc ? 1 : -1;
        if (aText < bText) return asc ? -1 : 1;
        return 0;
      });

      // append sorted rows back
      rows.forEach(row => tbody.appendChild(row));

      // toggle direction
      asc = !asc;

      // add indicator
      table.querySelectorAll("th").forEach(th => th.classList.remove("sorted-asc", "sorted-desc"));
      header.classList.add(asc ? "sorted-asc" : "sorted-desc");
    });
  });
}
