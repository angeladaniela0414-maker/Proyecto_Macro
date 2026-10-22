/* ============================================================================
   04_Datos_Iniciales.sql
   Ejecutar DESPUÉS de 03_Tablas_Horario.sql. Se puede repetir: no duplica nada.

   1) Usuarios para iniciar sesión (las contraseñas se guardan cifradas, no en texto plano):
        admin                          / 1234         -> Gestión (Administrador)
        gestion@live.uleam.edu.ec  / Uleam2026*   -> Gestión académica
        jperez@, mmora@, csantos@, arivas@ ...        -> Docentes      / Uleam2026*
        dcarvajal@, mzambrano@ ...                    -> Estudiantes   / Uleam2026*
      En el login basta escribir la parte anterior a la @ (por ejemplo: jperez).
   2) Datos de ejemplo (carrera, período, asignaturas, salones) para poder generar
      un horario enseguida. Si ya los carga tu programa de ingreso de datos, esta
      parte no hace falta; se omite sola lo que ya exista.
   ============================================================================ */
USE BD_Gestion_Horario;
GO
SET NOCOUNT ON;

DECLARE @id INT;

/* ---------- Administrador ---------- */
IF NOT EXISTS (SELECT 1 FROM Administrador WHERE correoInstitucional = 'admin')
    INSERT INTO Administrador (id, correoInstitucional, [contraseña])
    SELECT ISNULL(MAX(id), 0) + 1, 'admin', 'pbkdf2:sha256:1000000$iOtU96A3wXzS45lu$52924e6f6e9bd2664ed2fbe606eea8fef29335669a5cefd06dd24cb0174e3177' FROM Administrador;

/* ---------- Gestión académica ---------- */
IF NOT EXISTS (SELECT 1 FROM Usuario WHERE correoInstitucional = 'gestion@live.uleam.edu.ec')
BEGIN
    SET @id = (SELECT ISNULL(MAX(id), 0) + 1 FROM Usuario);
    INSERT INTO Usuario (id, correoInstitucional, [contraseña]) VALUES (@id, 'gestion@live.uleam.edu.ec', 'pbkdf2:sha256:1000000$79wRoMJiBVTm7OZU$0fb461a1f50eca929fbcb798f7f58ed95e418662b6de86638cda100004338f45');
    INSERT INTO Gestion_Academica (id, nombre, apellido, facultad, carrera, cargo)
    VALUES (@id, N'Laura', N'Vera', N'Facultad de Ciencias Informáticas', N'Ingeniería en Software', N'Coordinadora académica');
END

/* ---------- Docentes ---------- */
IF NOT EXISTS (SELECT 1 FROM Usuario WHERE correoInstitucional = 'jperez@live.uleam.edu.ec')
BEGIN
    SET @id = (SELECT ISNULL(MAX(id), 0) + 1 FROM Usuario);
    INSERT INTO Usuario (id, correoInstitucional, [contraseña]) VALUES (@id, 'jperez@live.uleam.edu.ec', 'pbkdf2:sha256:1000000$79wRoMJiBVTm7OZU$0fb461a1f50eca929fbcb798f7f58ed95e418662b6de86638cda100004338f45');
    INSERT INTO Docente (id, cedula, nombre, apellido, especialidad, nivel, estado)
    VALUES (@id, '1300000001', N'Juan', N'Pérez', N'Programación', 4, 1);
END
IF NOT EXISTS (SELECT 1 FROM Usuario WHERE correoInstitucional = 'mmora@live.uleam.edu.ec')
BEGIN
    SET @id = (SELECT ISNULL(MAX(id), 0) + 1 FROM Usuario);
    INSERT INTO Usuario (id, correoInstitucional, [contraseña]) VALUES (@id, 'mmora@live.uleam.edu.ec', 'pbkdf2:sha256:1000000$79wRoMJiBVTm7OZU$0fb461a1f50eca929fbcb798f7f58ed95e418662b6de86638cda100004338f45');
    INSERT INTO Docente (id, cedula, nombre, apellido, especialidad, nivel, estado)
    VALUES (@id, '1300000002', N'María', N'Mora', N'Bases de datos', 4, 1);
