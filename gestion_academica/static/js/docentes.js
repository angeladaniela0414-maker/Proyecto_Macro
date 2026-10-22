/* Sección: Docentes (registrar, buscar, activar/desactivar y eliminar). */
async function initDocentes() {
  let lista = [];

  function pintar() {
    const q = $("do-buscar").value.trim().toLowerCase();
    const filas = lista.filter((d) => `${d.nombre} ${d.apellido} ${d.cedula}`.toLowerCase().includes(q));
    $("do-tabla").innerHTML = filas.map((d) => `
      <tr><td>${esc(d.cedula)}</td><td>${esc(d.nombre)} ${esc(d.apellido)}</td><td>${esc(d.especialidad)}</td>
      <td>${esc(d.asignatura)}</td><td>${esc(d.nivel)}</td>
      <td><span class="etiqueta ${d.estado ? "ok" : "mal"}">${d.estado ? "Activo" : "Inactivo"}</span></td>
      <td><button class="btn chico" data-toggle="${d.id}">${d.estado ? "Desactivar" : "Activar"}</button>
          <button class="btn peligro chico" data-borrar="${d.id}">Eliminar</button></td></tr>`).join("")
      || `<tr><td colspan="7" class="sub">Sin resultados</td></tr>`;
  }

  async function cargar() { lista = await api("/api/docentes"); pintar(); }

  $("do-buscar").addEventListener("input", pintar);

  $("do-agregar").addEventListener("click", () => seguro(async () => {
    await api("/api/docentes", "POST", {
      cedula: $("do-ced").value.trim(), nombre: $("do-nom").value.trim(), apellido: $("do-ape").value.trim(),
      especialidad: $("do-esp").value.trim(), asignatura: $("do-asig").value.trim(), nivel: $("do-niv").value,
    });
    ["do-ced", "do-nom", "do-ape", "do-esp", "do-asig", "do-niv"].forEach((i) => ($(i).value = ""));
    aviso("Docente registrado"); await cargar();
  }));

  $("do-tabla").addEventListener("click", (e) => {
    const { toggle, borrar } = e.target.dataset;
    if (toggle) seguro(async () => { await api(`/api/docentes/${toggle}/estado`, "PUT"); await cargar(); });
    if (borrar && confirm("¿Eliminar este docente?")) seguro(async () => {
      await api(`/api/docentes/${borrar}`, "DELETE");
      aviso("Docente eliminado"); await cargar();
    });
  });
  await cargar();
}
