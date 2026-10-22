/* Sección: Exportar reportes (resumen + descargas CSV). */
async function initReportes() {
  pintarResumen("rp-resumen", await api("/api/resumen"));
}
