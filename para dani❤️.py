import math
import random
import time
import tkinter as tk

FONDO = "#24401f"
AMARILLOS = ["#ffd23f", "#ffc61a", "#ffe066", "#ffb703", "#fcd34d"]
TARJETA = "#fffbea"
TEXTO = "#4a3200"
MANTENER_BOTON = 2.0
ZONA_ABAJO = 90
def mezclar(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
class App:
    def __init__(self, root):
        self.root = root
        root.title("Flores para Daniela")
        root.geometry("1000x700")
        root.minsize(500, 400)

        self.c = tk.Canvas(root, bg=FONDO, highlightthickness=0, cursor="crosshair")
        self.c.pack(fill="both", expand=True)
        self.contador = 0
        self.gen = 0
        self.corriendo = False
        self.tarjeta_bbox = None
        self.boton = tk.Button(
            
            root, text="Presionar para una sorpresa", font=("Georgia", 14, "bold"),
            bg="#ffd23f", fg=TEXTO, activebackground="#ffe066", relief="flat",
            padx=22, pady=10, cursor="hand2", command=self.sorpresa)
        self.ult_visto = 0.0
        self.by = 2000.0
        self.hint = None
        self.boton_win = None
        self.crear_base()

        self.c.bind("<Button-1>", self.clic)
        self.c.bind("<Configure>", self.reubicar)
        root.bind("<F11>", lambda e: root.attributes("-fullscreen", not root.attributes("-fullscreen")))
        root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
        self.vigilar()

    def crear_base(self):
        w = max(self.c.winfo_width(), 1000)
        self.hint = self.c.create_text(
            w / 2, 30, text="Haz clic en cualquier parte de la pantalla",
            fill="#fff8e1", font=("Georgia", 16), tags="hint")
        self.boton_win = self.c.create_window(w / 2, self.by, window=self.boton, anchor="s")
    def reubicar(self, e=None):
        w = self.c.winfo_width()
        self.c.coords(self.hint, w / 2, 30)
        self.c.coords(self.boton_win, w / 2, self.by)
    def vigilar(self):
        w, h = self.c.winfo_width(), self.c.winfo_height()
        px = self.root.winfo_pointerx() - self.c.winfo_rootx()
        py = self.root.winfo_pointery() - self.c.winfo_rooty()
        en_zona = (0 <= px <= w) and (h - ZONA_ABAJO <= py <= h + 5)
        sobre_boton = (self.by < h) and (abs(px - w / 2) < 170) and (h - 80 <= py <= h)
        if en_zona or sobre_boton:
            self.ult_visto = time.time()
        visible = (time.time() - self.ult_visto < MANTENER_BOTON) and not self.corriendo
        objetivo = (h - 25) if visible else (h + 80)
        self.by += (objetivo - self.by) * 0.25
        if abs(objetivo - self.by) < 0.5:
            self.by = objetivo
        self.c.coords(self.boton_win, w / 2, self.by)
        self.root.after(40, self.vigilar)

    def dibujar_flor(self, x, y, tam, n, color, rot, tags, escala=1.0, fade=0.0, base=FONDO):
        s = tam * escala
        if s < 1:
            return
        relleno = mezclar(color, base, fade)
        borde = mezclar("#e0a000", base, fade)
        a, b, r0 = 0.20 * s, 0.30 * s, 0.30 * s
        for k in range(n):
            ang = rot + k * 2 * math.pi / n
            ca, sa = math.cos(ang), math.sin(ang)
            pts = []
            for t in range(0, 360, 45):
                lx = a * math.cos(math.radians(t))
                ly = r0 + b * math.sin(math.radians(t))
                pts += [x + lx * ca - ly * sa, y + lx * sa + ly * ca]
            self.c.create_polygon(pts, fill=relleno, outline=borde, smooth=True, tags=tags)
        self.c.create_oval(x - 0.13 * s, y - 0.13 * s, x + 0.13 * s, y + 0.13 * s,
                           fill=mezclar("#8a4b08", base, fade), outline="", tags=tags)
        self.c.create_oval(x - 0.07 * s, y - 0.09 * s, x - 0.01 * s, y - 0.03 * s,
                           fill=mezclar("#b8741a", base, fade), outline="", tags=tags)
        if self.tarjeta_bbox:
            self.c.tag_raise("tarjeta")
    def florecer(self, x, y, tam, retraso=0, efimera=False):
        self.contador += 1
        tag = f"f{self.contador}"
        n = random.choice([5, 6])
        color = random.choice(AMARILLOS)
        rot0 = random.uniform(0, math.tau)
        gen = self.gen
        pasos, pasos_fade = 6, 8
        def crecer(i=1):
            if gen != self.gen:
                return
            self.c.delete(tag)
            esc = 1 - (1 - i / pasos) ** 3
            esc *= 1 + 0.12 * math.sin(math.pi * i / pasos)
            self.dibujar_flor(x, y, tam, n, color, rot0 + (1 - i / pasos) * 1.2, tag, esc)
            if i < pasos:
                self.root.after(30, crecer, i + 1)
            elif efimera:
                self.root.after(1000, desvanecer)
        def desvanecer(j=1):
            if gen != self.gen:
                return
            self.c.delete(tag)
            if j >= pasos_fade:
                return
            f = j / pasos_fade
            self.dibujar_flor(x, y, tam, n, color, rot0, tag, 1 - 0.25 * f, fade=f)
            self.root.after(40, desvanecer, j + 1)
        self.root.after(int(retraso), crecer)
    def clic(self, e):
        if self.tarjeta_bbox:
            x1, y1, x2, y2 = self.tarjeta_bbox
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                return
        self.c.delete("hint")
        self.florecer(e.x, e.y, random.uniform(50, 100), 0, efimera=True)
    def sorpresa(self):
        if self.corriendo:
            return
        self.corriendo = True
        self.c.delete("hint")
        w, h = self.c.winfo_width(), self.c.winfo_height()
        banda = max(80, min(w, h) * 0.20)
        total = int(min(90, max(50, (w + h) / 14)))
        puntos = []
        for _ in range(total):
            lado = random.randint(0, 3)
            d = (random.random() ** 1.6) * banda
            if lado == 0:
                p = (random.uniform(0, w), d)
            elif lado == 1:
                p = (random.uniform(0, w), h - d)
            elif lado == 2:
                p = (d, random.uniform(0, h))
            else:
                p = (w - d, random.uniform(0, h))
            puntos.append((p[0], p[1], d))
        puntos.sort(key=lambda p: p[2])
        duracion = 2200
        for i, (x, y, _) in enumerate(puntos):
            self.florecer(x, y, random.uniform(65, 125),
                          retraso=i / total * duracion + random.uniform(0, 150))
        self.root.after(duracion + 500, self.mostrar_tarjeta)
    def mostrar_tarjeta(self):
        gen = self.gen
        w, h = self.c.winfo_width(), self.c.winfo_height()
        cx, cy = w / 2, h / 2
        tw, th = min(460, w - 60), min(300, h - 60)
        pasos = 12
        def rect(x1, y1, x2, y2, r, **kw):
            pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
                   x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
            return self.c.create_polygon(pts, smooth=True, tags="tarjeta", **kw)
        def crecer(i=1):
            if gen != self.gen:
                return
            self.c.delete("tarjeta")
            f = 1 - (1 - i / pasos) ** 3
            hw, hh = tw / 2 * f, th / 2 * f
            rect(cx - hw - 6, cy - hh - 6, cx + hw + 6, cy + hh + 6, 30, fill="#ffd23f", outline="")
            rect(cx - hw, cy - hh, cx + hw, cy + hh, 26, fill=TARJETA, outline="")
            self.tarjeta_bbox = (cx - hw, cy - hh, cx + hw, cy + hh)
            if i < pasos:
                self.root.after(30, crecer, i + 1)
            else:
                self.aparecer_mensaje(cx, cy, th)
        crecer()
    def aparecer_mensaje(self, cx, cy, th):
        gen = self.gen
        lineas = [
            (-th * 0.12, "Para Daniela", ("Georgia", 20)),
            (th * 0.06, "la más hermosa", ("Georgia", 36, "italic")),
            (th * 0.24, "Estas flores son todas para ti.", ("Georgia", 14)),
        ]
        ids = [self.c.create_text(cx, cy + dy, text=txt, fill=TARJETA, font=fuente, tags="tarjeta")
               for dy, txt, fuente in lineas]
        n_flor = random.choice([6, 7])
        rot_flor = random.uniform(0, math.tau)
        pos_flor = (cx, cy - th * 0.30)
        paso_retraso, duracion, total = 6, 12, 6 * 3 + 12
        def progreso(i, k):
            return min(1.0, max(0.0, (i - k * paso_retraso) / duracion))
        def animar(i=1):
            if gen != self.gen:
                return
            for k, item in enumerate(ids, start=1):
                p = progreso(i, k)
                self.c.itemconfigure(item, fill=mezclar(TARJETA, TEXTO, p * p * (3 - 2 * p)))
            self.c.delete("flortarj")
            p0 = progreso(i, 0)
            self.dibujar_flor(pos_flor[0], pos_flor[1], 46, n_flor, "#ffc61a", rot_flor,
                              ("tarjeta", "flortarj"), fade=1 - p0 * p0 * (3 - 2 * p0), base=TARJETA)
            if i < total:
                self.root.after(40, animar, i + 1)
            else:
                self.poner_cerrar(cx, cy, th)

        animar()
    def poner_cerrar(self, cx, cy, th):
        b = tk.Button(self.root, text="Cerrar", font=("Georgia", 12, "bold"), bg=TARJETA,
                      fg=TEXTO, relief="solid", bd=2, padx=14, pady=2, cursor="hand2",
                      command=self.cerrar)
        self.c.create_window(cx, cy + th * 0.39, window=b, tags="tarjeta")
        self.c.tag_raise("tarjeta")

    def cerrar(self):
        self.gen += 1
        self.c.delete("all")
        self.tarjeta_bbox = None
        self.corriendo = False
        self.crear_base()

if __name__ == "__main__":
    ventana = tk.Tk()
    App(ventana)
    ventana.mainloop()