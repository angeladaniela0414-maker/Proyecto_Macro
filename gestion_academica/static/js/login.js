const $ = (id) => document.getElementById(id);

async function ingresar() {
  $("mensaje").textContent = "";
  try {
    const r = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ usuario: $("usuario").value.trim(), clave: $("clave").value }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "No se pudo ingresar");
    window.location.href = "/index";
  } catch (e) {
    $("mensaje").textContent = e.message;
  }
}

$("btnIngresar").addEventListener("click", ingresar);
document.addEventListener("keydown", (e) => { if (e.key === "Enter") ingresar(); });
