from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from conexion_db import obtener_conexion

app = Flask(__name__)
app.secret_key = 'clave_secreta_uleam'

# Route: Página de Login
@app.route('/')
@app.route('/login')
def login():
    return render_template('login.html')

# API: Validar Credenciales
@app.route('/api/login', methods=['POST'])
def api_login():
    datos = request.json
    usuario = datos.get('usuario')
    password = datos.get('password')

    conn = obtener_conexion()
    if not conn:
        return jsonify({'success': False, 'message': 'Error de conexión con la base de datos'}), 500

    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, usuario FROM Usuarios WHERE usuario = ? AND password = ?", (usuario, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user[0]
        session['user_nombre'] = user[1]
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos'}), 401

# Route: Dashboard Principal
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', usuario=session.get('user_nombre'))

# API: Carga dinámica de secciones HTML
@app.route('/seccion/<nombre>')
def cargar_seccion(nombre):
    secciones_permitidas = [ 'gestion_salones', 'consultar_docentes', 'asignaturas' ]
    if nombre in secciones_permitidas:
        return render_template(f'secciones/{nombre}.html')
    return "<p>Sección no encontrada</p>", 404

# API: Obtener Horarios desde SQL Server
@app.route('/api/horarios', methods=['GET'])
def obtener_horarios():
    conn = obtener_conexion()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.dia, h.hora_inicio, h.hora_fin, a.nombre AS asignatura, d.nombre AS docente, s.nombre AS salon
        FROM Horarios h
        INNER JOIN Asignaturas a ON h.asignatura_id = a.id
        INNER JOIN Docentes d ON h.docente_id = d.id
        INNER JOIN Salones s ON h.salon_id = s.id
    """)
    filas = cursor.fetchall()
    conn.close()

    resultado = [
        {
            "dia": row[0],
            "hora": f"{row[1]} - {row[2]}",
            "asignatura": row[3],
            "docente": row[4],
            "salon": row[5]
        }
        for row in filas
    ]
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(debug=True)