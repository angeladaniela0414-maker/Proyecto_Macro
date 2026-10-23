const formulario = document.getElementById("formLogin");
const mensaje = document.getElementById("errorLogin");

if (formulario && mensaje) {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const correo = formulario.elements["correo"].value.trim();
    const contrasena = formulario.elements["contrasena"].value;
    mensaje.hidden = false;
    mensaje.textContent = "Comprobando las credenciales...";

    try {
      const respuesta = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ correo, contrasena })
      });
      const datos = await respuesta.json();
      if (!respuesta.ok) {
        mensaje.textContent = datos.detail || "No se pudo iniciar sesión.";
        return;
      }
      window.location.href = datos.redirect;
    } catch (error) {
      mensaje.textContent = "No se pudo conectar con el servidor. Comprueba la conexión e inténtalo otra vez.";
      console.error(error);
    }
  });

  const botonVer = document.getElementById("verClave");
  const campoClave = document.getElementById("contrasena");
  if (botonVer && campoClave) {
    botonVer.addEventListener("click", () => {
      const visible = campoClave.type === "text";
      campoClave.type = visible ? "password" : "text";
      botonVer.textContent = visible ? "Mostrar" : "Ocultar";
    });
  }
  const abrirAyuda = document.getElementById("abrirAyuda");
  const modalAyuda = document.getElementById("modalAyuda");
  if (abrirAyuda && modalAyuda) {
    abrirAyuda.addEventListener("click", (e) => { e.preventDefault(); modalAyuda.hidden = false; });
    modalAyuda.querySelectorAll("[data-cerrar]").forEach((b) => b.addEventListener("click", () => { modalAyuda.hidden = true; }));
  }
}