END
IF NOT EXISTS (SELECT 1 FROM Usuario WHERE correoInstitucional = 'csantos@live.uleam.edu.ec')
BEGIN
    SET @id = (SELECT ISNULL(MAX(id), 0) + 1 FROM Usuario);
    INSERT INTO Usuario (id, correoInstitucional, [contraseña]) VALUES (@id, 'csantos@live.uleam.edu.ec', 'pbkdf2:sha256:1000000$79wRoMJiBVTm7OZU$0fb461a1f50eca929fbcb798f7f58ed95e418662b6de86638cda100004338f45');
    INSERT INTO Docente (id, cedula, nombre, apellido, especialidad, nivel, estado)
    VALUES (@id, '1300000003', N'Carlos', N'Santos', N'Sistemas operativos', 4, 1);
END
IF NOT EXISTS (SELECT 1 FROM Usuario WHERE correoInstitucional = 'arivas@live.uleam.edu.ec')
BEGIN
    SET @id = (SELECT ISNULL(MAX(id), 0) + 1 FROM Usuario);
    INSERT INTO Usuario (id, correoInstitucional, [contraseña]) VALUES (@id, 'arivas@live.uleam.edu.ec', 'pbkdf2:sha256:1000000$79wRoMJiBVTm7OZU$0fb461a1f50eca929fbcb798f7f58ed95e418662b6de86638cda100004338f45');
    INSERT INTO Docente (id, cedula, nombre, apellido, especialidad, nivel, estado)
    VALUES (@id, '1300000004', N'Ana', N'Rivas', N'Redes', 4, 1);
END

/* ---------- Estudiantes ---------- */
IF NOT EXISTS (SELECT 1 FROM Usuario WHERE correoInstitucional = 'dcarvajal@live.uleam.edu.ec')
BEGIN
    SET @id = (SELECT ISNULL(MAX(id), 0) + 1 FROM Usuario);
    INSERT INTO Usuario (id, correoInstitucional, [contraseña]) VALUES (@id, 'dcarvajal@live.uleam.edu.ec', 'pbkdf2:sha256:1000000$79wRoMJiBVTm7OZU$0fb461a1f50eca929fbcb798f7f58ed95e418662b6de86638cda100004338f45');
    INSERT INTO Estudiante (id, correoInstitucional, nombre, apellido, curso, carrera, nivel)
    VALUES (@id, 'dcarvajal@live.uleam.edu.ec', N'Daniela', N'Carvajal', 'A', N'Ingeniería en Software', 4);
END
IF NOT EXISTS (SELECT 1 FROM Usuario WHERE correoInstitucional = 'mzambrano@live.uleam.edu.ec')
BEGIN
    SET @id = (SELECT ISNULL(MAX(id), 0) + 1 FROM Usuario);
    INSERT INTO Usuario (id, correoInstitucional, [contraseña]) VALUES (@id, 'mzambrano@live.uleam.edu.ec', 'pbkdf2:sha256:1000000$79wRoMJiBVTm7OZU$0fb461a1f50eca929fbcb798f7f58ed95e418662b6de86638cda100004338f45');
    INSERT INTO Estudiante (id, correoInstitucional, nombre, apellido, curso, carrera, nivel)
    VALUES (@id, 'mzambrano@live.uleam.edu.ec', N'Mateo', N'Zambrano', 'B', N'Ingeniería en Software', 4);
END

/* ---------- Datos de ejemplo: facultad, carrera, período ---------- */
IF NOT EXISTS (SELECT 1 FROM Facultad WHERE numeroDeFacultad = 1)
    INSERT INTO Facultad (numeroDeFacultad, nombre) VALUES (1, N'Facultad de Ciencias Informáticas');

IF NOT EXISTS (SELECT 1 FROM Carrera WHERE nombre = N'Ingeniería en Software')
    INSERT INTO Carrera (codigo, nombre, idFacultad)
    SELECT ISNULL((SELECT MAX(codigo) FROM Carrera), 100) + 1, N'Ingeniería en Software', (SELECT TOP 1 id FROM Facultad ORDER BY id);

IF NOT EXISTS (SELECT 1 FROM PeriodoAcademico WHERE nombre = '2026-1')
    INSERT INTO PeriodoAcademico (nombre, fechaInicio, fechaFin, activo) VALUES ('2026-1', '2026-04-20', '2026-09-04', 1);

