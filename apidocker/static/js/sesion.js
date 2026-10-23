// El botón debe tener el atributo data-salir.
document.querySelectorAll("[data-salir]").forEach((boton) => {
  boton.addEventListener("click", async () => {
    boton.disabled = true;
    try {
      const respuesta = await fetch("/api/logout", {
        method: "POST",
        credentials: "same-origin",
        cache: "no-store"
      });

      if (!respuesta.ok) {
        throw new Error("El servidor no pudo cerrar la sesión.");
      }

      window.location.replace("/");
    } catch (error) {
      boton.disabled = false;
      alert("No se pudo cerrar la sesión. Comprueba la conexión e inténtalo de nuevo.");
      console.error(error);
    }
  });
});
