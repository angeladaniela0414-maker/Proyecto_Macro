/* ---------- menú: [tabla en la base de datos, texto visible] ---------- */
const MENU = [
  { grupo: 'Usuarios', items: [
    ['Estudiante', 'Estudiantes'],
    ['Docente', 'Docentes'],
    ['Gestion_Academica', 'Gestión académica'],
    ['Administrador', 'Administradores'] ] },
  { grupo: 'Estructura académica', items: [
    ['Facultad', 'Facultades'],
    ['Carrera', 'Carreras'],
    ['PeriodoAcademico', 'Períodos académicos'],
    ['Asignatura', 'Asignaturas'],
    ['Salon', 'Aulas y salones'] ] },
  { grupo: 'Horarios y registros', items: [
    ['Horario', 'Horarios'],
    ['Tutoria', 'Tutorías'],
    ['TutoriaSolicitud', 'Solicitudes de tutoría'],
    ['Registro', 'Registros'],
    ['SolicitudClave', 'Solicitudes de clave'] ] }
];

/* Campos de texto/número con valores fijos (el primero es el predeterminado) */
const FIJAS = {
  'Horario.dia': [[1, 'Lunes'], [2, 'Martes'], [3, 'Miércoles'], [4, 'Jueves'], [5, 'Viernes']],
  'Docente.estado': [[1, 'Activo'], [0, 'Inactivo']],
  'Salon.tipoSalon': ['Aula', 'Laboratorio', 'Auditorio'],
  'Salon.estado': ['Disponible', 'Mantenimiento'],
  'Tutoria.estado': ['Programada', 'Cancelada'],
  'TutoriaSolicitud.estado': ['Solicitada', 'Cancelada'],
  'Registro.estado': ['Activo', 'Anulado'],
  'SolicitudClave.estado': ['Pendiente', 'Atendida', 'Rechazada']
};
const fija = (tabla, campo) => (FIJAS[`${tabla}.${campo}`] || null)
  ?.map(x => Array.isArray(x) ? x : [x, x]);

