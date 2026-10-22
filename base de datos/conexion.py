import pyodbc

# Configuración de los parámetros de conexión
DB_SERVER = 'localhost'  # O el nombre de tu instancia, p. ej. 'LOCALHOST\\SQLEXPRESS'
DB_NAME = 'GestionAcademicaDB'
DB_USER = 'tu_usuario'
DB_PASSWORD = 'tu_password'

def obtener_conexion():
    try:
        # Cadena de conexión para SQL Server
        string_conexion = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD};"
        )
        conexion = pyodbc.connect(string_conexion)
        return conexion
    except Exception as ex:
        print(f"Error al conectar a SQL Server: {ex}")
        return None