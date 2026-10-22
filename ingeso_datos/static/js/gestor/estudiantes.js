/* Sección: Estudiantes (registrar, buscar, filtrar por nivel y eliminar). */
async function initEstudiantes() {
  let lista = [];

  function pintar() {
    const q = $("es-buscar").value.trim().toLowerCase();
    const nivel = $("es-filtro-niv").value;
    const filas = lista.filter((e) =>
      (!nivel || String(e.nivel) === nivel) &&
      `${e.nombre} ${e.apellido} ${e.cedula} ${e.codigo_registro}`.toLowerCase().includes(q));
    $("es-tabla").innerHTML = filas.map((e) => `
      <tr><td>${esc(e.codigo_registro)}</td><td>${esc(e.cedula)}</td>
      <td>${esc(e.nombre)} ${esc(e.apellido)}</td><td>${esc(e.correo_institucional)}</td>
      <td>${esc(e.carrera)}</td><td>${esc(e.nivel)}</td><td>${esc(e.curso)}</td>
      <td><button class="btn peligro chico" data-borrar="${e.id}" aria-label="Eliminar a ${esc(e.nombre)} ${esc(e.apellido)}">Eliminar</button></td></tr>`).join("")
      || `<tr><td colspan="8" class="sub">Sin resultados</td></tr>`;
  }

  async function cargar() { lista = await api("/api/estudiantes"); pintar(); }

  $("es-buscar").addEventListener("input", pintar);
  $("es-filtro-niv").addEventListener("change", pintar);

  $("es-agregar").addEventListener("click", () => seguro(async () => {
    const r = await api("/api/estudiantes", "POST", {
      cedula: $("es-ced").value.trim(), codigo_registro: $("es-cod").value,
      nombre: $("es-nom").value.trim(), apellido: $("es-ape").value.trim(),
      carrera: $("es-car").value.trim(), nivel: $("es-niv").value,
      curso: $("es-cur").value.trim(), asignatura: $("es-asig").value.trim(),
    });
    ["es-ced", "es-cod", "es-nom", "es-ape", "es-niv", "es-cur", "es-asig"].forEach((i) => ($(i).value = ""));
    aviso(`Estudiante registrado: ${r.correo_institucional} (clave inicial: su cédula)`);
    await cargar();
  }));

  $("es-tabla").addEventListener("click", (e) => {
    if (e.target.dataset.borrar && confirm("¿Eliminar este estudiante?")) seguro(async () => {
      await api(`/api/estudiantes/${e.target.dataset.borrar}`, "DELETE");
      aviso("Estudiante eliminado"); await cargar();
    });
  });
  await cargar();
}