/* ---------- Asignaturas de 4.º nivel (con su docente titular) ---------- */
DECLARE @carrera INT = (SELECT id FROM Carrera WHERE nombre = N'Ingeniería en Software');
IF NOT EXISTS (SELECT 1 FROM Asignatura WHERE codigo = 'SOF-401')
    INSERT INTO Asignatura (codigo, nombre, nivel, idCarrera, horasSemanales, idDocente)
    VALUES ('SOF-401', N'Programación Orientada a Objetos', 4, @carrera, 4, (SELECT id FROM Usuario WHERE correoInstitucional = 'jperez@live.uleam.edu.ec'));
IF NOT EXISTS (SELECT 1 FROM Asignatura WHERE codigo = 'SOF-402')
    INSERT INTO Asignatura (codigo, nombre, nivel, idCarrera, horasSemanales, idDocente)
    VALUES ('SOF-402', N'Base de Datos Relacionales', 4, @carrera, 4, (SELECT id FROM Usuario WHERE correoInstitucional = 'mmora@live.uleam.edu.ec'));
IF NOT EXISTS (SELECT 1 FROM Asignatura WHERE codigo = 'SOF-403')
    INSERT INTO Asignatura (codigo, nombre, nivel, idCarrera, horasSemanales, idDocente)
    VALUES ('SOF-403', N'Redes y Conectividad I', 4, @carrera, 4, (SELECT id FROM Usuario WHERE correoInstitucional = 'arivas@live.uleam.edu.ec'));
IF NOT EXISTS (SELECT 1 FROM Asignatura WHERE codigo = 'SOF-404')
    INSERT INTO Asignatura (codigo, nombre, nivel, idCarrera, horasSemanales, idDocente)
    VALUES ('SOF-404', N'Sistemas Operativos', 4, @carrera, 4, (SELECT id FROM Usuario WHERE correoInstitucional = 'csantos@live.uleam.edu.ec'));
IF NOT EXISTS (SELECT 1 FROM Asignatura WHERE codigo = 'SOF-405')
    INSERT INTO Asignatura (codigo, nombre, nivel, idCarrera, horasSemanales, idDocente)
    VALUES ('SOF-405', N'Ingeniería de Software II', 4, @carrera, 4, (SELECT id FROM Usuario WHERE correoInstitucional = 'jperez@live.uleam.edu.ec'));

/* ---------- Salones ---------- */
IF NOT EXISTS (SELECT 1 FROM Salon WHERE nombre = N'Aula 102') INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) VALUES (102, N'Aula 102', 40, 'Aula');
IF NOT EXISTS (SELECT 1 FROM Salon WHERE nombre = N'Aula 201') INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) VALUES (201, N'Aula 201', 40, 'Aula');
IF NOT EXISTS (SELECT 1 FROM Salon WHERE nombre = N'Aula 204') INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) VALUES (204, N'Aula 204', 35, 'Aula');
IF NOT EXISTS (SELECT 1 FROM Salon WHERE nombre = N'Aula 205') INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) VALUES (205, N'Aula 205', 35, 'Aula');
IF NOT EXISTS (SELECT 1 FROM Salon WHERE nombre = N'Lab 1 - FCI') INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) VALUES (1, N'Lab 1 - FCI', 30, 'Laboratorio');
IF NOT EXISTS (SELECT 1 FROM Salon WHERE nombre = N'Lab 2 - FCI') INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) VALUES (2, N'Lab 2 - FCI', 30, 'Laboratorio');
IF NOT EXISTS (SELECT 1 FROM Salon WHERE nombre = N'Lab 3 - FCI') INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) VALUES (3, N'Lab 3 - FCI', 30, 'Laboratorio');
IF NOT EXISTS (SELECT 1 FROM Salon WHERE nombre = N'Lab Redes') INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) VALUES (4, N'Lab Redes', 25, 'Laboratorio');

PRINT 'Datos iniciales listos. Usuario de gestión: admin / 1234';
GO

SELECT 'Administrador' AS tabla, COUNT(*) AS filas FROM Administrador
UNION ALL SELECT 'Usuario', COUNT(*) FROM Usuario
UNION ALL SELECT 'Docente', COUNT(*) FROM Docente
UNION ALL SELECT 'Estudiante', COUNT(*) FROM Estudiante
UNION ALL SELECT 'Asignatura', COUNT(*) FROM Asignatura
UNION ALL SELECT 'Salon', COUNT(*) FROM Salon;
GO
