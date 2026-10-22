from abc import ABC, abstractmethod

class Producto:
    def __init__(self, id_prod: int, nombre: str, precio: float, stock: int, categoria: str):
        self.id_prod = id_prod
        self._nombre = nombre
        self._precio = precio
        self.stock = stock
        self.categoria = categoria

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, nuevo_nombre: str):
        if nuevo_nombre.strip():
            self._nombre = nuevo_nombre

    @property
    def precio(self) -> float:
        return self._precio

    @precio.setter
    def precio(self, valor: float):
        if valor >= 0:
            self._precio = valor

    def __str__(self):
        return f"[{self.id_prod}] {self._nombre} | Categoría: {self.categoria} | Precio: ${self._precio:.2f} | Stock: {self.stock}"


class Carrito:
    def __init__(self):
        self.items = []  # Lista de tuplas: (Producto, cantidad)

    # Sobrecarga del operador '+' para añadir un producto al carrito
    def __add__(self, tupla_item):
        producto, cantidad = tupla_item
        for idx, (prod, qty) in enumerate(self.items):
            if prod.id_prod == producto.id_prod:
                self.items[idx] = (prod, qty + cantidad)
                return self
        self.items.append((producto, cantidad))
        return self

    def total(self) -> float:
        return sum(prod.precio * qty for prod, qty in self.items)

    def vaciar(self):
        self.items.clear()


# ==========================================
# 2. PASARELAS DE PAGO (INYECCIÓN DE DEPENDENCIAS)
# ==========================================

class PasarelaPago(ABC):
    @abstractmethod
    def pagar(self, monto: float) -> bool:
        pass

class PayPal(PasarelaPago):
    def pagar(self, monto: float) -> bool:
        print(f"\n[PayPal] Transacción procesada con éxito por un total de: ${monto:.2f}")
        return True

class Stripe(PasarelaPago):
    def pagar(self, monto: float) -> bool:
        print(f"\n[Stripe] Cobro a tarjeta procesado con éxito por un total de: ${monto:.2f}")
        return True


class Pedido:
    def __init__(self, id_pedido: int, cliente, pasarela: PasarelaPago):
        self.id_pedido = id_pedido
        self.cliente = cliente
        self.pasarela = pasarela
        self.items = list(cliente.carrito.items)
        self.total = cliente.carrito.total()

    def procesar_pago(self) -> bool:
        if self.total == 0:
            print("❌ El carrito está vacío.")
            return False

        # Descontar el stock de cada producto
        for prod, qty in self.items:
            if prod.stock < qty:
                print(f"❌ Stock insuficiente para '{prod.nombre}'. Disponible: {prod.stock}")
                return False

        exito = self.pasarela.pagar(self.total)
        if exito:
            for prod, qty in self.items:
                prod.stock -= qty
            self.cliente.carrito.vaciar()
            print(f"✅ Pedido #{self.id_pedido} registrado y pagado correctamente.")
            return True
        return False

    def __str__(self):
        res = f"📦 Pedido #{self.id_pedido} - Cliente: {self.cliente.nombre} - Total: ${self.total:.2f}\n"
        for p, q in self.items:
            res += f"   • {p.nombre} x{q} (${p.precio * q:.2f})\n"
        return res


# ==========================================
# 3. ROLES DE USUARIO
# ==========================================

