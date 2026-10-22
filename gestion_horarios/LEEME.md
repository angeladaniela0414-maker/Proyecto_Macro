# Portal ULEAM · Gestión de horarios

Flask + SQL Server (`BD_Gestion_Horario`). HTML en `templates/`, CSS en `static/css/`, JS en `static/js/`.

## Puesta en marcha (Windows)
1. Instala el **ODBC Driver 17 for SQL Server** y Python 3.9+.
2. `pip install -r requirements.txt`
3. Revisa `config.py` (servidor SQL, driver, usuario). Por defecto: `localhost` con autenticación de Windows.
4. Crea las tablas académicas y datos de prueba (la BD y las tablas de usuarios ya deben existir):
   `python inicializar_datos.py`  (o `--sin-demo` para solo tablas)
5. `abrir_puerto_80.bat` (una sola vez, como Administrador) y luego `iniciar.bat` (como Administrador).
6. La consola muestra las direcciones: `http://localhost/` y `http://<IP-del-equipo>/` para otros equipos de la red.

Si el puerto 80 está ocupado (IIS, Apache), ciérralos o arranca con otro puerto: `set PUERTO=8080`.

## Usuarios de prueba (clave `Uleam2026*`)
- Estudiante: dcarvajal@live.uleam.edu.ec
- Docente: jperez@live.uleam.edu.ec
- Gestión académica: gestion@live.uleam.edu.ec
- Administrador existente: Admin@live.uleam.edu.ec / admin1234 (entra al panel de gestión; su clave se cifra al primer ingreso)

## Notas
- `Estudiante.carrera` debe coincidir exactamente con `Carrera.nombre`; `Estudiante.curso` es el paralelo (A, B…).
- Las contraseñas antiguas en texto plano siguen funcionando y se cifran solas al ingresar.
- «Generación de horarios» está vacía a propósito.
