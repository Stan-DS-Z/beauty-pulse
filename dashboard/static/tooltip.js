// KPI tooltips: any element with data-tooltip shows its full text on hover.
// One listener set on the document, so cards that arrive with a page swap
// need nothing of their own.
(function () {
  var tip = null;
  function ensure() {
    if (!tip) {
      tip = document.createElement("div");
      tip.id = "_kpi_tip";
      document.body.appendChild(tip);
    }
    return tip;
  }
  document.addEventListener("mouseover", function (e) {
    var el = e.target.closest && e.target.closest("[data-tooltip]");
    if (el) {
      var t = ensure();
      t.textContent = el.getAttribute("data-tooltip");
      t.style.display = "block";
    }
  });
  document.addEventListener("mouseout", function (e) {
    var el = e.target.closest && e.target.closest("[data-tooltip]");
    if (el && tip) tip.style.display = "none";
  });
  document.addEventListener("mousemove", function (e) {
    if (tip && tip.style.display === "block") {
      tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 300) + "px";
      tip.style.top = (e.clientY - 42) + "px";
    }
  });
})();
