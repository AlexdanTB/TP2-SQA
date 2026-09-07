import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, F, Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.generic import (
    TemplateView, ListView, DetailView,
    CreateView, UpdateView, DeleteView
)

from .models import Categoria, Insumo, Producto, MovimientoStock, Venta, DetalleVenta
from .forms import CategoriaForm, InsumoForm, ProductoForm, MovimientoStockForm


# ==========================================
# 1. DASHBOARD & MÉTRICAS PRINCIPALES
# ==========================================
class DashboardView(TemplateView):
    template_name = 'inventory_sales/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.now().date()

        # Ventas de hoy
        ventas_hoy = Venta.objects.filter(creado_en__date=hoy, estado='COMPLETADA')
        total_ventas_hoy = ventas_hoy.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        cantidad_ventas_hoy = ventas_hoy.count()

        # Totales generales
        total_productos = Producto.objects.filter(activo=True).count()
        total_insumos = Insumo.objects.filter(activo=True).count()

        # Alertas de Stock Bajo
        productos_stock_bajo = Producto.objects.filter(
            activo=True, stock_disponible__lte=F('stock_minimo')
        ).order_by('stock_disponible')

        insumos_stock_bajo = Insumo.objects.filter(
            activo=True, stock_actual__lte=F('stock_minimo')
        ).order_by('stock_actual')

        # Top 5 Productos Más Vendidos
        top_productos = DetalleVenta.objects.filter(
            venta__estado='COMPLETADA'
        ).values(
            'producto__nombre', 'producto__emoji', 'producto__precio'
        ).annotate(
            total_vendido=Sum('cantidad'),
            ingresos=Sum('subtotal')
        ).order_by('-total_vendido')[:5]

        # Últimas 5 Ventas
        ultimas_ventas = Venta.objects.all().order_by('-creado_en')[:5]

        context.update({
            'total_ventas_hoy': total_ventas_hoy,
            'cantidad_ventas_hoy': cantidad_ventas_hoy,
            'total_productos': total_productos,
            'total_insumos': total_insumos,
            'alertas_total': productos_stock_bajo.count() + insumos_stock_bajo.count(),
            'productos_stock_bajo': productos_stock_bajo[:6],
            'insumos_stock_bajo': insumos_stock_bajo[:6],
            'top_productos': top_productos,
            'ultimas_ventas': ultimas_ventas,
        })
        return context


# ==========================================
# 2. CRUD CATEGORÍAS
# ==========================================
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'inventory_sales/category_list.html'
    context_object_name = 'categorias'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Categoria.objects.filter(nombre__icontains=query)
        return Categoria.objects.all()


class CategoriaCreateView(CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'inventory_sales/category_form.html'
    success_url = reverse_lazy('category_list')

    def form_valid(self, form):
        messages.success(self.request, f"¡Categoría '{form.instance.nombre}' creada con éxito!")
        return super().form_valid(form)


class CategoriaUpdateView(UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'inventory_sales/category_form.html'
    success_url = reverse_lazy('category_list')

    def form_valid(self, form):
        messages.success(self.request, f"Categoría '{form.instance.nombre}' actualizada.")
        return super().form_valid(form)


class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'inventory_sales/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')

    def delete(self, request, *args, **kwargs):
        categoria = self.get_object()
        if categoria.productos.exists():
            messages.error(request, f"No se puede eliminar '{categoria.nombre}' porque contiene productos asociados.")
            return redirect('category_list')
        messages.warning(request, f"Categoría '{categoria.nombre}' eliminada.")
        return super().delete(request, *args, **kwargs)


# ==========================================
# 3. CRUD PRODUCTOS (MENÚ FAST FOOD)
# ==========================================
class ProductoListView(ListView):
    model = Producto
    template_name = 'inventory_sales/product_list.html'
    context_object_name = 'productos'

    def get_queryset(self):
        qs = Producto.objects.select_related('categoria').all()
        q = self.request.GET.get('q')
        cat = self.request.GET.get('categoria')
        stock_filter = self.request.GET.get('stock')

        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
        if cat:
            qs = qs.filter(categoria_id=cat)
        if stock_filter == 'bajo':
            qs = qs.filter(stock_disponible__lte=F('stock_minimo'), stock_disponible__gt=0)
        elif stock_filter == 'agotado':
            qs = qs.filter(stock_disponible=0)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        return context


class ProductoCreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'inventory_sales/product_form.html'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, f"Producto '{form.instance.nombre}' registrado correctamente.")
        return super().form_valid(form)


