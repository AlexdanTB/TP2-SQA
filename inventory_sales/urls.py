from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Punto de Venta (POS)
    path('pos/', views.pos_view, name='pos'),
    path('api/pos/procesar/', views.procesar_venta_api, name='pos_procesar'),

    # Categorías CRUD
    path('categorias/', views.CategoriaListView.as_view(), name='category_list'),
    path('categorias/crear/', views.CategoriaCreateView.as_view(), name='category_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='category_edit'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='category_delete'),

    # Productos CRUD
    path('productos/', views.ProductoListView.as_view(), name='product_list'),
    path('productos/crear/', views.ProductoCreateView.as_view(), name='product_create'),
    path('productos/<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='product_edit'),
    path('productos/<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='product_delete'),

    # Insumos CRUD (Materias Primas / Inventario Base)
    path('insumos/', views.InsumoListView.as_view(), name='insumo_list'),
    path('insumos/crear/', views.InsumoCreateView.as_view(), name='insumo_create'),
    path('insumos/<int:pk>/editar/', views.InsumoUpdateView.as_view(), name='insumo_edit'),
    path('insumos/<int:pk>/eliminar/', views.InsumoDeleteView.as_view(), name='insumo_delete'),

    # Movimientos de Stock / Reabastecimiento
    path('stock/movimientos/', views.MovimientoStockListView.as_view(), name='stock_movement_list'),
    path('stock/movimientos/nuevo/', views.crear_movimiento_stock, name='stock_movement_create'),

    # Ventas, Facturación e Historial
    path('ventas/', views.VentaListView.as_view(), name='sales_list'),
    path('ventas/<int:pk>/', views.VentaDetailView.as_view(), name='sale_detail'),
    path('ventas/<int:pk>/ticket/', views.ticket_venta_view, name='sale_receipt'),
    path('ventas/<int:pk>/anular/', views.anular_venta_view, name='sale_cancel'),
]
