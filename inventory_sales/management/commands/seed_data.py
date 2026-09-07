from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from inventory_sales.models import Categoria, Insumo, Producto, MovimientoStock, Venta, DetalleVenta


class Command(BaseCommand):
    help = 'Puebla la base de datos SQLite con datos iniciales para la tienda de comida rápida'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos de prueba..."))

        with transaction.atomic():
            # 1. CATEGORÍAS
            cats_data = [
                {'nombre': 'Hamburguesas', 'icono': '🍔', 'descripcion': 'Hamburguesas artesanales de carne Angus y pollo crispy'},
                {'nombre': 'Pizzas & Porciones', 'icono': '🍕', 'descripcion': 'Pizzas estilo New York e italianas'},
                {'nombre': 'Combos Especiales', 'icono': '🍟', 'descripcion': 'Combos completos con papas y bebida'},
                {'nombre': 'Bebidas & Gaseosas', 'icono': '🥤', 'descripcion': 'Refrescos, jugos naturales y agua'},
                {'nombre': 'Postres & Helados', 'icono': '🍦', 'descripcion': 'Helados suaves, sundaes y donas'},
            ]
            cats_map = {}
            for c_data in cats_data:
                cat, _ = Categoria.objects.get_or_create(
                    nombre=c_data['nombre'],
                    defaults={'icono': c_data['icono'], 'descripcion': c_data['descripcion']}
                )
                cats_map[cat.nombre] = cat

            self.stdout.write(self.style.SUCCESS(f"[OK] {len(cats_map)} Categorias creadas/verificadas."))

            # 2. INSUMOS / MATERIAS PRIMAS
            insumos_data = [
                {'codigo': 'INS-001', 'nombre': 'Pan de Hamburguesa Brioche', 'unidad_medida': 'UNIDAD', 'stock_actual': Decimal('150.00'), 'stock_minimo': Decimal('30.00'), 'costo_unitario': Decimal('0.35')},
                {'codigo': 'INS-002', 'nombre': 'Carne Angus Molida (Porcion 150g)', 'unidad_medida': 'PORCION', 'stock_actual': Decimal('80.00'), 'stock_minimo': Decimal('20.00'), 'costo_unitario': Decimal('1.20')},
                {'codigo': 'INS-003', 'nombre': 'Queso Cheddar Americano (Rebanadas)', 'unidad_medida': 'PORCION', 'stock_actual': Decimal('200.00'), 'stock_minimo': Decimal('40.00'), 'costo_unitario': Decimal('0.15')},
                {'codigo': 'INS-004', 'nombre': 'Papas Pre-Fritas Corte Tradicional', 'unidad_medida': 'KG', 'stock_actual': Decimal('45.00'), 'stock_minimo': Decimal('10.00'), 'costo_unitario': Decimal('1.80')},
                {'codigo': 'INS-005', 'nombre': 'Salsa Especial de la Casa', 'unidad_medida': 'LITRO', 'stock_actual': Decimal('8.50'), 'stock_minimo': Decimal('3.00'), 'costo_unitario': Decimal('4.50')},
                {'codigo': 'INS-006', 'nombre': 'Tocino Ahumado Rebanado', 'unidad_medida': 'KG', 'stock_actual': Decimal('3.00'), 'stock_minimo': Decimal('5.00'), 'costo_unitario': Decimal('6.50')},  # Stock bajo intencional
            ]
            for ins_data in insumos_data:
                Insumo.objects.get_or_create(
                    codigo=ins_data['codigo'],
                    defaults=ins_data
                )

            self.stdout.write(self.style.SUCCESS(f"[OK] {len(insumos_data)} Insumos cargados."))

            # 3. PRODUCTOS DEL MENÚ
            prods_data = [
                {
                    'codigo': 'PRD-001', 'nombre': 'Hamburguesa Clásica con Queso',
                    'categoria': cats_map['Hamburguesas'], 'precio': Decimal('4.99'), 'costo': Decimal('1.80'),
                    'stock_disponible': 40, 'stock_minimo': 10, 'emoji': '🍔',
                    'descripcion': 'Carne Angus 150g, queso cheddar derretido, lechuga, tomate y salsa especial.'
                },
                {
                    'codigo': 'PRD-002', 'nombre': 'Hamburguesa Doble Tocino BBQ',
                    'categoria': cats_map['Hamburguesas'], 'precio': Decimal('7.50'), 'costo': Decimal('2.90'),
                    'stock_disponible': 25, 'stock_minimo': 8, 'emoji': '🥓',
                    'descripcion': 'Doble carne Angus, doble tocino crujiente, cebolla caramelizada y salsa BBQ ahumada.'
                },
                {
                    'codigo': 'PRD-003', 'nombre': 'Combo Familiar FastBite',
                    'categoria': cats_map['Combos Especiales'], 'precio': Decimal('14.99'), 'costo': Decimal('5.50'),
                    'stock_disponible': 15, 'stock_minimo': 5, 'emoji': '🍟',
                    'descripcion': '2 Hamburguesas Clásicas + 2 Papas Medianas + 2 Gaseosas 500ml.'
                },
                {
                    'codigo': 'PRD-004', 'nombre': 'Porción Papas Rústicas con Queso',
                    'categoria': cats_map['Combos Especiales'], 'precio': Decimal('3.25'), 'costo': Decimal('0.90'),
                    'stock_disponible': 30, 'stock_minimo': 10, 'emoji': '🥔',
                    'descripcion': 'Papas rústicas sazonadas con paprika y bañadas en salsa cheddar caliente.'
                },
                {
                    'codigo': 'PRD-005', 'nombre': 'Pizza Personal Pepperoni Express',
                    'categoria': cats_map['Pizzas & Porciones'], 'precio': Decimal('5.50'), 'costo': Decimal('2.10'),
                    'stock_disponible': 18, 'stock_minimo': 5, 'emoji': '🍕',
                    'descripcion': 'Masa artesanal crujiente, queso mozzarella premium y doble pepperoni.'
                },
                {
                    'codigo': 'PRD-006', 'nombre': 'Gaseosa Coca-Cola 500ml',
                    'categoria': cats_map['Bebidas & Gaseosas'], 'precio': Decimal('1.50'), 'costo': Decimal('0.75'),
                    'stock_disponible': 60, 'stock_minimo': 15, 'emoji': '🥤',
                    'descripcion': 'Gaseosa bien helada en botella personal.'
                },
                {
                    'codigo': 'PRD-007', 'nombre': 'Sundae de Chocolate & Vainilla',
                    'categoria': cats_map['Postres & Helados'], 'precio': Decimal('2.25'), 'costo': Decimal('0.60'),
                    'stock_disponible': 4, 'stock_minimo': 8, 'emoji': '🍨',  # Stock bajo intencional para alerta SQA
                    'descripcion': 'Helado cremoso de vainilla con fudge de chocolate caliente y maní picado.'
                },
            ]

            created_prods = []
            for p_data in prods_data:
                prod, _ = Producto.objects.get_or_create(
                    codigo=p_data['codigo'],
                    defaults=p_data
                )
                created_prods.append(prod)

            self.stdout.write(self.style.SUCCESS(f"[OK] {len(created_prods)} Productos de Menu cargados."))

            # 4. REGISTRAR MOVIMIENTO INICIAL DE STOCK
            for p in created_prods:
                MovimientoStock.objects.get_or_create(
                    producto=p,
                    tipo='ENTRADA',
                    cantidad=Decimal(p.stock_disponible),
                    defaults={
                        'stock_anterior': Decimal('0.00'),
                        'stock_nuevo': Decimal(p.stock_disponible),
                        'motivo': 'Inventario inicial de apertura de tienda',
                        'responsable': 'Administrador SQA'
                    }
                )

        self.stdout.write(self.style.SUCCESS("[OK] Poblacion de datos completada exitosamente."))
