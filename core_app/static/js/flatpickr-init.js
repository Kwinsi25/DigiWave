// flatpickr-init.js
function formatDate(dateStr) {
    if (!dateStr) return "-"; // show dash if null
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-GB", {  // "01 Sep 2025"
        day: "2-digit",
        month: "short",
        year: "numeric"
    });
}
            
document.addEventListener("DOMContentLoaded", function () {
    flatpickr(".flat-date", {
        dateFormat: "Y-m-d",
        allowInput: true,
        altInput: true,
        altFormat: "F j, Y",
        monthSelectorType: "dropdown",   // ✅ Month dropdown
        onReady: function(selectedDates, dateStr, instance) {
            const yearSelect = document.createElement("select");
            yearSelect.classList.add("flatpickr-year-dropdown");

            // Dynamic range: currentYear - 50 → currentYear + 20
            const currentYear = new Date().getFullYear();
            const minYear = currentYear - 50;
            const maxYear = currentYear + 20;

            for (let y = minYear; y <= maxYear; y++) {
                let opt = document.createElement("option");
                opt.value = y;
                opt.textContent = y;
                if (y === instance.currentYear) opt.selected = true;
                yearSelect.appendChild(opt);
            }

            // Replace year input with dropdown
            const yearInput = instance.currentYearElement;
            yearInput.parentNode.replaceChild(yearSelect, yearInput);

            // Remove ↑ ↓ buttons
            if (instance.yearElements) {
                instance.yearElements.forEach(el => el.style.display = "none");
            }
            const container = yearSelect.parentNode;
            const upBtn = container.querySelector(".arrowUp");
            const downBtn = container.querySelector(".arrowDown");
            if (upBtn) upBtn.remove();
            if (downBtn) downBtn.remove();

            // Update Flatpickr when year changes
            yearSelect.addEventListener("change", function () {
                instance.changeYear(parseInt(this.value));
            });
        }
    });
});
