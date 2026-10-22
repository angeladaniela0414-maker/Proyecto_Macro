"""Menú lateral por rol: (endpoint, texto, icono Font Awesome)."""
ESTUDIANTE = [
    ("estudiante.inicio", "Inicio", "fa-house"),
    ("estudiante.horario", "Mi horario", "fa-calendar-days"),
    ("estudiante.registro", "Registro de horario", "fa-calendar-plus"),
    ("estudiante.tutorias", "Mis tutorías", "fa-chalkboard-user"),
    ("comun.salones", "Consulta de salones", "fa-door-open"),
    ("estudiante.comprobantes", "Comprobantes", "fa-file-pdf"),
]
DOCENTE = [
    ("docente.inicio", "Inicio", "fa-house"),
    ("docente.horario", "Mi horario", "fa-calendar-days"),
    ("docente.horarios", "Horarios por nivel", "fa-table-cells"),
    ("docente.tutorias", "Tutorías", "fa-chalkboard-user"),
    ("docente.estudiantes", "Mis estudiantes", "fa-user-graduate"),
    ("comun.salones", "Consulta de salones", "fa-door-open"),
]
GESTION = [
    ("gestor.index", "Panel de gestión", "fa-table-columns"),
]

MENUS = {"estudiante": ESTUDIANTE, "docente": DOCENTE, "gestion": GESTION, "admin": GESTION}
ETIQUETAS = {
    "estudiante": "Portal estudiantil",
    "docente": "Portal docente",
    "gestion": "Gestión académica",
    "admin": "Administración",
}
INICIO = {
    "estudiante": "estudiante.inicio",
    "docente": "docente.inicio",
    "gestion": "gestor.index",
    "admin": "gestor.index",
}
