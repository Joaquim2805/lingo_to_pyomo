/* ==========================================================
   LingPy — Application JavaScript
   ========================================================== */

/* ---------- Utilities ---------- */
function escapeHtml(t) {
  const d = document.createElement("div");
  d.textContent = t;
  return d.innerHTML;
}

/* ---------- Toast ---------- */
const Toast = {
  _container: null,
  _get() {
    if (!this._container)
      this._container = document.getElementById("toastContainer");
    return this._container;
  },
  show(title, message, type = "info") {
    const c = this._get();
    if (!c) return;
    const icons = {
      success: "circle-check",
      error: "circle-xmark",
      info: "circle-info",
      warning: "triangle-exclamation",
    };
    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    el.innerHTML = `<i class="fas fa-${icons[type] || icons.info}"></i><div><strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span></div><button class="toast-close" aria-label="Fermer"><i class="fas fa-xmark"></i></button>`;
    el.querySelector(".toast-close").addEventListener("click", () =>
      el.remove(),
    );
    c.appendChild(el);
    requestAnimationFrame(() => el.classList.add("show"));
    setTimeout(() => {
      el.classList.remove("show");
      setTimeout(() => el.remove(), 300);
    }, 5000);
  },
  success(t, m) {
    this.show(t, m, "success");
  },
  error(t, m) {
    this.show(t, m, "error");
  },
};

/* ---------- Modal ---------- */
const Modal = {
  open(id) {
    const m = document.getElementById(id);
    if (!m) return;
    m.classList.add("open");
    m.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  },
  close(id) {
    const m = document.getElementById(id);
    if (!m) return;
    m.classList.remove("open");
    m.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  },
  closeAll() {
    document.querySelectorAll(".modal-backdrop.open").forEach((m) => {
      m.classList.remove("open");
      m.setAttribute("aria-hidden", "true");
    });
    document.body.style.overflow = "";
  },
};

/* ---------- Tabs ---------- */
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      btn
        .closest(".tab-bar")
        .querySelectorAll(".tab-btn")
        .forEach((b) => b.classList.toggle("active", b === btn));
      document
        .querySelectorAll(".tab-pane")
        .forEach((p) => p.classList.toggle("active", p.dataset.pane === tab));
    });
  });
}

/* ---------- Source toggle (dataset / upload) ---------- */
function initSourceToggles() {
  document.querySelectorAll(".source-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      const group = btn.dataset.group;
      const source = btn.dataset.source;
      document
        .querySelectorAll(`.source-tab[data-group="${group}"]`)
        .forEach((b) => b.classList.toggle("active", b === btn));
      document
        .querySelectorAll(`.source-panel[data-group="${group}"]`)
        .forEach((p) =>
          p.classList.toggle("active", p.dataset.source === source),
        );
    });
  });
}

