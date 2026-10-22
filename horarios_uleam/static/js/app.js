/* Comportamiento general: menú móvil, filtros automáticos, buscador de la página y confirmaciones. */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  const alternar = () => document.body.classList.toggle('menu-abierto');
  if ($('#btnMenu')) $('#btnMenu').addEventListener('click', alternar);
  if ($('#velo')) $('#velo').addEventListener('click', alternar);

  // Los selects con data-auto envían el formulario al cambiar (filtros del horario)
  $$('select[data-auto]').forEach((s) => s.addEventListener('change', () => s.form.submit()));

  // Buscador superior: filtra las filas/tarjetas .filtrable de la página
  const buscador = $('#buscador');
  if (buscador) {
    if (!$('.filtrable')) buscador.closest('.buscador').classList.add('oculto');
    buscador.addEventListener('input', () => {
      const q = buscador.value.trim().toLowerCase();
      $$('.filtrable').forEach((el) => el.classList.toggle('oculto', q && !el.textContent.toLowerCase().includes(q)));
    });
  }

  document.addEventListener('submit', (e) => {
    const t = e.target.closest('[data-confirmar]');
    if (t && !confirm(t.dataset.confirmar)) e.preventDefault();
  });

  // Los botones con data-confirmar y name=accion respetan el mensaje propio del botón
  document.addEventListener('click', (e) => {
    const b = e.target.closest('button[data-confirmar-boton]');
    if (b && !confirm(b.dataset.confirmarBoton)) e.preventDefault();
  });

  $$('.alerta[data-auto]').forEach((a) => setTimeout(() => a.remove(), 7000));
})();
