/* Sección: Claves de acceso (solicitudes de recuperación y restablecimiento manual). */
async function initClaves() {
  const ETIQ = { Pendiente: "aviso", Atendida: "ok", Rechazada: "mal" };

  function mostrar(correo, clave) {
    $("cl-resultado").innerHTML = `
      <div class="tarjeta aviso-clave" style="margin-top:1rem">
        Clave temporal para <strong>${esc(correo)}</strong>: <code>${esc(clave)}</code>
        <p class="sub">Se muestra una sola vez. Entrégala por un canal seguro; el usuario puede cambiarla en «Mi cuenta».</p>
      </div>`;
  }

  async function cargar() {
    const lista = await api("/api/claves/solicitudes");
    $("cl-tabla").innerHTML = lista.map((s) => `
      <tr><td>${esc(s.correo)}</td><td>${esc(s.fecha)}</td>
      <td><span class="etiqueta ${ETIQ[s.estado] || ""}">${esc(s.estado)}</span></td>
      <td>${s.estado === "Pendiente" ? `<button class="btn chico" data-atender="${s.id}">Generar clave</button>` : ""}</td></tr>`).join("")
      || `<tr><td colspan="4" class="sub">No hay solicitudes</td></tr>`;
  }

  $("cl-restablecer").addEventListener("click", () => seguro(async () => {
    const correo = $("cl-correo").value.trim();
    const r = await api("/api/claves/restablecer", "POST", { correo });
    mostrar(r.correo, r.clave); $("cl-correo").value = "";
  }));

  $("cl-tabla").addEventListener("click", (e) => {
    const id = e.target.dataset.atender;
    if (id) seguro(async () => {
      const r = await api(`/api/claves/solicitudes/${id}/atender`, "POST");
      mostrar(r.correo, r.clave); await cargar();
    });
  });
  await cargar();
}