/* ---------- Upload zones ---------- */
function initUploadZones() {
  document
    .querySelectorAll(".upload-zone:not(.upload-zone-batch)")
    .forEach((zone) => {
      const input = zone.querySelector("input[type=file]");
      if (!input) return;
      const infoEl = zone.querySelector(".upload-file-info");
      const nameEl = zone.querySelector("[id$='FileName']");

      /* Derive accepted extensions from the input's accept attribute */
      const acceptAttr = (input.getAttribute("accept") || ".lng").toLowerCase();
      const acceptedExts = acceptAttr.split(",").map((s) => s.trim());

      zone.addEventListener("click", (e) => {
        if (!e.target.closest(".remove-file")) input.click();
      });
      zone.addEventListener("dragover", (e) => {
        e.preventDefault();
        zone.classList.add("drag-over");
      });
      zone.addEventListener("dragleave", () =>
        zone.classList.remove("drag-over"),
      );
      zone.addEventListener("drop", (e) => {
        e.preventDefault();
        zone.classList.remove("drag-over");
        if (e.dataTransfer.files.length) {
          const file = e.dataTransfer.files[0];
          const ext = file.name
            .substring(file.name.lastIndexOf("."))
            .toLowerCase();
          if (!acceptedExts.includes(ext)) {
            Toast.error(
              "Format invalide",
              `Seuls les fichiers ${acceptedExts.join(", ")} sont acceptés.`,
            );
            return;
          }
          const dt = new DataTransfer();
          dt.items.add(file);
          input.files = dt.files;
          showFileInfo(file);
        }
      });
      input.addEventListener("change", () => {
        if (input.files.length) showFileInfo(input.files[0]);
      });

      function showFileInfo(file) {
        if (infoEl && nameEl) {
          nameEl.textContent = file.name;
          infoEl.classList.remove("hidden");
          zone
            .querySelectorAll(
              ".upload-zone-icon, .upload-zone-text, .upload-zone-hint",
            )
            .forEach((el) => el.classList.add("hidden"));
        }
      }
    });

  /* Remove-file buttons */
  document.querySelectorAll(".remove-file").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const inputId = btn.dataset.clear;
      const input = document.getElementById(inputId);
      if (input) {
        input.value = "";
      }
      const zone = btn.closest(".upload-zone");
      if (zone) {
        zone.querySelector(".upload-file-info")?.classList.add("hidden");
        zone
          .querySelectorAll(
            ".upload-zone-icon, .upload-zone-text, .upload-zone-hint",
          )
          .forEach((el) => el.classList.remove("hidden"));
      }
    });
  });
}

/* ---------- Navbar ---------- */
function initNavbar() {
  const toggle = document.getElementById("navToggle");
  const links = document.getElementById("navMenu");
  if (toggle && links) {
    toggle.addEventListener("click", () => {
      links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", links.classList.contains("open"));
    });
  }
}

/* ---------- Modal close buttons ---------- */
function initModalCloseButtons() {
  document.querySelectorAll("[data-close]").forEach((btn) => {
    btn.addEventListener("click", () => Modal.close(btn.dataset.close));
  });
  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) Modal.close(backdrop.id);
    });
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") Modal.closeAll();
  });
}

/* ---------- Smooth scroll ---------- */
function initSmoothScroll() {
  document.querySelectorAll("a[data-scroll]").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      const target = document.querySelector(a.getAttribute("href"));
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

/* ---------- API helpers ---------- */

/**
 * Build a FormData from a form, excluding inputs inside inactive source panels.
 * This prevents sending both a dataset selection AND a file upload simultaneously.
 */
function buildFormData(form) {
  // Temporarily disable inputs inside inactive source panels
  const disabled = [];
  form
    .querySelectorAll(
      ".source-panel:not(.active) select, .source-panel:not(.active) input",
    )
    .forEach((el) => {
      if (!el.disabled) {
        el.disabled = true;
        disabled.push(el);
      }
    });
  const fd = new FormData(form);
  // Re-enable
  disabled.forEach((el) => (el.disabled = false));
  return fd;
}

async function apiPost(url, formData) {
  const res = await fetch(url, { method: "POST", body: formData });
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json"))
    return { ok: res.ok, data: await res.json() };
  return {
    ok: res.ok,
    data: null,
    blob: await res.blob(),
    filename: extractFilename(res),
  };
}

async function apiDownload(url, formData) {
  const res = await fetch(url, {
    method: "POST",
    body: formData || new FormData(),
  });
  if (!res.ok) {
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const d = await res.json();
      throw new Error(d.error || "Erreur");
    }
    throw new Error("Erreur de téléchargement");
  }
  const blob = await res.blob();
  const fn = extractFilename(res) || "download";
  triggerDownload(blob, fn);
}

