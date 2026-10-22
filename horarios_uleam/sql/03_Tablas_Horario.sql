/* ============================================================================
   03_Tablas_Horario.sql
   Continúa 01_BaseDeDatos.sql y 02_Usuarios.sql (SQL Server 2022).
   Crea SOLO las tablas que faltan. No borra nada y se puede ejecutar varias veces.
   Orden de ejecución:  01  ->  02  ->  03  ->  04_Datos_Iniciales.sql
   ============================================================================ */
USE BD_Gestion_Horario;
GO

/* 02_Usuarios.sql tiene una coma sobrante en CREATE TABLE Administrador y por eso falla.
   Si esa tabla no quedó creada, se crea aquí correctamente. */
IF OBJECT_ID('dbo.Administrador', 'U') IS NULL
CREATE TABLE dbo.Administrador (
    id INT PRIMARY KEY,
    correoInstitucional VARCHAR(120) NOT NULL UNIQUE,
    [contraseña] VARCHAR(255) NOT NULL
);
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
    nombre VARCHAR(100) NOT NULL UNIQUE,          -- debe coincidir con Estudiante.carrera
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
    idDocente INT NULL,                           -- docente titular (lo usa la generación de horarios)
    CONSTRAINT FK_Asignatura_Carrera FOREIGN KEY (idCarrera) REFERENCES dbo.Carrera(id),
    CONSTRAINT FK_Asignatura_Docente FOREIGN KEY (idDocente) REFERENCES dbo.Docente(id)
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

/* Si Asignatura ya existía de antes sin docente titular, se agrega la columna. */
IF COL_LENGTH('dbo.Asignatura', 'idDocente') IS NULL
    ALTER TABLE dbo.Asignatura ADD idDocente INT NULL
        CONSTRAINT FK_Asignatura_Docente FOREIGN KEY REFERENCES dbo.Docente(id);
GO

PRINT 'Tablas listas.';
GO
