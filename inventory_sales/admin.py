from django.contrib import admin
from .models import Categoria, Insumo, Producto, MovimientoStock, Venta, DetalleVenta


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('icono', 'nombre', 'activo', 'creado_en')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'unidad_medida', 'stock_actual', 'stock_minimo', 'costo_unitario', 'estado_stock', 'activo')
    list_filter = ('unidad_medida', 'activo')
    search_fields = ('codigo', 'nombre')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('emoji', 'codigo', 'nombre', 'categoria', 'precio', 'costo', 'stock_disponible', 'stock_minimo', 'estado_stock', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion')


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'get_item_nombre', 'cantidad', 'stock_anterior', 'stock_nuevo', 'responsable', 'fecha')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre', 'insumo__nombre', 'motivo', 'responsable')

    def get_item_nombre(self, obj):
        return obj.producto.nombre if obj.producto else (obj.insumo.nombre if obj.insumo else "-")
    get_item_nombre.short_description = "Producto / Insumo"


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal')


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('numero_ticket', 'cliente_nombre', 'metodo_pago', 'total', 'estado', 'creado_en')
    list_filter = ('estado', 'metodo_pago', 'creado_en')
    search_fields = ('numero_ticket', 'cliente_nombre', 'cliente_identificacion')
    inlines = [DetalleVentaInline]
