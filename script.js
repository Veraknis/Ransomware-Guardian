// Progressive Web App frontend (vanilla JS)
// - Fetches ./output.json (produced by your Python script)
// - Search, sector filter, chips
// - Pagination, mobile-first card UI
// - Offline caching via service worker (network-first for output.json)
// - Export CSV & copy per-card

const DATA_URL = "./output.json";
const PAGE_SIZE = 18;
let raw = [];
let filtered = [];
let page = 1;

// DOM
const searchEl = document.getElementById("search");
const sectorSelect = document.getElementById("sectorSelect");
const chipsEl = document.getElementById("chips");
const grid = document.getElementById("grid");
const countEl = document.getElementById("count");
const lastUpdatedEl = document.getElementById("lastUpdated");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");
const pageInfo = document.getElementById("pageInfo");
const emptyEl = document.getElementById("empty");
const exportBtn = document.getElementById("exportBtn");
const refreshBtn = document.getElementById("refreshBtn");
const clearBtn = document.getElementById("clearBtn");

// Template
const cardTpl = document.getElementById("cardTpl");

// Helpers
const isoToNice = (iso) => {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleString();
};
const excerpt = (s, n = 160) =>
  s ? (s.length > n ? s.slice(0, n).trim() + "…" : s) : "";
const escapeHtml = (s) =>
  String(s || "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[
        c
      ])
  );

// Load data: network-first for output.json; if network fails SW/caches will be used
async function loadData() {
  try {
    const res = await fetch(DATA_URL, { cache: "no-store" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    raw = normalize(data);
    setupFilters();
    runFilter();
    lastUpdatedEl.textContent = raw.length ? `records: ${raw.length}` : "";
  } catch (err) {
    console.error("Initial fetch failed, trying fallback...", err);
    try {
      const res2 = await fetch(DATA_URL); // allow SW or browser cache to serve
      const data2 = await res2.json();
      raw = normalize(data2);
      setupFilters();
      runFilter();
    } catch (e) {
      grid.innerHTML = `<div class="empty muted">Unable to load data — ensure output.json is present in the site root.</div>`;
    }
  }
}

function normalize(data) {
  const arr = Array.isArray(data) ? data : data.records || [];
  return arr.map((r) => ({
    discovered:
      r.discovered || r.post_date || r.date || r.posted || r.created || "",
    title: r.post_title || r.title || r.name || "",
    group: r.group || r.ransom_group || r.actor || r.group_name || "",
    sector: (r.sector || r.industry || "Unknown").trim() || "Unknown",
    description: r.description || r.desc || r.summary || "",
  }));
}

function setupFilters() {
  const sectors = [...new Set(raw.map((r) => r.sector).filter(Boolean))].sort();
  sectorSelect.innerHTML =
    '<option value="">All sectors</option>' +
    sectors
      .map((s) => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`)
      .join("");
  chipsEl.innerHTML = sectors
    .slice(0, 12)
    .map(
      (s) =>
        `<button class="chip" data-s="${escapeHtml(s)}">${escapeHtml(
          s
        )}</button>`
    )
    .join("");
  countEl.textContent = raw.length;
  chipsEl.querySelectorAll(".chip").forEach((b) =>
    b.addEventListener("click", () => {
      sectorSelect.value = b.dataset.s;
      runFilter();
    })
  );
}

function runFilter() {
  const q = (searchEl.value || "").trim().toLowerCase();
  const sector = (sectorSelect.value || "").trim().toLowerCase();
  filtered = raw.filter((r) => {
    const text =
      `${r.title} ${r.group} ${r.description} ${r.sector}`.toLowerCase();
    const okQ = !q || text.includes(q);
    const okS = !sector || r.sector.toLowerCase() === sector;
    return okQ && okS;
  });
  page = 1;
  render();
}

function render() {
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  if (page > totalPages) page = totalPages;
  const start = (page - 1) * PAGE_SIZE;
  const pageItems = filtered.slice(start, start + PAGE_SIZE);
  grid.innerHTML = "";
  if (!pageItems.length) {
    emptyEl.hidden = false;
  } else {
    emptyEl.hidden = true;
  }

  for (const it of pageItems) {
    const el = cardTpl.content.cloneNode(true);
    el.querySelector(".title").textContent = it.title || "(no title)";
    el.querySelector(".sector").textContent = it.sector;
    el.querySelector(".meta").textContent = it.discovered
      ? isoToNice(it.discovered)
      : "";
    el.querySelector(".desc").textContent = excerpt(it.description, 200);
    el.querySelector(".group").textContent = it.group;
    const copyBtn = el.querySelector(".copy");
    copyBtn.addEventListener("click", () => {
      copyToClipboard(
        `${it.title} — ${it.group}\n${it.sector}\n\n${it.description}`
      );
    });
    grid.appendChild(el);
  }

  pageInfo.textContent = `${page} / ${totalPages}`;
  prevBtn.disabled = page <= 1;
  nextBtn.disabled = page >= totalPages;
}

prevBtn.addEventListener("click", () => {
  if (page > 1) {
    page--;
    render();
  }
});
nextBtn.addEventListener("click", () => {
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  if (page < totalPages) {
    page++;
    render();
  }
});

searchEl.addEventListener("input", debounce(runFilter, 220));
sectorSelect.addEventListener("change", () => runFilter());
refreshBtn.addEventListener("click", () => {
  loadData();
});
clearBtn.addEventListener("click", () => {
  searchEl.value = "";
  sectorSelect.value = "";
  runFilter();
});

exportBtn.addEventListener("click", () => {
  const csv = toCSV(filtered);
  downloadBlob(csv, "ransomware_guardian_export.csv", "text/csv");
});

function toCSV(arr) {
  const cols = ["discovered", "title", "group", "sector", "description"];
  const lines = [cols.join(",")];
  for (const r of arr) {
    const row = cols.map((c) => `"${String(r[c] || "").replace(/"/g, '""')}"`);
    lines.push(row.join(","));
  }
  return lines.join("\n");
}

function downloadBlob(data, name, type) {
  const blob = new Blob([data], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function copyToClipboard(text) {
  navigator.clipboard
    ?.writeText(text)
    .then(() => {
      alert("Copied to clipboard");
    })
    .catch(() => {
      alert("Copy failed");
    });
}

function debounce(fn, wait = 200) {
  let t;
  return (...a) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...a), wait);
  };
}

// register service worker (will activate on HTTPS hosts like GitHub Pages)
if ("serviceWorker" in navigator) {
  navigator.serviceWorker
    .register("sw.js")
    .then(() => console.log("SW registered"))
    .catch((e) => console.warn("SW reg failed", e));
}

// initial boot
loadData();
