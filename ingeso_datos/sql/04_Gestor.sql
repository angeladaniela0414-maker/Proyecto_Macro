/* Columnas y tablas que necesita el panel de Gestión Académica. Seguro de ejecutar varias veces. */
USE BD_Gestion_Horario;
GO

/* 02_Usuarios.sql trae una coma sobrante en esta tabla; si no se pudo crear, se crea aquí. */
IF OBJECT_ID('dbo.Administrador', 'U') IS NULL
CREATE TABLE dbo.Administrador (
    id INT PRIMARY KEY,
    correoInstitucional VARCHAR(120) NOT NULL UNIQUE,
    [contraseña] VARCHAR(255) NOT NULL
);
GO

IF COL_LENGTH('dbo.Docente', 'asignatura') IS NULL ALTER TABLE dbo.Docente ADD asignatura VARCHAR(100) NULL;
GO
IF COL_LENGTH('dbo.Estudiante', 'cedula') IS NULL ALTER TABLE dbo.Estudiante ADD cedula VARCHAR(10) NULL;
GO
IF COL_LENGTH('dbo.Estudiante', 'codigoRegistro') IS NULL ALTER TABLE dbo.Estudiante ADD codigoRegistro INT NULL;
GO
IF COL_LENGTH('dbo.Estudiante', 'asignatura') IS NULL ALTER TABLE dbo.Estudiante ADD asignatura VARCHAR(100) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_Estudiante_cedula')
    CREATE UNIQUE INDEX UX_Estudiante_cedula ON dbo.Estudiante(cedula) WHERE cedula IS NOT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_Estudiante_codigoRegistro')
    CREATE UNIQUE INDEX UX_Estudiante_codigoRegistro ON dbo.Estudiante(codigoRegistro) WHERE codigoRegistro IS NOT NULL;
GO

/* Docente titular de cada asignatura (lo usa la generación automática de horarios). */
IF COL_LENGTH('dbo.Asignatura', 'idDocente') IS NULL
    ALTER TABLE dbo.Asignatura ADD idDocente INT NULL
        CONSTRAINT FK_Asignatura_Docente FOREIGN KEY REFERENCES dbo.Docente(id);
GO