const PALABRAS = {
  numero: 'número', dia: 'día', tutoria: 'tutoría', periodo: 'período', codigo: 'código',
  cedula: 'cédula', gestion: 'gestión', salon: 'salón', academica: 'académica'
};
function etiqueta(n) {
  if (n === 'id') return 'ID';
  if (n === 'contraseña') return 'Contraseña';
  if (n === 'correoUsuario') return 'Correo institucional';
  const s = n.replace(/^id(?=[A-Z])/, '').replace(/([a-z])([A-Z])/g, '$1 $2').toLowerCase()
    .split(' ').map(p => PALABRAS[p] || p).join(' ');
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const $ = (s) => document.querySelector(s);
const esc = (v) => String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const estado = { tabla: null, titulo: '', datos: null, opciones: {}, editando: null };

async function api(url, metodo = 'GET', cuerpo) {
  const r = await fetch(url, {
    method: metodo,
    headers: { 'Content-Type': 'application/json' },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined
  });
  if (r.status === 401) { window.location.href = '/'; throw new Error('Sesión expirada.'); }
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(datos.error || 'Ocurrió un error.');
  return datos;
}

/* ---------- menú lateral ---------- */
function construirMenu() {
  $('#listaMenu').innerHTML = MENU.map(g => `
    <div class="grupo">${g.grupo}</div>
    ${g.items.map(([t, txt]) => `<button class="opcion" data-tabla="${t}" data-titulo="${txt}">${txt}</button>`).join('')}
  `).join('');
}
$('#listaMenu').addEventListener('click', (e) => {
  const b = e.target.closest('button.opcion');
  if (!b) return;
  document.querySelectorAll('.opcion').forEach(x => x.classList.toggle('activa', x === b));
  document.body.classList.remove('menu-abierto');
  abrirTabla(b.dataset.tabla, b.dataset.titulo);
});
$('#btnMenu').addEventListener('click', () => document.body.classList.toggle('menu-abierto'));
$('#velo').addEventListener('click', () => document.body.classList.remove('menu-abierto'));

/* ---------- listado ---------- */
async function abrirTabla(tabla, titulo) {
  estado.tabla = tabla;
  estado.titulo = titulo;
  $('#bienvenida').hidden = true;
  $('#vista').hidden = false;
  $('#titulo').textContent = titulo;
  $('#mensaje').textContent = '';
  await cargar();
}

async function cargar() {
  try {
    const datos = await api(`/api/${estado.tabla}`);
    const tablas = [...new Set(Object.values(datos.refs))];
    const listas = await Promise.all(tablas.map(t => api(`/api/${t}/opciones`)));
    estado.opciones = Object.fromEntries(tablas.map((t, i) => [t, listas[i]]));
    estado.datos = datos;
    dibujar();
  } catch (err) {
    aviso(err.message, true);
  }
}

function texto(col, v) {
  if (v === null || v === undefined || v === '') return '—';
  const clave = typeof v === 'boolean' ? (v ? '1' : '0') : String(v);
  const f = fija(estado.tabla, col);
  if (f) return (f.find(([val]) => String(val) === clave) || [0, v])[1];
  const ref = estado.datos.refs[col];
  if (ref) return (estado.opciones[ref].find(o => o.id === v) || { texto: v }).texto;
  if (typeof v === 'boolean') return v ? 'Sí' : 'No';
  return v;
}

function dibujar() {
  const { columnas, filas } = estado.datos;
  $('#cabecera').innerHTML = `<tr>${columnas.map(c => `<th>${etiqueta(c)}</th>`).join('')}<th>Acciones</th></tr>`;
  $('#cuerpo').innerHTML = filas.length
    ? filas.map(f => `<tr>
        ${columnas.map(c => `<td>${esc(texto(c, f[c]))}</td>`).join('')}
        <td><div class="acciones-fila">
          <button class="mini editar" data-id="${f.id}">Editar</button>
          <button class="mini borrar" data-id="${f.id}">Eliminar</button>
        </div></td></tr>`).join('')
    : `<tr><td class="vacio" colspan="${columnas.length + 1}">Aún no hay registros. Usa «Nuevo registro» para agregar el primero.</td></tr>`;
}

$('#cuerpo').addEventListener('click', async (e) => {
  const b = e.target.closest('button[data-id]');
  if (!b) return;
  const id = Number(b.dataset.id);
  if (b.classList.contains('editar')) {
    abrirFormulario(estado.datos.filas.find(f => f.id === id));
  } else if (confirm('¿Eliminar este registro? Esta acción no se puede deshacer.')) {
    try {
      await api(`/api/${estado.tabla}/${id}`, 'DELETE');
      await cargar();
      aviso('Registro eliminado.');
    } catch (err) { aviso(err.message, true); }
  }
});

/* ---------- formulario crear / editar ---------- */
function selectHtml(id, c, opciones, valor, vacio) {
  const marcado = valor === null || valor === undefined ? '' : (typeof valor === 'boolean' ? (valor ? '1' : '0') : String(valor));
  return `<select id="${id}" ${c.obligatorio ? 'required' : ''}>
    ${vacio !== null ? `<option value="">${vacio}</option>` : ''}
    ${opciones.map(([v, t]) => `<option value="${esc(v)}" ${String(v) === marcado ? 'selected' : ''}>${esc(t)}</option>`).join('')}
  </select>`;
}

function abrirFormulario(fila) {
  const editar = !!fila;
  estado.editando = editar ? fila.id : null;
  $('#dlgTitulo').textContent = `${editar ? 'Editar registro' : 'Nuevo registro'} · ${estado.titulo}`;
  $('#btnGuardar').textContent = editar ? 'Guardar cambios' : 'Crear registro';
  $('#dlgError').textContent = '';

  $('#campos').innerHTML = estado.datos.campos.map(c => {
    const id = `f_${c.nombre}`;
    const v = editar ? fila[c.nombre] : null;
    const f = fija(estado.tabla, c.nombre);
    let control;

    if (c.ref) {
      const ops = estado.opciones[c.ref].map(o => [o.id, o.texto]);
      control = selectHtml(id, c, ops, v, c.obligatorio ? 'Seleccione…' : 'Sin asignar');
    } else if (f) {
      control = selectHtml(id, c, f, v, c.nulo ? 'Sin definir' : null);
    } else if (c.tipo === 'bit') {
      control = selectHtml(id, c, [[0, 'No'], [1, 'Sí']], v, c.nulo ? 'Sin definir' : null);
    } else {
      const tipo = { number: 'number', date: 'date', time: 'time', datetime: 'datetime-local', password: 'password' }[c.tipo] || 'text';
      let valor = v === null || v === undefined ? '' : String(v);
      if (c.tipo === 'datetime') valor = valor.replace(' ', 'T');
      if (c.tipo === 'password') valor = '';
      const req = c.obligatorio && !(c.tipo === 'password' && editar);
      const ayuda = c.tipo === 'password' ? (editar ? 'Déjala en blanco para conservarla' : '')
        : (c.default ? 'Valor predeterminado' : '');
      control = `<input id="${id}" type="${tipo}" value="${esc(valor)}" ${req ? 'required' : ''}
        ${c.max ? `maxlength="${c.max}"` : ''} ${tipo === 'number' ? 'step="1"' : ''}
        ${c.tipo === 'password' ? 'autocomplete="new-password"' : ''} placeholder="${ayuda}">`;
    }
    const obligatorio = c.obligatorio && !(c.tipo === 'password' && editar);
    return `<div class="campo"><label for="${id}">${etiqueta(c.nombre)}${obligatorio ? ' <span>*</span>' : ''}</label>${control}</div>`;
  }).join('');

  $('#dlg').showModal();
}

$('#btnNuevo').addEventListener('click', () => abrirFormulario(null));
$('#btnCancelar').addEventListener('click', () => $('#dlg').close());

$('#formDlg').addEventListener('submit', async (e) => {
  e.preventDefault();
  $('#dlgError').textContent = '';
  const cuerpo = {};
  estado.datos.campos.forEach(c => { cuerpo[c.nombre] = document.getElementById(`f_${c.nombre}`).value; });
  const editando = estado.editando;
  try {
    if (editando !== null) await api(`/api/${estado.tabla}/${editando}`, 'PUT', cuerpo);
    else await api(`/api/${estado.tabla}`, 'POST', cuerpo);
    $('#dlg').close();
    await cargar();
    aviso(editando !== null ? 'Cambios guardados.' : 'Registro creado.');
  } catch (err) {
    $('#dlgError').textContent = err.message;
  }
});

/* ---------- mensajes ---------- */
let temporizador;
function aviso(texto, malo = false) {
  const m = $('#mensaje');
  m.textContent = texto;
  m.className = `mensaje ${malo ? 'mal' : 'ok'}`;
  clearTimeout(temporizador);
  if (!malo) temporizador = setTimeout(() => { m.textContent = ''; }, 4000);
}

construirMenu();