class ProductoUpdateView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'inventory_sales/product_form.html'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, f"Producto '{form.instance.nombre}' actualizado.")
        return super().form_valid(form)


class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = 'inventory_sales/product_confirm_delete.html'
    success_url = reverse_lazy('product_list')

    def delete(self, request, *args, **kwargs):
        producto = self.get_object()
        if producto.ventas_detalle.exists():
            # Si tiene ventas históricas, preferimos desactivar para mantener integridad referencial SQA
            producto.activo = False
            producto.save()
            messages.warning(request, f"El producto '{producto.nombre}' fue desactivado porque cuenta con historial de ventas.")
            return redirect('product_list')
        messages.warning(request, f"Producto '{producto.nombre}' eliminado permanentemente.")
        return super().delete(request, *args, **kwargs)


# ==========================================
# 4. CRUD INSUMOS / MATERIAS PRIMAS
# ==========================================
class InsumoListView(ListView):
    model = Insumo
    template_name = 'inventory_sales/insumo_list.html'
    context_object_name = 'insumos'

    def get_queryset(self):
        qs = Insumo.objects.all()
        q = self.request.GET.get('q')
        stock_filter = self.request.GET.get('stock')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
        if stock_filter == 'bajo':
            qs = qs.filter(stock_actual__lte=F('stock_minimo'), stock_actual__gt=0)
        elif stock_filter == 'agotado':
            qs = qs.filter(stock_actual=0)
        return qs


class InsumoCreateView(CreateView):
    model = Insumo
    form_class = InsumoForm
    template_name = 'inventory_sales/insumo_form.html'
    success_url = reverse_lazy('insumo_list')

    def form_valid(self, form):
        messages.success(self.request, f"Insumo '{form.instance.nombre}' registrado con éxito.")
        return super().form_valid(form)


class InsumoUpdateView(UpdateView):
    model = Insumo
    form_class = InsumoForm
    template_name = 'inventory_sales/insumo_form.html'
    success_url = reverse_lazy('insumo_list')

    def form_valid(self, form):
        messages.success(self.request, f"Insumo '{form.instance.nombre}' actualizado.")
        return super().form_valid(form)


class InsumoDeleteView(DeleteView):
    model = Insumo
    template_name = 'inventory_sales/insumo_confirm_delete.html'
    success_url = reverse_lazy('insumo_list')

    def delete(self, request, *args, **kwargs):
        insumo = self.get_object()
        messages.warning(request, f"Insumo '{insumo.nombre}' eliminado.")
        return super().delete(request, *args, **kwargs)


# ==========================================
# 5. MOVIMIENTOS Y GESTIÓN DE STOCK
# ==========================================
class MovimientoStockListView(ListView):
    model = MovimientoStock
    template_name = 'inventory_sales/stock_movement_list.html'
    context_object_name = 'movimientos'
    paginate_by = 25


