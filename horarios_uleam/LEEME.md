# Sistema de horarios ULEAM (FastAPI + SQL Server 2022)

Este sistema **no ingresa datos**. Lee lo que carga el programa aparte de ingreso de datos en `BD_Gestion_Horario`
y solo **escribe en `Horario`** cuando Gestión académica genera o descarta un horario.
No crea bases ni tablas.

## Roles (según la tabla donde esté la cuenta)
| Rol | Tabla | Qué hace |
|---|---|---|
| Gestión | `Gestion_Academica` (y `Administrador`) | Genera/descarta horarios por carrera, nivel y paralelo; los consulta; ve docentes, estudiantes, salones y conflictos |
| Docente | `Docente` | Su horario; horarios de otros niveles/asignaturas/paralelos con filtros; PDF |
| Estudiante | `Estudiante` | Su horario (carrera + nivel + paralelo); filtros; PDF |

Quien genera el horario lo «reparte»: docentes y estudiantes lo ven en cuanto existe.

## Base de datos (carpeta `sql/`)
Ejecuta en SSMS, en este orden, sobre tu servidor: `01_BaseDeDatos.sql` → `02_Usuarios.sql` → `sql/03_Tablas_Horario.sql` → `sql/04_Datos_Iniciales.sql`.
- `03` crea solo las tablas que faltan (incluida `Administrador` si `02` falló por la coma sobrante). No borra nada.
- `04` crea los usuarios para iniciar sesión y datos de ejemplo. Ingreso: **admin / 1234** (gestión). Otros usuarios: clave `Uleam2026*`
  (`gestion@`, `jperez@`, `mmora@`, `csantos@`, `arivas@`, `dcarvajal@`, `mzambrano@` + `live.uleam.edu.ec`; en el login basta la parte antes de la @).
- Ambos se pueden repetir sin duplicar datos. Ojo: el `DELETE FROM Administrador` del final de `02` borra el admin; si vuelves a ejecutar `02`, ejecuta `04` otra vez.

## Puesta en marcha
1. ODBC Driver 18 (o 17) para SQL Server y Python 3.9+. `pip install -r requirements.txt`
2. `config.py`: servidor (`DB_SERVER`), driver (`DB_DRIVER`) y, si no usas autenticación de Windows, usuario y clave.
3. `abrir_puerto_80.bat` (una vez) y `iniciar.bat`, ambos como Administrador.
4. La consola muestra `http://localhost/` y `http://<IP>/` para el resto de la red. Puerto: `PUERTO` en `config.py`.

## Tablas y columnas que lee (todo el SQL está en `consultas.py`)
- `Usuario(id, correoInstitucional, contraseña)` · `Estudiante(id, nombre, apellido, curso, carrera, nivel)` ·
  `Docente(id, nombre, apellido, cedula, especialidad, estado)` · `Gestion_Academica(id, nombre, apellido)` · `Administrador(id, correoInstitucional, contraseña)`
- `Carrera(id, nombre)` — `Estudiante.carrera` debe coincidir con `Carrera.nombre`; `Estudiante.curso` es el paralelo.
- `PeriodoAcademico(id, nombre, activo)` · `Asignatura(id, codigo, nombre, nivel, idCarrera, horasSemanales, idDocente)`
- `Salon(id, numeroDeSalon, nombre, capacidad, tipoSalon, estado)`
- `Horario(id, idPeriodo, idAsignatura, idDocente, idSalon, paralelo, dia 1-5, horaInicio, horaFin)`
Si tus nombres son otros, se cambian solo en `consultas.py`. Las contraseñas pueden estar en texto plano o con hash pbkdf2/scrypt; este sistema nunca las modifica.
Al arrancar avisa si falta alguna tabla.

## Generación de horarios
Bloques de 2 h entre 07:00 y 21:00, sin cruces de docente, salón ni grupo (carrera + nivel + paralelo). Usa el docente de `Asignatura.idDocente`
(si no tiene docente activo, la asignatura se omite y se avisa) y prefiere salones donde caben todos los estudiantes del paralelo.
