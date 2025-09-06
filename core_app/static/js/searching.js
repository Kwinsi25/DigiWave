function enableTableSearch(inputId, tableId) {
  const searchBox = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!searchBox || !table) return;

  searchBox.addEventListener("keyup", function () {
    let query = this.value.toLowerCase();
    let rows = table.querySelectorAll("tbody tr");

    rows.forEach(row => {
      let text = row.innerText.toLowerCase();

      if (query && text.includes(query)) {
        row.style.display = "";

        // highlight all td except last column
        let cells = row.querySelectorAll("td");
        cells.forEach((td, index) => {
          if (index === cells.length - 1) return; // skip last column

          let original = td.getAttribute("data-original") || td.innerText;
          td.setAttribute("data-original", original); // safe copy
          let regex = new RegExp(`(${query})`, "gi");
          td.innerHTML = original.replace(regex, "<mark>$1</mark>");
        });

      } else if (!query) {
        // reset everything
        row.style.display = "";
        let cells = row.querySelectorAll("td");
        cells.forEach((td, index) => {
          if (index === cells.length - 1) return;
          let original = td.getAttribute("data-original") || td.innerText;
          td.innerHTML = original;
          location.reload()
        });
      } else {
        row.style.display = "none";
      }
    });
  });
}
