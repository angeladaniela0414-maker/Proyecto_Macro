/* Matriz semanal de horarios: carga /api/horario y la dibuja. */
(function () {
  const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'];
  const esc = (t) => Portal.esc(t);

  function filtrosDe(el) {
    return [...document.querySelectorAll('[data-filtro][data-destino="' + el.id + '"]')];
  }

  function dibujar(el, bloques) {
    if (!bloques.length) {
      el.innerHTML = '<div class="horario-estado"><i class="fa-regular fa-calendar-xmark"></i><br>' +
        'No hay clases registradas para esta selección.</div>';
      return;
    }
    const grupo = el.dataset.grupo === '1';
    const hoy = new Date().getDay(); // 0 = domingo
    const franjas = [...new Set(bloques.map((b) => b.horaInicio + '|' + b.horaFin))].sort();
    let h = '<div class="horario-caja"><table class="horario-tabla"><thead><tr><th>Hora</th>';
    DIAS.forEach((d, i) => { h += '<th class="' + (hoy === i + 1 ? 'hoy' : '') + '">' + d + '</th>'; });
    h += '</tr></thead><tbody>';
    franjas.forEach((f) => {
      const [hi, hf] = f.split('|');
      h += '<tr><td class="franja">' + hi + ' - ' + hf + '</td>';
      for (let d = 1; d <= 5; d++) {
        const celda = bloques.filter((b) => b.dia === d && b.horaInicio === hi && b.horaFin === hf);
        const cls = hoy === d ? 'hoy' : '';
        if (!celda.length) { h += '<td class="libre ' + cls + '">—</td>'; continue; }
        h += '<td class="' + cls + '">' + celda.map((b) =>
          '<div class="bloque-clase"><strong>' + esc(b.asignatura) + '</strong><div class="meta">' +
          (grupo ? '<span><i class="fa-solid fa-layer-group"></i>Nivel ' + b.nivel + ' · Par. ' + esc(b.paralelo) + '</span>' : '') +
          (b.docente ? '<span><i class="fa-solid fa-user-tie"></i>' + esc(b.docente) + '</span>' : '') +
          (b.salon ? '<span><i class="fa-solid fa-door-open"></i>' + esc(b.salon) + '</span>' : '') +
          '</div></div>').join('') + '</td>';
      }
      h += '</tr>';
    });
    el.innerHTML = h + '</tbody></table></div>';
  }

  async function cargar(el) {
    const params = new URLSearchParams(JSON.parse(el.dataset.fijos || '{}'));
    filtrosDe(el).forEach((s) => { if (s.value) params.set(s.dataset.filtro, s.value); });
    el.classList.add('cargando');
    try {
      const d = await Portal.api(el.dataset.api + '?' + params.toString());
      dibujar(el, d.bloques);
    } catch (e) {
      el.innerHTML = '<div class="horario-estado">No se pudo cargar el horario. ' + esc(e.message) + '</div>';
    } finally {
      el.classList.remove('cargando');
    }
  }

  function iniciar(el) {
    filtrosDe(el).forEach((s) => {
      s.dataset.inicial = s.value;
      s.addEventListener('change', () => cargar(el));
    });
    document.querySelectorAll('[data-reset-filtros="' + el.id + '"]').forEach((b) =>
      b.addEventListener('click', () => {
        filtrosDe(el).forEach((s) => { s.value = s.dataset.inicial; });
        cargar(el);
      }));
    if (el.dataset.diferido !== '1') cargar(el);
  }

  window.HorarioApp = { cargar };
  document.querySelectorAll('.horario-app').forEach(iniciar);

  // Gestión: ver el horario de un docente en un modal
  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-horario-docente]');
    if (!b) return;
    const el = document.getElementById('horarioDocente');
    el.dataset.fijos = JSON.stringify({ docente: b.dataset.horarioDocente });
    document.getElementById('tituloHorarioDocente').textContent = 'Horario de ' + b.dataset.nombre;
    Portal.abrirModal('modalHorarioDocente');
    cargar(el);
  });
})();