function extractFilename(res) {
  const cd = res.headers.get("content-disposition");
  if (!cd) return null;
  const m = cd.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/i);
  return m ? decodeURIComponent(m[1].replace(/"/g, "")) : null;
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
}

/* ---------- Button loading state ---------- */
function setLoading(btn, loading) {
  if (!btn) return;
  if (loading) {
    btn.dataset.originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Traitement…';
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.originalHtml || btn.innerHTML;
    btn.disabled = false;
  }
}

/* ---------- OLE detection on all file selects ---------- */
function initOleDetection() {
  let oleFiles = [];
  try {
    const el = document.getElementById("ole-files-data");
    if (el) oleFiles = JSON.parse(el.textContent);
  } catch (e) {
    /* ignore */
  }
  if (
    !oleFiles.length &&
    !document.querySelectorAll(".ole-detect-select").length
  )
    return;

  document.querySelectorAll(".ole-detect-select").forEach((select) => {
    const pill =
      select.closest(".form-group")?.querySelector("[data-ole-pill]") ||
      select.parentElement.querySelector("[data-ole-pill]");
    if (!pill) return;

    function updatePill() {
      const val = select.value;
      if (!val) {
        pill.textContent = "";
        pill.className = "status-pill";
        pill.style.display = "none";
        return;
      }
      if (oleFiles.includes(val)) {
        pill.innerHTML =
          '<i class="fas fa-file-excel" style="font-size:0.85em"></i> Contient @OLE \u2014 un fichier Excel est li\u00e9 \u00e0 ce mod\u00e8le';
        pill.className = "status-pill status-pill-warning";
      } else {
        pill.innerHTML =
          '<i class="fas fa-check-circle" style="font-size:0.85em"></i> Pas de d\u00e9pendance Excel d\u00e9tect\u00e9e';
        pill.className = "status-pill status-pill-ok";
      }
    }

    select.addEventListener("change", updatePill);
    /* run once if a value is already selected */
    if (select.value) updatePill();
  });
}

/* ============================================================
   PAGE: Home (quick start)
   ============================================================ */
function initHomePage() {
  const uploadForm = document.getElementById("quickUploadForm");
  const datasetForm = document.getElementById("quickDatasetForm");

  function handleQuickForm(form) {
    if (!form) return;
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = form.querySelector("button[type=submit]");
      setLoading(btn, true);
      try {
        const fd = buildFormData(form);
        const { ok, data } = await apiPost("/tools/generate", fd);
        if (ok && data && data.success) {
          window._currentJob = data;
          showPreview(data);
          Toast.success("Conversion réussie", "L'aperçu est disponible.");
        } else {
          showError(data);
        }
      } catch (err) {
        Toast.error("Erreur réseau", err.message);
      } finally {
        setLoading(btn, false);
      }
    });
  }

  handleQuickForm(uploadForm);
  handleQuickForm(datasetForm);
}

/* ============================================================
   PAGE: Tools
   ============================================================ */
let _currentJob = null;

