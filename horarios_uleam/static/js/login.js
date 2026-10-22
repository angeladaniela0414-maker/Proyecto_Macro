(function () {
  const $ = (s) => document.querySelector(s);
  const form = $('#formLogin');
  const clave = $('#clave');

  $('#verClave').addEventListener('click', function () {
    const visible = clave.type === 'text';
    clave.type = visible ? 'password' : 'text';
    this.textContent = visible ? 'Mostrar' : 'Ocultar';
    this.setAttribute('aria-label', visible ? 'Mostrar contraseña' : 'Ocultar contraseña');
  });

  form.addEventListener('submit', function () {
    const b = form.querySelector('button[type=submit]');
    b.disabled = true;
    b.textContent = 'Ingresando…';
  });

  const modal = $('#modalAyuda');
  const cerrar = () => { modal.hidden = true; };
  $('#abrirAyuda').addEventListener('click', (e) => { e.preventDefault(); modal.hidden = false; });
  modal.querySelectorAll('[data-cerrar]').forEach((b) => b.addEventListener('click', cerrar));
  modal.addEventListener('click', (e) => { if (e.target === modal) cerrar(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') cerrar(); });
})();