def crear_movimiento_stock(request):
    if request.method == 'POST':
        form = MovimientoStockForm(request.POST)
        if form.is_valid():
            item_tipo = form.cleaned_data['item_tipo']
            tipo = form.cleaned_data['tipo']
            cantidad = form.cleaned_data['cantidad']
            motivo = form.cleaned_data['motivo']
            responsable = form.cleaned_data['responsable']

            with transaction.atomic():
                if item_tipo == 'PRODUCTO':
                    prod = form.cleaned_data['producto']
                    stock_anterior = Decimal(prod.stock_disponible)

                    if tipo == 'ENTRADA':
                        stock_nuevo = stock_anterior + cantidad
                    elif tipo == 'SALIDA_MERMA':
                        if cantidad > stock_anterior:
                            form.add_error('cantidad', f"No se puede extraer más del stock disponible ({stock_anterior}).")
                            return render(request, 'inventory_sales/stock_movement_form.html', {'form': form})
                        stock_nuevo = stock_anterior - cantidad
                    else:  # AJUSTE
                        stock_nuevo = cantidad

                    prod.stock_disponible = int(stock_nuevo)
                    prod.save()

                    MovimientoStock.objects.create(
                        producto=prod,
                        tipo=tipo,
                        cantidad=cantidad,
                        stock_anterior=stock_anterior,
                        stock_nuevo=Decimal(prod.stock_disponible),
                        motivo=motivo,
                        responsable=responsable
                    )
                    messages.success(request, f"Stock de '{prod.nombre}' actualizado a {prod.stock_disponible} unidades.")

                else:  # INSUMO
                    insumo = form.cleaned_data['insumo']
                    stock_anterior = insumo.stock_actual

                    if tipo == 'ENTRADA':
                        stock_nuevo = stock_anterior + cantidad
                    elif tipo == 'SALIDA_MERMA':
                        if cantidad > stock_anterior:
                            form.add_error('cantidad', f"No se puede extraer más del stock disponible ({stock_anterior}).")
                            return render(request, 'inventory_sales/stock_movement_form.html', {'form': form})
                        stock_nuevo = stock_anterior - cantidad
                    else:  # AJUSTE
                        stock_nuevo = cantidad

                    insumo.stock_actual = stock_nuevo
                    insumo.save()

                    MovimientoStock.objects.create(
                        insumo=insumo,
                        tipo=tipo,
                        cantidad=cantidad,
                        stock_anterior=stock_anterior,
                        stock_nuevo=insumo.stock_actual,
                        motivo=motivo,
                        responsable=responsable
                    )
                    messages.success(request, f"Stock de '{insumo.nombre}' actualizado a {insumo.stock_actual} {insumo.get_unidad_medida_display()}.")

            return redirect('stock_movement_list')
    else:
        form = MovimientoStockForm()

    return render(request, 'inventory_sales/stock_movement_form.html', {'form': form})


# ==========================================
# 6. PUNTO DE VENTA (POS) Y PROCESAMIENTO DE VENTAS
# ==========================================
def pos_view(request):
    categorias = Categoria.objects.filter(activo=True).prefetch_related('productos')
    productos = Producto.objects.filter(activo=True).select_related('categoria')
    return render(request, 'inventory_sales/pos.html', {
        'categorias': categorias,
        'productos': productos,
    })


def procesar_venta_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        cliente_nombre = data.get('cliente_nombre', 'Consumidor Final')
        cliente_id = data.get('cliente_identificacion', '9999999999')
        metodo_pago = data.get('metodo_pago', 'EFECTIVO')
        monto_recibido = Decimal(str(data.get('monto_recibido', 0)))
        observaciones = data.get('observaciones', '')

        if not items:
            return JsonResponse({'success': False, 'error': 'El carrito de venta está vacío.'}, status=400)

        with transaction.atomic():
            total_acumulado = Decimal('0.00')
            items_a_guardar = []

            # 1. Validación de stock previa
            for item in items:
                prod_id = item.get('id')
                cantidad = int(item.get('cantidad', 1))

                if cantidad <= 0:
                    return JsonResponse({'success': False, 'error': 'Cantidad no válida.'}, status=400)

                producto = Producto.objects.select_for_update().get(id=prod_id)

                if not producto.activo:
                    return JsonResponse({'success': False, 'error': f"El producto '{producto.nombre}' no está disponible."}, status=400)

                if producto.stock_disponible < cantidad:
                    return JsonResponse({
                        'success': False, 
                        'error': f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock_disponible}, solicitado: {cantidad}."
                    }, status=400)

                item_total = (producto.precio * Decimal(cantidad)).quantize(Decimal('0.01'))
                total_acumulado += item_total

                items_a_guardar.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'precio': producto.precio,
                    'subtotal': item_total
                })

            # 2. Desglose de IVA (15% incluido en el PVP del menú de comida rápida)
            subtotal_base = (total_acumulado / Decimal('1.15')).quantize(Decimal('0.01'))
            iva_total = total_acumulado - subtotal_base
            total_final = total_acumulado

            # Validación de pago si es en efectivo
            cambio = Decimal('0.00')
            if metodo_pago == 'EFECTIVO':
                if monto_recibido < total_final:
                    return JsonResponse({
                        'success': False,
                        'error': f"El monto recibido (${monto_recibido:.2f}) es menor al total (${total_final:.2f})."
                    }, status=400)
                cambio = (monto_recibido - total_final).quantize(Decimal('0.01'))
            else:
                monto_recibido = total_final

            # 3. Creación de la Venta en ORM
            ticket_num = Venta.generar_numero_ticket()
            venta = Venta.objects.create(
                numero_ticket=ticket_num,
                cliente_nombre=cliente_nombre or "Consumidor Final",
                cliente_identificacion=cliente_id or "9999999999",
                metodo_pago=metodo_pago,
                monto_recibido=monto_recibido,
                cambio=cambio,
                subtotal=subtotal_base,
                iva=iva_total,
                total=total_final,
                estado='COMPLETADA',
                observaciones=observaciones
            )

            # 4. Creación de Detalle y Descuento de Stock
            for item in items_a_guardar:
                prod = item['producto']
                cant = item['cantidad']

                DetalleVenta.objects.create(
                    venta=venta,
                    producto=prod,
                    cantidad=cant,
                    precio_unitario=item['precio'],
                    subtotal=item['subtotal']
                )

                # Descuento en stock
                stock_previo = prod.stock_disponible
                prod.stock_disponible -= cant
                prod.save()

                # Registro de movimiento
                MovimientoStock.objects.create(
                    producto=prod,
                    tipo='SALIDA_MERMA',
                    cantidad=Decimal(cant),
                    stock_anterior=Decimal(stock_previo),
                    stock_nuevo=Decimal(prod.stock_disponible),
                    motivo=f"Venta en POS - Ticket #{ticket_num}",
                    responsable="Cajero POS"
                )

        return JsonResponse({
            'success': True,
            'ticket_id': venta.id,
            'ticket_numero': venta.numero_ticket,
            'total': float(venta.total),
            'cambio': float(venta.cambio),
            'receipt_url': f"/ventas/{venta.id}/ticket/"
        })

    except Producto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Uno de los productos no existe en la base de datos.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error interno al procesar la venta: {str(e)}"}, status=500)