function initToolsPage() {
  /* --- Generate --- */
  const genForm = document.getElementById("generateForm");
  if (genForm) {
    genForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("generateBtn");
      setLoading(btn, true);
      try {
        const fd = buildFormData(genForm);
        const { ok, data } = await apiPost("/tools/generate", fd);
        if (ok && data && data.success) {
          _currentJob = data;
          showPreview(data);
          Toast.success(
            "Conversion réussie",
            `Fichier ${data.file_name} converti.`,
          );
        } else {
          showError(data);
        }
      } catch (err) {
        Toast.error("Erreur", err.message);
      } finally {
        setLoading(btn, false);
      }
    });
  }

  /* --- Clean --- */
  const cleanForm = document.getElementById("cleanForm");
  if (cleanForm) {
    cleanForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("cleanBtn");
      setLoading(btn, true);
      try {
        const fd = buildFormData(cleanForm);
        const { ok, data } = await apiPost("/tools/clean", fd);
        if (ok && data && data.success) {
          _currentJob = data;
          showCleanPreview(data);
          Toast.success(
            "Nettoyage terminé",
            `Fichier ${data.file_name} généré.`,
          );
        } else {
          showError(data);
        }
      } catch (err) {
        Toast.error("Erreur", err.message);
      } finally {
        setLoading(btn, false);
      }
    });
  }

  /* --- OLE --- */
  const oleForm = document.getElementById("oleForm");
  if (oleForm) {
    oleForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("convertOleBtn");
      setLoading(btn, true);
      try {
        const fd = buildFormData(oleForm);
        const { ok, data } = await apiPost("/tools/convert-ole", fd);
        if (ok && data && data.success) {
          _currentJob = data;
          showOlePreview(data);
          Toast.success(
            "Conversion OLE terminée",
            `Fichier ${data.file_name} généré.`,
          );
        } else {
          showError(data);
        }
      } catch (err) {
        Toast.error("Erreur", err.message);
      } finally {
        setLoading(btn, false);
      }
    });
  }

  /* --- Pipeline --- */
  const pipelineForm = document.getElementById("pipelineForm");
  if (pipelineForm) {
    pipelineForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("pipelineBtn");
      setLoading(btn, true);
      try {
        const fd = buildFormData(pipelineForm);
        /* Send checkbox values as "true"/"false" strings */
        fd.set(
          "do_clean",
          document.getElementById("do_clean")?.checked ? "true" : "false",
        );
        fd.set(
          "external_data",
          document.getElementById("external_data")?.checked ? "true" : "false",
        );
        const { ok, data } = await apiPost("/tools/pipeline", fd);
        if (ok && data && data.success) {
          _currentJob = data;
          showPipelineResult(data);
          Toast.success(
            "Pipeline terminé",
            "Tous les artefacts ont été générés.",
          );
        } else {
          showError(data);
        }
      } catch (err) {
        Toast.error("Erreur", err.message);
      } finally {
        setLoading(btn, false);
      }
    });
  }

  initOleDetection();
  initDownloadButtons();
  initViewToggle();
}

/* --- Preview modal (generate + quick-start) --- */
function showPreview(data) {
  const code = document.getElementById("previewCode");
  const leftCode = document.getElementById("leftCode");
  const rightCode = document.getElementById("rightCode");
  const meta = document.getElementById("previewMeta");
  const compareLink = document.getElementById("previewCompareLink");

  if (code) {
    code.textContent = data.pyomo_code || "";
    hljs.highlightElement(code);
  }
  if (leftCode) {
    leftCode.textContent = data.lingo_original || "";
  }
  if (rightCode) {
    rightCode.textContent = data.pyomo_code || "";
    hljs.highlightElement(rightCode);
  }
  if (meta) {
    meta.innerHTML = `<span class="badge badge-primary">${escapeHtml(data.file_name || "")}</span> <span class="badge badge-accent">${escapeHtml(data.solver || "")}</span>`;
  }
  if (compareLink && data.job_id) {
    compareLink.href = `/compare/${data.job_id}`;
    compareLink.classList.remove("hidden");
  }

  Modal.open("previewModal");
}

/* --- Clean preview (reuse preview modal) --- */
function showCleanPreview(data) {
  const code = document.getElementById("previewCode");
  const leftCode = document.getElementById("leftCode");
  const rightCode = document.getElementById("rightCode");
  const meta = document.getElementById("previewMeta");
  const leftTitle = document.getElementById("leftTitle");
  const rightTitle = document.getElementById("rightTitle");

  if (code) {
    code.textContent = data.content_preview || "";
  }
  if (leftCode) {
    leftCode.textContent = data.original_content || "";
  }
  if (rightCode) {
    rightCode.textContent = data.content_preview || "";
  }
  if (leftTitle) leftTitle.textContent = "Original";
  if (rightTitle) rightTitle.textContent = "Nettoyé";
  if (meta) {
    meta.innerHTML = `<span class="badge badge-primary">${escapeHtml(data.file_name || "")}</span> <span class="text-muted">${data.original_size} → ${data.cleaned_size} caractères</span>`;
  }

  Modal.open("previewModal");
}