class Administrador:
    def __init__(self, nombre="Daniela Carvajal"):
        self.nombre = nombre

    def mostrar_menu(self):
        print(f"\n-------- Bienvenido a la tienda de {self.nombre} (Administrador) --------")
        print("1. Crear cliente")
        print("2. Crear producto")
        print("3. Crear categoría")
        print("4. Modificar categoría")
        print("5. Modificar producto")
        print("6. Eliminar producto")
        print("7. Visualizar pedidos")
        print("0. Salir")

    def ejecutar_opcion(self, opcion, tienda):
        if opcion == "1":
            nombre = input("Nombre del nuevo cliente: ").strip()
            correo = input("Correo electrónico: ").strip()
            if nombre and correo:
                tienda.clientes.append({"nombre": nombre, "correo": correo})
                print(f"✅ Cliente '{nombre}' registrado exitosamente.")
            else:
                print("❌ Datos inválidos.")

        elif opcion == "2":
            if not tienda.categorias:
                print("⚠️ Debe crear al menos una categoría antes de agregar productos.")
                return
            nombre = input("Nombre del producto: ").strip()
            precio = float(input("Precio: "))
            stock = int(input("Stock inicial: "))
            
            print("\nCategorías disponibles:")
            for idx, cat in enumerate(tienda.categorias, 1):
                print(f"  {idx}. {cat}")
            c_idx = int(input("Seleccione el número de categoría: ")) - 1
            
            if 0 <= c_idx < len(tienda.categorias):
                cat_sel = tienda.categorias[c_idx]
                nuevo_p = Producto(tienda.obtener_nuevo_id_producto(), nombre, precio, stock, cat_sel)
                tienda.productos.append(nuevo_p)
                print(f"✅ Producto '{nombre}' creado con éxito.")
            else:
                print("❌ Categoría no válida.")

        elif opcion == "3":
            nueva_cat = input("Nombre de la nueva categoría: ").strip()
            if nueva_cat and nueva_cat not in tienda.categorias:
                tienda.categorias.append(nueva_cat)
                print(f"✅ Categoría '{nueva_cat}' creada.")
            else:
                print("❌ Categoría existente o inválida.")

        elif opcion == "4":
            if not tienda.categorias:
                print("No hay categorías para modificar.")
                return
            for idx, cat in enumerate(tienda.categorias, 1):
                print(f"{idx}. {cat}")
            c_idx = int(input("Seleccione la categoría a modificar: ")) - 1
            if 0 <= c_idx < len(tienda.categorias):
                nuevo_nom = input("Nuevo nombre para la categoría: ").strip()
                cat_vieja = tienda.categorias[c_idx]
                tienda.categorias[c_idx] = nuevo_nom
                # Actualizar categoría en productos asociados
                for p in tienda.productos:
                    if p.categoria == cat_vieja:
                        p.categoria = nuevo_nom
                print(f"✅ Categoría actualizada a '{nuevo_nom}'.")

        elif opcion == "5":
            if not tienda.productos:
                print("No hay productos cargados.")
                return
            for p in tienda.productos:
                print(p)
            p_id = int(input("Ingrese el ID del producto a modificar: "))
            prod = next((p for p in tienda.productos if p.id_prod == p_id), None)
            if prod:
                print(f"Modificando: {prod.nombre}")
                prod.nombre = input(f"Nuevo nombre [{prod.nombre}]: ").strip() or prod.nombre
                
                prec_str = input(f"Nuevo precio [{prod.precio}]: ").strip()
                if prec_str:
                    prod.precio = float(prec_str)

                stock_str = input(f"Nuevo stock [{prod.stock}]: ").strip()
                if stock_str:
                    prod.stock = int(stock_str)

                print("✅ Producto modificado exitosamente.")
            else:
                print("❌ Producto no encontrado.")

        elif opcion == "6":
            if not tienda.productos:
                print("No hay productos cargados.")
                return
            for p in tienda.productos:
                print(p)
            p_id = int(input("Ingrese el ID del producto a eliminar: "))
            prod = next((p for p in tienda.productos if p.id_prod == p_id), None)
            if prod:
                tienda.productos.remove(prod)
                print(f"🗑️ Producto '{prod.nombre}' eliminado.")
            else:
                print("❌ Producto no encontrado.")

        elif opcion == "7":
            print("\n📋 HISTORIAL DE PEDIDOS REALIZADOS:")
            if not tienda.pedidos:
                print("Aún no se han registrado pedidos.")
            else:
                for ped in tienda.pedidos:
                    print(ped)
        else:
            print("❌ Opción no válida.")