# ==========================================
# 7. HISTORIAL, DETALLE Y TICKET DE VENTAS
# ==========================================
class VentaListView(ListView):
    model = Venta
    template_name = 'inventory_sales/sales_list.html'
    context_object_name = 'ventas'
    paginate_by = 20

    def get_queryset(self):
        qs = Venta.objects.all().order_by('-creado_en')
        q = self.request.GET.get('q')
        fecha = self.request.GET.get('fecha')
        estado = self.request.GET.get('estado')

        if q:
            qs = qs.filter(
                Q(numero_ticket__icontains=q) | 
                Q(cliente_nombre__icontains=q) | 
                Q(cliente_identificacion__icontains=q)
            )
        if fecha:
            qs = qs.filter(creado_en__date=fecha)
        if estado:
            qs = qs.filter(estado=estado)
        return qs


class VentaDetailView(DetailView):
    model = Venta
    template_name = 'inventory_sales/sale_detail.html'
    context_object_name = 'venta'


def ticket_venta_view(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    return render(request, 'inventory_sales/sale_receipt.html', {'venta': venta})


def anular_venta_view(request, pk):
    venta = get_object_or_404(Venta, pk=pk)

    if venta.estado == 'ANULADA':
        messages.warning(request, f"La venta #{venta.numero_ticket} ya se encuentra anulada.")
        return redirect('sale_detail', pk=venta.pk)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', 'Anulación de venta por devolución o error de digitación')

        with transaction.atomic():
            # Restaurar stock de cada producto
            for detalle in venta.detalles.all():
                producto = detalle.producto
                stock_previo = producto.stock_disponible
                producto.stock_disponible += detalle.cantidad
                producto.save()

                MovimientoStock.objects.create(
                    producto=producto,
                    tipo='ENTRADA',
                    cantidad=Decimal(detalle.cantidad),
                    stock_anterior=Decimal(stock_previo),
                    stock_nuevo=Decimal(producto.stock_disponible),
                    motivo=f"Restitución por Anulación de Venta #{venta.numero_ticket}. Motivo: {motivo}",
                    responsable=request.user.username if request.user.is_authenticated else "Supervisor"
                )

            venta.estado = 'ANULADA'
            venta.observaciones = f"{venta.observaciones} | ANULADA: {motivo}".strip()
            venta.save()

            messages.success(request, f"Venta #{venta.numero_ticket} anulada con éxito y el stock ha sido restituido.")
            return redirect('sale_detail', pk=venta.pk)

    return render(request, 'inventory_sales/sale_confirm_cancel.html', {'venta': venta})