/* --- OLE preview (reuse preview modal) --- */
function showOlePreview(data) {
  const code = document.getElementById("previewCode");
  const leftCode = document.getElementById("leftCode");
  const rightCode = document.getElementById("rightCode");
  const leftTitle = document.getElementById("leftTitle");
  const rightTitle = document.getElementById("rightTitle");
  const meta = document.getElementById("previewMeta");

  if (code) {
    code.textContent = data.content_preview || "";
  }
  if (leftCode) {
    leftCode.textContent = data.original_content || "";
  }
  if (rightCode) {
    rightCode.textContent = data.content_preview || "";
  }
  if (leftTitle) leftTitle.textContent = "Avec @OLE";
  if (rightTitle) rightTitle.textContent = "Explicite";
  if (meta) {
    meta.innerHTML = `<span class="badge badge-primary">${escapeHtml(data.file_name || "")}</span>`;
  }

  Modal.open("previewModal");
}

/* --- Pipeline result modal --- */
function showPipelineResult(data) {
  const stepsEl = document.getElementById("pipelineSteps");
  const tagsEl = document.getElementById("pipelineTags");
  const codeEl = document.getElementById("pipelinePreviewCode");
  const dlNb = document.getElementById("downloadPipelineNotebookBtn");
  const dlData = document.getElementById("downloadPipelineDataBtn");

  if (stepsEl && data.pipeline_steps) {
    stepsEl.innerHTML = data.pipeline_steps
      .map((s) => `<li>${escapeHtml(s)}</li>`)
      .join("");
  }

  if (tagsEl) {
    let tags = `<span class="badge badge-primary">${escapeHtml(data.notebook_filename || "")}</span>`;
    if (data.data_filename) {
      tags += ` <span class="badge badge-accent">${escapeHtml(data.data_filename)}</span>`;
    }
    tagsEl.innerHTML = tags;
  }

  if (codeEl) {
    codeEl.textContent = data.pyomo_code_preview || "";
    hljs.highlightElement(codeEl);
  }

  if (dlData) {
    if (data.data_filename) dlData.classList.remove("hidden");
    else dlData.classList.add("hidden");
  }

  Modal.open("pipelineModal");
}

/* --- Error modal --- */
function showError(data) {
  const msg = document.getElementById("errorMessage");
  const det = document.getElementById("errorDetails");
  if (msg)
    msg.textContent =
      (data && data.error) || "Une erreur inconnue s'est produite.";
  if (det && data && data.traceback) {
    det.classList.remove("hidden");
    det.innerHTML = `<pre class="error-traceback">${escapeHtml(data.traceback)}</pre>`;
  } else if (det) {
    det.classList.add("hidden");
  }
  Modal.open("errorModal");
}

/* --- View toggle (single / compare) --- */
function initViewToggle() {
  const singleBtn = document.getElementById("singleViewBtn");
  const compareBtn = document.getElementById("compareViewBtn");
  const singleView = document.querySelector(".preview-single");
  const compareView = document.querySelector(".preview-compare");
  if (!singleBtn || !compareBtn) return;

  singleBtn.addEventListener("click", () => {
    singleBtn.classList.add("active");
    compareBtn.classList.remove("active");
    singleView?.classList.remove("hidden");
    compareView?.classList.add("hidden");
  });
  compareBtn.addEventListener("click", () => {
    compareBtn.classList.add("active");
    singleBtn.classList.remove("active");
    compareView?.classList.remove("hidden");
    singleView?.classList.add("hidden");
  });
}

