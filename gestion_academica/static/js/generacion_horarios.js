/* Módulo: Generación de horarios (grilla semanal, generación automática y alta manual). */
const DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"];
const HORAS = Array.from({ length: 14 }, (_, i) => 7 + i); // 7..20

async function initGeneracionHorarios() {
  const nivel = () => $("gh-nivel").value;
  const periodo = () => $("gh-periodo").value.trim();

  async function cargarCatalogos() {
    const [asig, salones] = await Promise.all([api(`/api/asignaturas?nivel=${nivel()}`), api("/api/salones")]);
    $("gh-asig").innerHTML = asig.map((a) => `<option value="${a.id}">${esc(a.nombre)}</option>`).join("")
      || `<option value="">(sin asignaturas en este nivel)</option>`;
    $("gh-salon").innerHTML = salones.filter((s) => s.estado !== "Mantenimiento")
      .map((s) => `<option value="${s.id}">${esc(s.numero)} · ${esc(s.tipo)} (${esc(s.capacidad)})</option>`).join("");
  }

  async function pintarGrilla() {
    const horarios = await api(`/api/horarios?nivel=${nivel()}&periodo=${encodeURIComponent(periodo())}`);
    const celdas = {};
    horarios.forEach((h) => {
      (celdas[`${h.dia}|${h.hora_inicio}`] ||= []).push(h);
    });
    const cabecera = `<tr><th>Hora</th>${DIAS_SEMANA.map((d) => `<th>${d}</th>`).join("")}</tr>`;
    const filas = HORAS.map((hora) => `<tr><td>${hora}:00</td>${DIAS_SEMANA.map((dia) => {
      const bloques = (celdas[`${dia}|${hora}`] || []).map((h) => `
        <div class="bloque">
          <button title="Eliminar bloque" aria-label="Eliminar ${esc(h.asignatura)}" data-del="${h.id}">×</button>
          <strong>${esc(h.asignatura)}</strong>
          <small>${h.hora_inicio}:00–${h.hora_fin}:00 · Salón ${esc(h.salon)} · Par. ${esc(h.paralelo)}</small>
          <small>${esc(h.doc_nombre || "")} ${esc(h.doc_apellido || "")}</small>
        </div>`).join("");
      return `<td>${bloques}</td>`;
    }).join("")}</tr>`).join("");
    $("gh-grilla").innerHTML = cabecera + filas;
  }

  const refrescar = async () => { await cargarCatalogos(); await pintarGrilla(); };

  $("gh-nivel").addEventListener("change", () => seguro(refrescar));
  $("gh-periodo").addEventListener("change", () => seguro(pintarGrilla));

  $("gh-generar").addEventListener("click", () => seguro(async () => {
    const r = await api("/api/horarios/generar", "POST",
      { nivel: nivel(), periodo: periodo(), paralelo: $("gh-paralelo").value.trim() || "A" });
    $("gh-avisos").innerHTML = r.sin_ubicar.map((m) => `<li>${esc(m)}</li>`).join("");
    aviso(`${r.creados} bloque(s) generado(s)`);
    await pintarGrilla();
  }));

  $("gh-limpiar").addEventListener("click", () => {
    if (!confirm("¿Eliminar todos los horarios de este nivel y periodo?")) return;
    seguro(async () => {
      await api("/api/horarios/limpiar", "POST", { nivel: nivel(), periodo: periodo() });
      $("gh-avisos").innerHTML = "";
      aviso("Horarios eliminados"); await pintarGrilla();
    });
  });

  $("gh-agregar").addEventListener("click", () => seguro(async () => {
    await api("/api/horarios", "POST", {
      asignatura_id: $("gh-asig").value, salon_id: $("gh-salon").value, dia: $("gh-dia").value,
      hora_inicio: $("gh-ini").value, hora_fin: $("gh-fin").value,
      paralelo: $("gh-paralelo").value.trim() || "A", periodo: periodo(),
    });
    aviso("Bloque agregado"); await pintarGrilla();
  }));

  $("gh-grilla").addEventListener("click", (e) => {
    if (e.target.dataset.del) seguro(async () => {
      await api(`/api/horarios/${e.target.dataset.del}`, "DELETE");
      aviso("Bloque eliminado"); await pintarGrilla();
    });
  });

  await refrescar();
}
