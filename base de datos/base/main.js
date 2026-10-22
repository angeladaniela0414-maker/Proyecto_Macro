document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    
    // Cargar la primera sección por defecto
    cargarSeccion('generacion_horarios');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            const seccion = item.getAttribute('data-section');
            cargarSeccion(seccion);
        });
    });
});

async function cargarSeccion(nombreSeccion) {
    const mainContent = document.getElementById('main-content');
    try {
        const res = await fetch(`/seccion/${nombreSeccion}`);
        if (res.ok) {
            const html = await res.text();
            mainContent.innerHTML = html;
            
            // Ejecutar JS específico si carga la sección de horarios
            if (nombreSeccion === 'generacion_horarios') {
                const script = document.createElement('script');
                script.src = '/static/js/generacion_horarios.js';
                document.body.appendChild(script);
            }
        } else {
            mainContent.innerHTML = '<h2>Error al cargar la sección</h2>';
        }
    } catch (err) {
        console.error('Error:', err);
    }
}