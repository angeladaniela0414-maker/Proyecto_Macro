/* Búsqueda de salones libres por día y franja horaria */
(function () {
  const form = document.getElementById('formLibres');
  if (!form) return;
  const salida = document.getElementById('resultadoLibres');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const q = new URLSearchParams(new FormData(form));
    q.delete('csrf');
    salida.innerHTML = '<span class="suave">Buscando…</span>';
    try {
      const d = await Portal.api(form.dataset.api + '?' + q.toString());
      salida.innerHTML = d.salones.length
        ? '<div class="lista-chips">' + d.salones.map((s) =>
            '<span class="etiqueta ok"><i class="fa-solid fa-door-open"></i>' + Portal.esc(s.nombre) +
            ' · ' + s.capacidad + ' pers.</span>').join('') + '</div>'
        : '<p class="vacio">No hay salones libres en esa franja.</p>';
    } catch (err) {
      salida.innerHTML = '<div class="alerta alerta-error">' + Portal.esc(err.message) + '</div>';
    }
  });
})();
