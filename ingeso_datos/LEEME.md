# Portal ULEAM · Gestión de horarios

Flask + SQL Server (`BD_Gestion_Horario`). HTML en `templates/`, CSS en `static/css/`, JS en `static/js/`.

## Puesta en marcha (Windows)
1. Instala el **ODBC Driver 17 for SQL Server** y Python 3.9+.
2. `pip install -r requirements.txt`
3. Revisa `config.py` (servidor SQL, driver, usuario). Por defecto: `localhost` con autenticación de Windows.
4. Crea/ajusta las tablas y carga datos de prueba (la BD y las tablas de usuarios ya deben existir):
   `python inicializar_datos.py`  (o `--sin-demo` para solo tablas). Ejecuta `sql/03_Horarios.sql` y `sql/04_Gestor.sql`
   (agrega a tus tablas: `Docente.asignatura`, `Estudiante.cedula/codigoRegistro/asignatura`, `Asignatura.idDocente`) y
   crea el administrador **admin / 1234** si no existe.
5. `abrir_puerto_80.bat` (una sola vez, como Administrador) y luego `iniciar.bat` (como Administrador).
6. La consola muestra las direcciones: `http://localhost/` y `http://<IP-del-equipo>/` para otros equipos de la red.

Si el puerto 80 está ocupado (IIS, Apache), ciérralos o arranca con otro puerto: `set PUERTO=8080`.

## Usuarios de prueba (clave `Uleam2026*`)
- Estudiante: dcarvajal@live.uleam.edu.ec
- Docente: jperez@live.uleam.edu.ec
- Gestión académica: gestion@live.uleam.edu.ec
- Administrador: **admin / 1234** → panel de gestión (CRUD). Cámbiala en «Cambiar mi contraseña» antes de abrir el portal a la red.
- En el login basta escribir la parte anterior a la @ (ej. `jperez`).

## Notas
- `Estudiante.carrera` debe coincidir exactamente con `Carrera.nombre`; `Estudiante.curso` es el paralelo (A, B…).
- Las contraseñas antiguas en texto plano siguen funcionando y se cifran solas al ingresar.
- «Generación de horarios» está vacía a propósito.
- Panel de gestión (`/index`): estudiantes, docentes, aulas, laboratorios, asignaturas, generación de horarios, claves y reportes CSV.
  Al crear un docente o estudiante se genera su correo (`nombre.apellido@live.uleam.edu.ec`) y su clave inicial es la cédula.
- Fondo del login: `static/img/montanas.svg`; puedes reemplazarlo cambiando la ruta en `static/css/login.css`.