/* --- Download buttons --- */
function initDownloadButtons() {
  const previewDl = document.getElementById("previewDownloadBtn");
  if (previewDl) {
    previewDl.addEventListener("click", async () => {
      if (!_currentJob || !_currentJob.job_id) return;
      setLoading(previewDl, true);
      try {
        const type = _currentJob.pyomo_code ? "notebook" : "lng";
        await apiDownload(`/api/download/${_currentJob.job_id}/${type}`);
        Toast.success("Téléchargement", "Fichier téléchargé avec succès.");
      } catch (err) {
        Toast.error("Erreur", err.message);
      } finally {
        setLoading(previewDl, false);
      }
    });
  }

  const pipelineNb = document.getElementById("downloadPipelineNotebookBtn");
  if (pipelineNb) {
    pipelineNb.addEventListener("click", async () => {
      if (!_currentJob || !_currentJob.job_id) return;
      setLoading(pipelineNb, true);
      try {
        await apiDownload(`/api/download/${_currentJob.job_id}/notebook`);
        Toast.success("Téléchargement", "Notebook téléchargé.");
      } catch (err) {
        Toast.error("Erreur", err.message);
      } finally {
        setLoading(pipelineNb, false);
      }
    });
  }

  const pipelineData = document.getElementById("downloadPipelineDataBtn");
  if (pipelineData) {
    pipelineData.addEventListener("click", async () => {
      if (!_currentJob || !_currentJob.job_id) return;
      setLoading(pipelineData, true);
      try {
        await apiDownload(`/api/download/${_currentJob.job_id}/data`);
        Toast.success("Téléchargement", "Données téléchargées.");
      } catch (err) {
        Toast.error("Erreur", err.message);
      } finally {
        setLoading(pipelineData, false);
      }
    });
  }
}

/* ============================================================
   PAGE: Batch
   ============================================================ */
