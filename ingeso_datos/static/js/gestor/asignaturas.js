/* Sección: Asignaturas (alta y asignación de docente). */
async function initAsignaturas() {
  const docentes = (await api("/api/docentes")).filter((d) => d.estado);

  async function pintar() {
    const asignaturas = await api("/api/asignaturas");
    $("as-tabla").innerHTML = asignaturas.map((a) => `
      <tr><td>${esc(a.codigo)}</td><td>${esc(a.nombre)}</td><td>${esc(a.nivel)}</td><td>${esc(a.carrera)}</td>
      <td>${esc(a.horas_semanales)}</td>
      <td><select data-doc="${a.id}" aria-label="Docente de ${esc(a.nombre)}">
        <option value="">— Sin asignar —</option>
        ${docentes.map((d) => `<option value="${d.id}" ${d.id === a.docente_id ? "selected" : ""}>${esc(d.nombre)} ${esc(d.apellido)}</option>`).join("")}
      </select></td></tr>`).join("");
  }

  $("as-agregar").addEventListener("click", () => seguro(async () => {
    await api("/api/asignaturas", "POST", {
      codigo: $("as-cod").value.trim(), nombre: $("as-nom").value.trim(), nivel: $("as-niv").value,
      carrera: $("as-car").value.trim(), horas_semanales: $("as-hor").value,
    });
    ["as-cod", "as-nom", "as-niv"].forEach((i) => ($(i).value = ""));
    aviso("Asignatura agregada"); await pintar();
  }));

  $("as-tabla").addEventListener("change", (e) => {
    if (e.target.dataset.doc) seguro(async () => {
      await api(`/api/asignaturas/${e.target.dataset.doc}/docente`, "PUT", { docente_id: e.target.value || null });
      aviso("Docente asignado");
    });
  });
  await pintar();
}
