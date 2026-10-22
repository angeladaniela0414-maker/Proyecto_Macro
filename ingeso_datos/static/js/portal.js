/* Comportamiento general del portal */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const csrf = ($('meta[name=csrf]') || {}).content;

  // --- Utilidades globales ---------------------------------------------------
  window.Portal = {
    async api(url, opciones = {}) {
      const o = Object.assign({ headers: {} }, opciones);
      o.headers['Accept'] = 'application/json';
      if (o.method && o.method !== 'GET') o.headers['X-CSRF-Token'] = csrf;
      const r = await fetch(url, o);
      if (r.status === 401) { location.href = '/login'; throw new Error('Sesión expirada'); }
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.error || 'No se pudo completar la acción.');
      return d;
    },
    aviso(texto, tipo) {
      const t = document.createElement('div');
      t.className = 'toast ' + (tipo || '');
      t.textContent = texto;
      $('#toasts').appendChild(t);
      setTimeout(() => t.remove(), 4500);
    },
    abrirModal(id) {
      const m = document.getElementById(id);
      if (!m) return;
      m.hidden = false;
      const campo = $('input:not([type=hidden]),select', m);
      if (campo) campo.focus();
    },
    cerrarModal(m) { m.hidden = true; },
    esc(t) {
      return String(t == null ? '' : t).replace(/[&<>"']/g, (c) =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    },
  };

  // --- Menú lateral en móvil ---------------------------------------------------
  const alternar = () => document.body.classList.toggle('menu-abierto');
  const btn = $('#btnMenu');
  if (btn) btn.addEventListener('click', alternar);
  const velo = $('#velo');
  if (velo) velo.addEventListener('click', alternar);

  // --- Buscador superior: filtra tablas y tarjetas de la página -------------------
  const buscador = $('#buscador');
  if (buscador) {
    buscador.addEventListener('input', () => {
      const q = buscador.value.trim().toLowerCase();
      $$('.filtrable').forEach((el) => {
        el.classList.toggle('oculto', q && !el.textContent.toLowerCase().includes(q));
      });
    });
    if (!$('.filtrable')) buscador.closest('.buscador').classList.add('oculto');
  }

  // --- Modales ---------------------------------------------------------------
  document.addEventListener('click', (e) => {
    const abrir = e.target.closest('[data-abrir-modal]');
    if (abrir) { Portal.abrirModal(abrir.dataset.abrirModal); return; }
    if (e.target.closest('[data-cerrar]')) { Portal.cerrarModal(e.target.closest('.modal')); return; }
    if (e.target.classList && e.target.classList.contains('modal')) Portal.cerrarModal(e.target);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') $$('.modal:not([hidden])').forEach(Portal.cerrarModal);
  });

  // --- Confirmaciones ----------------------------------------------------------
  document.addEventListener('submit', (e) => {
    const t = e.target.closest('[data-confirmar]');
    if (t && !confirm(t.dataset.confirmar)) e.preventDefault();
  });

  // --- Generar contraseña aleatoria -----------------------------------------------
  document.addEventListener('click', (e) => {
    const g = e.target.closest('[data-generar-clave]');
    if (!g) return;
    const alfabeto = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789';
    const buf = new Uint32Array(10);
    crypto.getRandomValues(buf);
    const campo = $(g.dataset.generarClave);
    campo.value = [...buf].map((n) => alfabeto[n % alfabeto.length]).join('');
    campo.type = 'text';
  });

  // --- Copiar al portapapeles --------------------------------------------------------
  document.addEventListener('click', async (e) => {
    const c = e.target.closest('[data-copiar]');
    if (!c) return;
    try { await navigator.clipboard.writeText(c.dataset.copiar); Portal.aviso('Copiado'); }
    catch (_) { Portal.aviso('Selecciona el texto y cópialo manualmente.', 'error'); }
  });

  // --- Cerrar avisos automáticos -----------------------------------------------------
  $$('.alerta[data-auto]').forEach((a) => setTimeout(() => a.remove(), 6000));
})();
