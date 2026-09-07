# 🍔 FastFood Express - Sistema de Gestión de Stock, Inventario y Ventas

Sistema web desarrollado bajo la arquitectura **MVT (Model-View-Template)** utilizando **Django**, **ORM** y **SQLite** para la administración integral de stock, inventario y ventas en una tienda de comida rápida.

---

## 🏛️ Arquitectura MVT (Model - View - Template)

| Capa | Implementación en el Proyecto | Responsabilidad |
| :--- | :--- | :--- |
| **Model (ORM)** | `inventory_sales/models.py` | Definición de entidades (`Categoria`, `Insumo`, `Producto`, `MovimientoStock`, `Venta`, `DetalleVenta`), validadores y lógica de integridad persistida en SQLite (`db.sqlite3`). |
| **View (Controlador)** | `inventory_sales/views.py` | Lógica de negocio, consultas ORM, control transaccional de stock (`transaction.atomic`), procesamiento del POS y cálculo de facturación/IVA. |
| **Template (Presentación)** | `templates/inventory_sales/*.html` | Interfaz gráfica interactiva responsiva con diseño Dark Slate & Amber Flame, carrito de compras dinámico y tickets térmicos imprimibles. |

---

## 🚀 Características Principales

1. **Gestión de Menú y Productos (CRUD)**:
   - Registro, edición, listado con filtros y eliminación/desactivación de productos.
   - Control de precios, costos estimados y cálculo de márgenes.
   - Clasificación por categorías con emojis representativos.
2. **Control de Inventario & Stock (CRUD)**:
   - Gestión de insumos y materias primas de cocina con unidades de medida (kg, unidades, litros, porciones).
   - Semáforo de alerta visual en tiempo real (**Óptimo**, **Stock Bajo**, **Agotado**).
   - Módulo de auditoría de movimientos (entradas por compra, salidas por merma/vencimiento y ajustes de inventario).
3. **Terminal Punto de Venta (POS)**:
   - Catálogo ágil con filtrado por categoría y búsqueda instantánea.
   - Carrito dinámico con validación de existencias en tiempo real.
   - Cálculo automático de subtotal, IVA (15%) y cambio en efectivo.
   - Generación de comprobante/ticket digital térmico imprimible.
4. **Historial de Ventas & Anulaciones**:
   - Registro detallado de transacciones con métodos de pago (Efectivo, Tarjeta, Transferencia).
   - Proceso de anulación transaccional con restitución automática del stock al inventario.
5. **Dashboard Ejecutivo**:
   - KPIs del día: Total vendido ($), cantidad de tickets emitidos, productos en menú y alertas de stock bajo.
   - Ranking de los 5 productos más vendidos.

---

## ⚙️ Instalación y Puesta en Marcha

### 1. Clonar / Navegar al Proyecto
```bash
cd dev
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Aplicar Migraciones de SQLite
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Cargar Datos de Prueba (Seed Data)
Puebla la tienda con categorías, platos del menú, insumos y stock inicial:
```bash
python manage.py seed_data
```

### 5. Iniciar el Servidor de Desarrollo
```bash
python manage.py runserver
```

Acceder desde el navegador a: **`http://127.0.0.1:8000/`**

> **Credenciales de Administrador preconfiguradas:**  
> - **Usuario:** `admin`  
> - **Contraseña:** `admin123`  
> - **Panel Admin:** `http://127.0.0.1:8000/admin/`

---

## 🧪 Pruebas Unitarias SQA (Calidad de Software)

Para ejecutar la suite automatizada de pruebas unitarias:
```bash
python manage.py test inventory_sales
```
Verifica la integridad de datos, operaciones CRUD, descuento de inventario, validaciones de sobreventa y reversión de stock en anulaciones.