function initBatchPage() {
  const form = document.getElementById("batchForm");
  if (!form) return;

  const zone = document.getElementById("batchUploadZone");
  const input = document.getElementById("batchFileInput");
  const fileListEl = document.getElementById("batchFileList");

  /*
   * Managed file store:
   *   _batchFiles = [ { id, lngFile: File, excelFile: File|null, hasOle: bool } ]
   * We read each .lng to detect @OLE so we can show the Excel upload button.
   */
  let _batchFiles = [];
  let _nextId = 1;

  /* --- Helpers --- */
  function fileId() {
    return _nextId++;
  }

  async function detectOle(file) {
    try {
      const text = await file.text();
      return text.includes("@OLE");
    } catch {
      return false;
    }
  }

  async function addFiles(rawFiles) {
    const files = Array.from(rawFiles); /* snapshot – FileList may be cleared */
    const existingNames = new Set(_batchFiles.map((f) => f.lngFile.name));
    for (const f of files) {
      const lower = f.name.toLowerCase();
      if (lower.endsWith(".lng") && !existingNames.has(f.name)) {
        const hasOle = await detectOle(f);
        _batchFiles.push({ id: fileId(), lngFile: f, excelFile: null, hasOle });
        existingNames.add(f.name);
      } else if (lower.endsWith(".xlsx") || lower.endsWith(".xls")) {
        /* Auto-pair Excel: find a .lng entry whose stem matches or that has no Excel yet */
        const stem = f.name.replace(/\.(xlsx|xls)$/i, "").toLowerCase();
        const match = _batchFiles.find(
          (b) =>
            !b.excelFile &&
            b.hasOle &&
            b.lngFile.name
              .replace(/\.lng$/i, "")
              .toLowerCase()
              .includes(stem),
        );
        if (match) {
          match.excelFile = f;
        } else {
          /* No auto-match, attach to first OLE file without Excel */
          const first = _batchFiles.find((b) => b.hasOle && !b.excelFile);
          if (first) first.excelFile = f;
        }
      }
    }
    renderFileList();
  }

  function removeFile(id) {
    _batchFiles = _batchFiles.filter((f) => f.id !== id);
    renderFileList();
  }

  function removeExcel(id) {
    const entry = _batchFiles.find((f) => f.id === id);
    if (entry) entry.excelFile = null;
    renderFileList();
  }

  function renderFileList() {
    if (!fileListEl) return;
    fileListEl.innerHTML = "";

    for (const entry of _batchFiles) {
      const card = document.createElement("div");
      card.className = "batch-file-card";

      /* LNG icon */
      const iconDiv = `<div class="batch-file-icon icon-lng"><i class="fas fa-file-code"></i></div>`;

      /* File info */
      const size = (entry.lngFile.size / 1024).toFixed(1);
      let metaHtml = `${size} Ko`;
      if (entry.hasOle)
        metaHtml += ` <span style="color:var(--warning);font-weight:600">· @OLE</span>`;

      const infoDiv = `<div class="batch-file-info">
        <div class="batch-file-name">${escapeHtml(entry.lngFile.name)}</div>
        <div class="batch-file-meta">${metaHtml}</div>
      </div>`;

      /* Excel button (only for OLE files) */
      let excelHtml = "";
      if (entry.hasOle) {
        if (entry.excelFile) {
          excelHtml = `<button type="button" class="batch-file-excel-link has-excel" data-action="remove-excel" data-id="${entry.id}" title="Retirer ${escapeHtml(entry.excelFile.name)}">
            <i class="fas fa-file-excel"></i> ${escapeHtml(entry.excelFile.name)}
            <i class="fas fa-xmark" style="margin-left:0.15rem;font-size:0.65rem;opacity:0.7"></i>
          </button>`;
        } else {
          excelHtml = `<button type="button" class="batch-file-excel-link" data-action="add-excel" data-id="${entry.id}" title="Associer un fichier Excel">
            <i class="fas fa-file-excel"></i> + Excel
          </button>`;
        }
      }

      /* Remove button */
      const removeBtn = `<button type="button" class="batch-file-remove" data-action="remove" data-id="${entry.id}" title="Retirer"><i class="fas fa-xmark"></i></button>`;

      card.innerHTML = iconDiv + infoDiv + excelHtml + removeBtn;
      fileListEl.appendChild(card);
    }

    /* Bind actions */
    fileListEl.querySelectorAll("[data-action]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const id = parseInt(btn.dataset.id, 10);
        const action = btn.dataset.action;
        if (action === "remove") removeFile(id);
        else if (action === "remove-excel") removeExcel(id);
        else if (action === "add-excel") pickExcel(id);
      });
    });
  }

  function pickExcel(entryId) {
    const tmp = document.createElement("input");
    tmp.type = "file";
    tmp.accept = ".xlsx,.xls";
    tmp.addEventListener("change", () => {
      if (tmp.files.length) {
        const entry = _batchFiles.find((f) => f.id === entryId);
        if (entry) {
          entry.excelFile = tmp.files[0];
          renderFileList();
        }
      }
    });
    tmp.click();
  }

  /* --- Drop zone --- */
  if (zone && input) {
    zone.addEventListener("click", () => input.click());
    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("drag-over");
    });
    zone.addEventListener("dragleave", () =>
      zone.classList.remove("drag-over"),
    );
    zone.addEventListener("drop", (e) => {
      e.preventDefault();
      zone.classList.remove("drag-over");
      addFiles(e.dataTransfer.files);
    });
    input.addEventListener("change", () => {
      if (input.files.length) addFiles(input.files);
      input.value = ""; /* allow re-picking the same files */
    });
  }

  /* --- Submit --- */
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("batchProcessBtn");
    setLoading(btn, true);
    try {
      const fd = new FormData();

      /* Uploaded LNG files */
      for (const entry of _batchFiles) {
        fd.append("files", entry.lngFile);
      }

      /* Excel files: send with indexed keys so backend can pair them */
      for (let i = 0; i < _batchFiles.length; i++) {
        const entry = _batchFiles[i];
        if (entry.excelFile) {
          fd.append("excel_files", entry.excelFile);
          fd.append("excel_for_lng", entry.lngFile.name);
        }
      }

      /* Dataset selection */
      const datasetSelect = document.getElementById("batchDatasetSelect");
      if (datasetSelect) {
        for (const opt of datasetSelect.selectedOptions) {
          fd.append("dataset_files", opt.value);
        }
      }

      fd.set(
        "solver",
        document.getElementById("batchSolver")?.value || "highs",
      );
      fd.set(
        "do_clean",
        document.getElementById("batchDoClean")?.checked ? "true" : "false",
      );
      fd.set(
        "external_data",
        document.getElementById("batchExternalData")?.checked
          ? "true"
          : "false",
      );
      fd.set(
        "external_data_format",
        document.getElementById("batchDataFormat")?.value || "json",
      );

      const { ok, data } = await apiPost("/batch/process", fd);
      if (ok && data && data.success) {
        renderBatchResults(data);
        Toast.success(
          "Traitement terminé",
          `${data.succeeded}/${data.total} fichiers convertis.`,
        );
      } else {
        showError(data);
      }
    } catch (err) {
      Toast.error("Erreur", err.message);
    } finally {
      setLoading(btn, false);
    }
  });
}

