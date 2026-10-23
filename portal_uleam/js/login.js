const form = document.getElementById('formLogin');
const error = document.getElementById('error');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  error.textContent = '';
  const boton = form.querySelector('button');
  boton.disabled = true;
  boton.textContent = 'Ingresando…';

  try {
    const r = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ correo: form.correo.value, clave: form.clave.value })
    });
    const datos = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(datos.error || 'No se pudo iniciar sesión.');
    window.location.href = '/panel';
  } catch (err) {
    error.textContent = err.message;
    boton.disabled = false;
    boton.textContent = 'Ingresar';
  }
});