class Cliente:
    def __init__(self, nombre: str = "Cliente"):
        self.nombre = nombre
        self.carrito = Carrito()

    def mostrar_menu(self):
        print(f"\n--------- bienvenido a la tienda en linea ({self.nombre}) -------------")
        print("1. ver productos")
        print("2. agregar productos al carrito")
        print("3. ver carrito")
        print("4. eliminar productos del carrito")
        print("5. realizar pago")
        print("0. Salir")

    def ejecutar_opcion(self, opcion, tienda):
        if opcion == "1":
            print("\n--- CATÁLOGO DE PRODUCTOS ---")
            if not tienda.productos:
                print("No hay productos disponibles por ahora.")
            else:
                for p in tienda.productos:
                    print(p)

        elif opcion == "2":
            if not tienda.productos:
                print("No hay productos para comprar.")
                return
            self.ejecutar_opcion("1", tienda)
            p_id = int(input("Ingrese el ID del producto a agregar: "))
            prod = next((p for p in tienda.productos if p.id_prod == p_id), None)
            
            if prod:
                qty = int(input(f"Cantidad a agregar (Disponibles: {prod.stock}): "))
                if 1 <= qty <= prod.stock:
                    # Sobrecarga del operador '+'
                    self.carrito + (prod, qty)
                    print(f"✅ Agregado(s) {qty} x {prod.nombre} al carrito.")
                else:
                    print("❌ Cantidad fuera de rango de stock.")
            else:
                print("❌ Producto no encontrado.")

        elif opcion == "3":
            print("\n🛒 TU CARRITO DE COMPRAS:")
            if not self.carrito.items:
                print("El carrito está vacío.")
            else:
                for p, q in self.carrito.items:
                    print(f"  • {p.nombre} x{q} - ${p.precio * q:.2f}")
                print(f"Total acumulado: ${self.carrito.total():.2f}")

        elif opcion == "4":
            if not self.carrito.items:
                print("El carrito está vacío.")
                return
            print("\nProductos en tu carrito:")
            for idx, (p, q) in enumerate(self.carrito.items, 1):
                print(f"  {idx}. {p.nombre} x{q}")
            c_idx = int(input("Seleccione el número a eliminar: ")) - 1
            if 0 <= c_idx < len(self.carrito.items):
                eliminado = self.carrito.items.pop(c_idx)
                print(f"🗑️ Se eliminó '{eliminado[0].nombre}' del carrito.")
            else:
                print("❌ Selección inválida.")

        elif opcion == "5":
            if self.carrito.total() == 0:
                print("❌ Tu carrito está vacío.")
                return
            
            print("\nSelecciona método de pago:")
            print("1. PayPal")
            print("2. Stripe")
            m_opcion = input("Opción (1 o 2): ")
            
            pasarela = PayPal() if m_opcion == "1" else Stripe()
            
            id_ped = tienda.obtener_nuevo_id_pedido()
            nuevo_pedido = Pedido(id_ped, self, pasarela)
            
            if nuevo_pedido.procesar_pago():
                tienda.pedidos.append(nuevo_pedido)

        else:
            print("❌ Opción no válida.")


# ==========================================
# 4. GESTOR PRINCIPAL DE LA TIENDA
# ==========================================

class Tienda:
    def __init__(self):
        self.categorias = ["Electrónica", "Ropa"]
        self.productos = [
            Producto(1, "Laptop HP", 650.00, 5, "Electrónica"),
            Producto(2, "Mouse Inalámbrico", 15.00, 20, "Electrónica"),
            Producto(3, "Camiseta", 20.00, 10, "Ropa")
        ]
        self.clientes = []
        self.pedidos = []
        self._contador_prod = 3
        self._contador_ped = 0

    def obtener_nuevo_id_producto(self):
        self._contador_prod += 1
        return self._contador_prod

    def obtener_nuevo_id_pedido(self):
        self._contador_ped += 1
        return self._contador_ped


def iniciar_sistema():
    tienda = Tienda()
    
    while True:
        print("\n==========================================")
        print("   === SISTEMA DE TIENDA EN LÍNEA ===")
        print("==========================================")
        print("Seleccione su rol:")
        print("1. Administrador")
        print("2. Cliente")
        print("0. Salir del sistema")
        
        rol = input("Ingrese opción (0, 1 o 2): ").strip()
        
        if rol == "1":
            admin = Administrador()
            while True:
                admin.mostrar_menu()
                opcion = input("Seleccione una opción: ").strip()
                if opcion == "0":
                    print("Cerrando sesión de administrador...")
                    break
                admin.ejecutar_opcion(opcion, tienda)

        elif rol == "2":
            nom_cliente = input("\nIngrese su nombre para continuar: ").strip() or "Cliente Anonimo"
            cliente = Cliente(nom_cliente)
            while True:
                cliente.mostrar_menu()
                opcion = input("Seleccione una opción: ").strip()
                if opcion == "0":
                    print("Gracias por tu visita. ¡Hasta pronto!")
                    break
                cliente.ejecutar_opcion(opcion, tienda)

        elif rol == "0":
            print("\nSaliendo del sistema. ¡Que tengas un buen día!")
            break
        else:
            print("❌ Rol no válido. Intente nuevamente.")


if __name__ == "__main__":
    iniciar_sistema()