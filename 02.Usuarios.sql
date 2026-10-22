USE BD_Gestion_Horario;
GO

CREATE TABLE Usuario (
    id INT PRIMARY KEY,
    correoInstitucional VARCHAR(120) NOT NULL UNIQUE,
    contraseña VARCHAR(255) NOT NULL
);
GO

CREATE TABLE Gestion_Academica (
    id INT PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL,
    apellido VARCHAR(80) NOT NULL,
    facultad VARCHAR(100),
    carrera VARCHAR(100),
    cargo VARCHAR(80),

    CONSTRAINT FK_Gestion_Academica_Usuario
    FOREIGN KEY (id) REFERENCES Usuario(id)
);
GO

CREATE TABLE Docente (
    id INT PRIMARY KEY,
    cedula VARCHAR(10) NOT NULL UNIQUE,
    nombre VARCHAR(80) NOT NULL,
    apellido VARCHAR(80) NOT NULL,
    especialidad VARCHAR(100),
    nivel INT,
    estado BIT,

    CONSTRAINT FK_Docente_Usuario
    FOREIGN KEY (id) REFERENCES Usuario(id)
);
GO

CREATE TABLE Estudiante (
    id INT PRIMARY KEY,
    correoInstitucional VARCHAR(120) NOT NULL UNIQUE,
    nombre VARCHAR(80) NOT NULL,
    apellido VARCHAR(80) NOT NULL,
    curso VARCHAR(30),
    carrera VARCHAR(100),
    nivel INT,

    CONSTRAINT FK_Estudiante_Usuario
    FOREIGN KEY (id) REFERENCES Usuario(id)
);
GO

CREATE TABLE Administrador (
    id INT PRIMARY KEY,
    correoInstitucional VARCHAR(120) NOT NULL UNIQUE,
    contraseña VARCHAR(255) NOT NULL,
);
GO

INSERT INTO Administrador
    (id, correoInstitucional, contraseña)
VALUES
    (1, 'Admin@live.uleam.edu.ec', 'admin1234');

SELECT * FROM Administrador

DELETE FROM Administrador;