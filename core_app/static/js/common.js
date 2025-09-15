// Records per page
document.addEventListener("DOMContentLoaded", function () {
  const recordsPerPage = document.getElementById('recordsPerPage');
  if (recordsPerPage) {
    recordsPerPage.addEventListener('change', function () {
      const form = document.getElementById('recordsForm');
      if (!form) return;
      const hiddenPage = document.createElement('input');
      hiddenPage.type = 'hidden';
      hiddenPage.name = 'page';
      hiddenPage.value = 1;
      form.appendChild(hiddenPage);
      form.submit();
    });
  }
});

// Toast function
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container") || (() => {
    const div = document.createElement("div");
    div.id = "toast-container";
    div.style.position = "fixed";
    div.style.top = "20px";
    div.style.right = "20px";
    div.style.zIndex = "3000";
    div.style.display = "flex";
    div.style.flexDirection = "column";
    div.style.gap = "10px";
    document.body.appendChild(div);
    return div;
  })();

  const toast = document.createElement("div");
  toast.className = `toast align-items-center text-white bg-${type} border-0 show`;
  toast.style.minWidth = "250px";
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 500);
  }, 3000);
}

// Auto-hide existing toasts
document.addEventListener("DOMContentLoaded", function () {
  const toasts = document.querySelectorAll('#toast-container .toast');
  toasts.forEach(function (toast) {
    setTimeout(() => {
      toast.style.transition = "opacity 0.5s ease, transform 0.5s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      setTimeout(() => toast.remove(), 500);
    }, 3000);
  });
});


