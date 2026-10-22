/* Docente: ver los estudiantes que solicitaron una tutoría */
(function () {
  document.addEventListener('click', async (e) => {
    const b = e.target.closest('[data-solicitantes]');
    if (!b) return;
    const cuerpo = document.getElementById('cuerpoSolicitantes');
    document.getElementById('tituloSolicitantes').textContent = b.dataset.nombre;
    cuerpo.innerHTML = '<tr><td colspan="4" class="suave">Cargando…</td></tr>';
    Portal.abrirModal('modalSolicitantes');
    try {
      const d = await Portal.api(b.dataset.url);
      cuerpo.innerHTML = d.estudiantes.length ? d.estudiantes.map((s) =>
        '<tr><td>' + Portal.esc(s.apellido + ' ' + s.nombre) + '</td><td>' + Portal.esc(s.correo) +
        '</td><td>' + s.nivel + '</td><td>' + Portal.esc(s.curso) + '</td></tr>').join('')
        : '<tr><td colspan="4" class="vacio">Aún no hay solicitudes.</td></tr>';
    } catch (err) {
      cuerpo.innerHTML = '<tr><td colspan="4">' + Portal.esc(err.message) + '</td></tr>';
    }
  });
})();
