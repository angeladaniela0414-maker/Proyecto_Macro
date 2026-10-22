/* Utilidades compartidas, navegación entre secciones y pantalla de inicio. */
const $ = (id) => document.getElementById(id);

function esc(t) {
  return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function aviso(msg, tipo = "exito") {
  const t = $("toast");
  t.textContent = msg;
  t.className = `toast ver ${tipo}`;
  clearTimeout(aviso._id);
  aviso._id = setTimeout(() => (t.className = "toast"), 3200);
}

async function api(url, metodo = "GET", cuerpo) {
  const r = await fetch(url, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  if (r.status === 401) { window.location.href = "/login"; throw new Error("Sesión expirada"); }
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(datos.error || "Error en la solicitud");
  return datos;
}

/* Ejecuta una acción mostrando el error en un aviso en vez de romper el flujo. */
async function seguro(fn) {
  try { await fn(); } catch (e) { aviso(e.message, "error"); }
}

/* ------------------------------------------------------------ navegación */
const INICIALIZADORES = {
  inicio: () => initInicio(),
  estudiantes: () => initEstudiantes(),
  docentes: () => initDocentes(),
  aulas: () => initEspacios("Aula", "au"),
  laboratorios: () => initEspacios("Laboratorio", "la"),
  asignaturas: () => initAsignaturas(),
  generacion_horarios: () => initGeneracionHorarios(),
  exportar_reportes: () => initReportes(),
};

async function cargarSeccion(nombre) {
  document.querySelectorAll(".sidebar nav a").forEach((a) =>
    a.classList.toggle("activo", a.dataset.seccion === nombre));
  const cont = $("contenido");
  try {
    const r = await fetch(`/seccion/${nombre}`);
    if (r.status === 401) { window.location.href = "/login"; return; }
    if (!r.ok) throw new Error("No se pudo cargar la sección");
    cont.innerHTML = await r.text();
    await INICIALIZADORES[nombre]?.();
  } catch (e) {
    cont.textContent = e.message;
  }
}

document.addEventListener("click", (e) => {
  const enlace = e.target.closest("[data-seccion]");
  if (enlace) { e.preventDefault(); cargarSeccion(enlace.dataset.seccion); }
});

document.addEventListener("DOMContentLoaded", () => {
  $("btnSalir")?.addEventListener("click", async () => {
    await api("/api/logout", "POST");
    window.location.href = "/login";
  });
});

/* ------------------------------------------------------------ inicio */
const ETIQUETAS_RESUMEN = {
  estudiantes: "Estudiantes", docentes: "Docentes", aulas: "Aulas", laboratorios: "Laboratorios",
  asignaturas: "Asignaturas", horarios: "Bloques de horario",
};

function pintarResumen(destino, datos) {
  $(destino).innerHTML = Object.entries(ETIQUETAS_RESUMEN)
    .map(([k, nombre]) => `<div><strong>${esc(datos[k] ?? 0)}</strong>${nombre}</div>`).join("");
}

async function initInicio() {
  pintarResumen("in-resumen", await api("/api/resumen"));
}
