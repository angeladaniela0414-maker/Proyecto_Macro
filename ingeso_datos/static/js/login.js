(function () {
  const $ = (s) => document.querySelector(s);
  const form = $('#formLogin');
  const clave = $('#clave');

  // Mostrar / ocultar contraseña
  $('#verClave').addEventListener('click', function () {
    const visible = clave.type === 'text';
    clave.type = visible ? 'password' : 'text';
    this.textContent = visible ? 'Mostrar' : 'Ocultar';
    this.setAttribute('aria-label', visible ? 'Mostrar contraseña' : 'Ocultar contraseña');
  });

  // Evitar doble envío
  form.addEventListener('submit', function () {
    const b = form.querySelector('button[type=submit]');
    b.disabled = true;
    b.textContent = 'Ingresando…';
  });

  // Modal "¿Olvidaste tu clave?"
  const modal = $('#modalRecuperar');
  const msg = $('#msgRecuperar');
  const abrir = (e) => {
    e.preventDefault();
    msg.hidden = true;
    modal.hidden = false;
    if (form.usuario.value.includes('@')) $('#correoRecuperar').value = form.usuario.value;
    $('#correoRecuperar').focus();
  };
  const cerrar = () => { modal.hidden = true; };
  document.querySelectorAll('[data-abrir-recuperar]').forEach((a) => a.addEventListener('click', abrir));
  document.querySelectorAll('[data-cerrar]').forEach((b) => b.addEventListener('click', cerrar));
  modal.addEventListener('click', (e) => { if (e.target === modal) cerrar(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') cerrar(); });

  $('#formRecuperar').addEventListener('submit', async function (e) {
    e.preventDefault();
    const boton = this.querySelector('button[type=submit]');
    boton.disabled = true;
    try {
      const r = await fetch(this.action, { method: 'POST', body: new FormData(this) });
      const d = await r.json();
      msg.textContent = d.mensaje;
      msg.className = 'msg-modal ' + (d.ok ? 'ok' : 'error');
    } catch (err) {
      msg.textContent = 'No se pudo enviar la solicitud. Revisa tu conexión.';
      msg.className = 'msg-modal error';
    }
    msg.hidden = false;
    boton.disabled = false;
  });
})();
