/* Secciones: Aulas y Laboratorios (misma lógica, distinto tipo y prefijo de ids). */
const CLASE_SALON = { Disponible: "ok", Ocupado: "aviso", Mantenimiento: "mal" };

async function initEspacios(tipo, p) {
  async function pintar() {
    const lista = await api(`/api/salones?tipo=${encodeURIComponent(tipo)}`);
    $(`${p}-tabla`).innerHTML = lista.map((s) => `
      <tr><td>${esc(s.numero)}</td><td>${esc(s.capacidad)}</td>
      <td><span class="etiqueta ${CLASE_SALON[s.estado] || ""}">${esc(s.estado)}</span></td>
      <td>
        <select data-estado="${s.id}" aria-label="Estado del ${esc(tipo.toLowerCase())} ${esc(s.numero)}">
          ${["Disponible", "Ocupado", "Mantenimiento"].map((e) => `<option ${e === s.estado ? "selected" : ""}>${e}</option>`).join("")}
        </select>
        <button class="btn peligro chico" data-borrar="${s.id}">Eliminar</button>
      </td></tr>`).join("") || `<tr><td colspan="4" class="sub">Aún no hay registros</td></tr>`;
  }

  $(`${p}-agregar`).addEventListener("click", () => seguro(async () => {
    await api("/api/salones", "POST", { numero: $(`${p}-numero`).value, capacidad: $(`${p}-cap`).value, tipo });
    $(`${p}-numero`).value = ""; $(`${p}-cap`).value = "";
    aviso(`${tipo} registrado`); await pintar();
  }));

  $(`${p}-tabla`).addEventListener("change", (e) => {
    if (e.target.dataset.estado) seguro(async () => {
      await api(`/api/salones/${e.target.dataset.estado}/estado`, "PUT", { estado: e.target.value });
      aviso("Estado actualizado"); await pintar();
    });
  });

  $(`${p}-tabla`).addEventListener("click", (e) => {
    if (e.target.dataset.borrar && confirm(`¿Eliminar este ${tipo.toLowerCase()}?`)) seguro(async () => {
      await api(`/api/salones/${e.target.dataset.borrar}`, "DELETE");
      aviso(`${tipo} eliminado`); await pintar();
    });
  });
  await pintar();
}
