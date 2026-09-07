import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from .models import Categoria, Insumo, Producto, MovimientoStock, Venta, DetalleVenta


class CategoriaModelAndCRUDTest(TestCase):
    """Pruebas SQA para el Modelo y CRUD de Categorías."""

    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(
            nombre="Hamburguesas",
            descripcion="Hamburguesas caseras",
            icono="🍔"
        )

    def test_categoria_creacion_y_str(self):
        self.assertEqual(str(self.categoria), "🍔 Hamburguesas")
        self.assertTrue(self.categoria.activo)

    def test_categoria_list_view(self):
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hamburguesas")

    def test_categoria_create_view(self):
        response = self.client.post(reverse('category_create'), {
            'nombre': 'Bebidas',
            'descripcion': 'Gaseosas y jugos',
            'icono': '🥤',
            'activo': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Categoria.objects.filter(nombre='Bebidas').exists())

    def test_categoria_update_view(self):
        response = self.client.post(reverse('category_edit', args=[self.categoria.pk]), {
            'nombre': 'Hamburguesas Gourmet',
            'descripcion': 'Actualizada',
            'icono': '🍔',
            'activo': True
        })
        self.assertEqual(response.status_code, 302)
        self.categoria.refresh_from_db()
        self.assertEqual(self.categoria.nombre, 'Hamburguesas Gourmet')


class ProductoAndStockTest(TestCase):
    """Pruebas SQA para Productos, Insumos y Control de Stock."""

    def setUp(self):
        self.client = Client()
        self.cat = Categoria.objects.create(nombre="Snacks", icono="🍟")
        self.producto = Producto.objects.create(
            codigo="PRD-TEST-1",
            nombre="Papas Fritas Medianas",
            categoria=self.cat,
            precio=Decimal('2.50'),
            costo=Decimal('0.80'),
            stock_disponible=10,
            stock_minimo=3,
            emoji="🍟"
        )

    def test_producto_estado_stock_optimo(self):
        self.assertEqual(self.producto.estado_stock, "OPTIMO")
        self.assertTrue(self.producto.tiene_stock)

    def test_producto_estado_stock_bajo_y_agotado(self):
        self.producto.stock_disponible = 2
        self.producto.save()
        self.assertEqual(self.producto.estado_stock, "BAJO")

        self.producto.stock_disponible = 0
        self.producto.save()
        self.assertEqual(self.producto.estado_stock, "AGOTADO")
        self.assertFalse(self.producto.tiene_stock)

    def test_crear_movimiento_stock_entrada(self):
        response = self.client.post(reverse('stock_movement_create'), {
            'item_tipo': 'PRODUCTO',
            'producto': self.producto.id,
            'tipo': 'ENTRADA',
            'cantidad': '15.00',
            'motivo': 'Compra de existencias',
            'responsable': 'Auditor SQA'
        })
        self.assertEqual(response.status_code, 302)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_disponible, 25)
        self.assertTrue(MovimientoStock.objects.filter(producto=self.producto, tipo='ENTRADA').exists())


class VentasAndPOSTransactionTest(TestCase):
    """Pruebas SQA de Procesamiento de Ventas en POS y Transaccionalidad."""

    def setUp(self):
        self.client = Client()
        self.cat = Categoria.objects.create(nombre="Combos", icono="🍔")
        self.producto1 = Producto.objects.create(
            codigo="PRD-POS-1",
            nombre="Hamburguesa Royal",
            categoria=self.cat,
            precio=Decimal('5.00'),
            stock_disponible=10,
            stock_minimo=2
        )
        self.producto2 = Producto.objects.create(
            codigo="PRD-POS-2",
            nombre="Gaseosa 500ml",
            categoria=self.cat,
            precio=Decimal('2.00'),
            stock_disponible=5,
            stock_minimo=1
        )

    def test_procesar_venta_exitosa_descuenta_stock(self):
        payload = {
            'cliente_nombre': 'Alex Dávila',
            'cliente_identificacion': '1720304050',
            'metodo_pago': 'EFECTIVO',
            'monto_recibido': 20.00,
            'items': [
                {'id': self.producto1.id, 'cantidad': 2},  # 2 x $5.00 = $10.00
                {'id': self.producto2.id, 'cantidad': 1},  # 1 x $2.00 = $2.00
            ]
        }
        # Total PVP: 2 x $5.00 + 1 x $2.00 = $12.00. Con $20.00 recibido, cambio = $8.00
        response = self.client.post(
            reverse('pos_procesar'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total'], 12.00)
        self.assertEqual(data['cambio'], 8.00)

        # Verificar descuento exacto de stock en ORM
        self.producto1.refresh_from_db()
        self.producto2.refresh_from_db()
        self.assertEqual(self.producto1.stock_disponible, 8)
        self.assertEqual(self.producto2.stock_disponible, 4)

        # Verificar creación de Venta y Detalle
        venta = Venta.objects.get(numero_ticket=data['ticket_numero'])
        self.assertEqual(venta.cliente_nombre, 'Alex Dávila')
        self.assertEqual(venta.detalles.count(), 2)

    def test_rechazo_venta_por_stock_insuficiente(self):
        payload = {
            'cliente_nombre': 'Test Cliente',
            'cliente_identificacion': '9999999999',
            'metodo_pago': 'EFECTIVO',
            'monto_recibido': 100.00,
            'items': [
                {'id': self.producto2.id, 'cantidad': 10}  # Solo hay 5 en stock
            ]
        }

        response = self.client.post(
            reverse('pos_procesar'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Stock insuficiente', data['error'])

        # Verificar que el stock no fue alterado
        self.producto2.refresh_from_db()
        self.assertEqual(self.producto2.stock_disponible, 5)

    def test_anular_venta_restituye_stock(self):
        # 1. Crear venta inicial (3 x $5.00 = $15.00 + 15% IVA = $17.25)
        payload = {
            'cliente_nombre': 'Cliente Devolución',
            'metodo_pago': 'EFECTIVO',
            'monto_recibido': 20.00,
            'items': [{'id': self.producto1.id, 'cantidad': 3}]
        }
        resp = self.client.post(reverse('pos_procesar'), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        ticket_id = resp.json()['ticket_id']

        self.producto1.refresh_from_db()
        self.assertEqual(self.producto1.stock_disponible, 7)

        # 2. Anular la venta
        cancel_resp = self.client.post(
            reverse('sale_cancel', args=[ticket_id]),
            data={'motivo': 'Error de digitación en caja'}
        )
        self.assertEqual(cancel_resp.status_code, 302)

        # 3. Comprobar que el stock volvió a 10
        self.producto1.refresh_from_db()
        self.assertEqual(self.producto1.stock_disponible, 10)

        venta = Venta.objects.get(id=ticket_id)
        self.assertEqual(venta.estado, 'ANULADA')
