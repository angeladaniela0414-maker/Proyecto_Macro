/* Tablas académicas del portal. Seguro de ejecutar varias veces (no borra datos). */
USE BD_Gestion_Horario;
GO

IF OBJECT_ID('dbo.Facultad', 'U') IS NULL
CREATE TABLE dbo.Facultad (
    id INT IDENTITY(1,1) PRIMARY KEY,
    numeroDeFacultad INT NOT NULL UNIQUE,
    nombre VARCHAR(120) NOT NULL
);
GO

IF OBJECT_ID('dbo.Carrera', 'U') IS NULL
CREATE TABLE dbo.Carrera (
    id INT IDENTITY(1,1) PRIMARY KEY,
    codigo INT NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL UNIQUE,   -- debe coincidir con Estudiante.carrera
    idFacultad INT NOT NULL,
    CONSTRAINT FK_Carrera_Facultad FOREIGN KEY (idFacultad) REFERENCES dbo.Facultad(id)
);
GO

IF OBJECT_ID('dbo.PeriodoAcademico', 'U') IS NULL
CREATE TABLE dbo.PeriodoAcademico (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE,
    fechaInicio DATE NOT NULL,
    fechaFin DATE NOT NULL,
    activo BIT NOT NULL DEFAULT 0
);
GO

IF OBJECT_ID('dbo.Asignatura', 'U') IS NULL
CREATE TABLE dbo.Asignatura (
    id INT IDENTITY(1,1) PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(120) NOT NULL,
    nivel INT NOT NULL,
    idCarrera INT NOT NULL,
    horasSemanales INT NOT NULL DEFAULT 4,
    CONSTRAINT FK_Asignatura_Carrera FOREIGN KEY (idCarrera) REFERENCES dbo.Carrera(id)
);
GO

IF OBJECT_ID('dbo.Salon', 'U') IS NULL
CREATE TABLE dbo.Salon (
    id INT IDENTITY(1,1) PRIMARY KEY,
    numeroDeSalon INT NOT NULL,
    nombre VARCHAR(60) NOT NULL UNIQUE,
    capacidad INT NOT NULL,
    tipoSalon VARCHAR(30) NOT NULL DEFAULT 'Aula',          -- Aula | Laboratorio | Auditorio
    estado VARCHAR(20) NOT NULL DEFAULT 'Disponible'        -- Disponible | Mantenimiento
);
GO

IF OBJECT_ID('dbo.Horario', 'U') IS NULL
CREATE TABLE dbo.Horario (
    id INT IDENTITY(1,1) PRIMARY KEY,
    idPeriodo INT NOT NULL,
    idAsignatura INT NOT NULL,
    idDocente INT NULL,
    idSalon INT NULL,
    paralelo VARCHAR(5) NOT NULL,
    dia TINYINT NOT NULL CHECK (dia BETWEEN 1 AND 5),       -- 1 = lunes ... 5 = viernes
    horaInicio TIME(0) NOT NULL,
    horaFin TIME(0) NOT NULL,
    CONSTRAINT CK_Horario_Horas CHECK (horaFin > horaInicio),
    CONSTRAINT UQ_Horario_Bloque UNIQUE (idPeriodo, idAsignatura, paralelo, dia, horaInicio),
    CONSTRAINT FK_Horario_Periodo FOREIGN KEY (idPeriodo) REFERENCES dbo.PeriodoAcademico(id),
    CONSTRAINT FK_Horario_Asignatura FOREIGN KEY (idAsignatura) REFERENCES dbo.Asignatura(id),
    CONSTRAINT FK_Horario_Docente FOREIGN KEY (idDocente) REFERENCES dbo.Docente(id),
    CONSTRAINT FK_Horario_Salon FOREIGN KEY (idSalon) REFERENCES dbo.Salon(id)
);
GO

IF OBJECT_ID('dbo.Tutoria', 'U') IS NULL
CREATE TABLE dbo.Tutoria (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    idDocente INT NOT NULL,
    idAsignatura INT NULL,
    idSalon INT NULL,
    fecha DATE NOT NULL,
    horaInicio TIME(0) NOT NULL,
    horaFin TIME(0) NOT NULL,
    cupo INT NOT NULL DEFAULT 10,
    estado VARCHAR(15) NOT NULL DEFAULT 'Programada',       -- Programada | Cancelada
    CONSTRAINT FK_Tutoria_Docente FOREIGN KEY (idDocente) REFERENCES dbo.Docente(id),
    CONSTRAINT FK_Tutoria_Asignatura FOREIGN KEY (idAsignatura) REFERENCES dbo.Asignatura(id),
    CONSTRAINT FK_Tutoria_Salon FOREIGN KEY (idSalon) REFERENCES dbo.Salon(id)
);
GO

IF OBJECT_ID('dbo.TutoriaSolicitud', 'U') IS NULL
CREATE TABLE dbo.TutoriaSolicitud (
    id INT IDENTITY(1,1) PRIMARY KEY,
    idTutoria INT NOT NULL,
    idEstudiante INT NOT NULL,
    fecha DATETIME NOT NULL DEFAULT GETDATE(),
    estado VARCHAR(15) NOT NULL DEFAULT 'Solicitada',       -- Solicitada | Cancelada
    CONSTRAINT UQ_TutoriaSolicitud UNIQUE (idTutoria, idEstudiante),
    CONSTRAINT FK_TutSol_Tutoria FOREIGN KEY (idTutoria) REFERENCES dbo.Tutoria(id),
    CONSTRAINT FK_TutSol_Estudiante FOREIGN KEY (idEstudiante) REFERENCES dbo.Estudiante(id)
);
GO

IF OBJECT_ID('dbo.Registro', 'U') IS NULL
CREATE TABLE dbo.Registro (
    id INT IDENTITY(1,1) PRIMARY KEY,
    idEstudiante INT NOT NULL,
    idPeriodo INT NOT NULL,
    nivel INT NOT NULL,
    paralelo VARCHAR(5) NOT NULL,
    fechaRegistro DATETIME NOT NULL DEFAULT GETDATE(),
    estado VARCHAR(15) NOT NULL DEFAULT 'Activo',           -- Activo | Anulado
    codigo VARCHAR(40) NULL,
    CONSTRAINT FK_Registro_Estudiante FOREIGN KEY (idEstudiante) REFERENCES dbo.Estudiante(id),
    CONSTRAINT FK_Registro_Periodo FOREIGN KEY (idPeriodo) REFERENCES dbo.PeriodoAcademico(id)
);
GO

IF OBJECT_ID('dbo.SolicitudClave', 'U') IS NULL
CREATE TABLE dbo.SolicitudClave (
    id INT IDENTITY(1,1) PRIMARY KEY,
    correo VARCHAR(120) NOT NULL,
    fecha DATETIME NOT NULL DEFAULT GETDATE(),
    estado VARCHAR(15) NOT NULL DEFAULT 'Pendiente'         -- Pendiente | Atendida | Rechazada
);
GO