function renderBatchResults(data) {
  const container = document.getElementById("batchResults");
  const cardsEl = document.getElementById("batchResultCards");
  const successCount = document.getElementById("batchSuccessCount");
  const errorCount = document.getElementById("batchErrorCount");
  const zipBtn = document.getElementById("batchDownloadZip");

  if (!container || !cardsEl) return;

  container.classList.remove("hidden");
  if (successCount) successCount.textContent = `${data.succeeded} réussi(s)`;
  if (errorCount) errorCount.textContent = `${data.failed} erreur(s)`;
  if (errorCount) errorCount.style.display = data.failed > 0 ? "" : "none";

  cardsEl.innerHTML = "";
  for (const item of data.results) {
    const card = document.createElement("div");
    card.className = "batch-result-card";

    const isOk = item.status === "success";

    /* Header */
    let headerHtml = `<div class="batch-result-header">
      <div class="batch-result-status ${isOk ? "status-ok" : "status-err"}"></div>
      <span class="batch-result-name">${escapeHtml(item.name)}</span>
      <span class="batch-result-badge ${isOk ? "badge-ok" : "badge-err"}">
        <i class="fas ${isOk ? "fa-check" : "fa-xmark"}"></i> ${isOk ? "OK" : "Erreur"}
      </span>
    </div>`;

    let bodyHtml = "";

    if (isOk) {
      /* File chips */
      let chipsHtml = "";
      if (item.notebook) {
        chipsHtml += `<span class="batch-result-file-chip chip-notebook"><i class="fas fa-book-open"></i> ${escapeHtml(item.notebook)}</span>`;
      }
      if (item.data_file) {
        const ext = item.data_file.split(".").pop().toUpperCase();
        chipsHtml += `<span class="batch-result-file-chip chip-data"><i class="fas fa-database"></i> ${escapeHtml(item.data_file)} <span style="opacity:0.7;font-size:0.68rem">${ext}</span></span>`;
      }
      if (item.has_ole) {
        chipsHtml += `<span class="batch-result-file-chip chip-ole"><i class="fas fa-file-excel"></i> OLE converti</span>`;
      }
      bodyHtml += `<div class="batch-result-files">${chipsHtml}</div>`;

      /* Steps */
      if (item.steps && item.steps.length) {
        let stepsHtml = item.steps
          .map((s) => `<span class="batch-result-step">${escapeHtml(s)}</span>`)
          .join("");
        bodyHtml += `<div class="batch-result-steps">${stepsHtml}</div>`;
      }
    } else {
      bodyHtml += `<div class="batch-result-error"><i class="fas fa-triangle-exclamation"></i> ${escapeHtml(item.error || "Erreur inconnue")}</div>`;
    }

    card.innerHTML = headerHtml + bodyHtml;
    cardsEl.appendChild(card);
  }

  if (zipBtn) {
    zipBtn.onclick = async () => {
      setLoading(zipBtn, true);
      try {
        await apiDownload(`/api/download/${data.job_id}/zip`);
        Toast.success("Téléchargement", "Archive ZIP téléchargée.");
      } catch (err) {
        Toast.error("Erreur", err.message);
      } finally {
        setLoading(zipBtn, false);
      }
    };
  }
}

/* ============================================================
   Bootstrap on DOMContentLoaded
   ============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  initNavbar();
  initModalCloseButtons();
  initSmoothScroll();
  initTabs();
  initSourceToggles();
  initUploadZones();

  const page = document.body.dataset.page;
  switch (page) {
    case "home":
      initHomePage();
      break;
    case "tools":
      initToolsPage();
      break;
    case "batch":
      initBatchPage();
      break;
  }
});
