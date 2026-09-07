import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de Categoría")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    icono = models.CharField(max_length=50, default="🍔", verbose_name="Ícono / Emoji")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.icono} {self.nombre}"


class Insumo(models.Model):
    UNIDADES = [
        ('UNIDAD', 'Unidades (u)'),
        ('KG', 'Kilogramos (kg)'),
        ('GRAMO', 'Gramos (g)'),
        ('LITRO', 'Litros (L)'),
        ('PORCION', 'Porciones'),
    ]

    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código de Insumo")
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Insumo / Materia Prima")
    unidad_medida = models.CharField(max_length=20, choices=UNIDADES, default='UNIDAD', verbose_name="Unidad de Medida")
    stock_actual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Stock Actual"
    )
    stock_minimo = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=5.00, 
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Stock Mínimo de Alerta"
    )
    costo_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Costo Unitario ($)"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Insumo / Materia Prima"
        verbose_name_plural = "Insumos y Materias Primas"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.stock_actual} {self.get_unidad_medida_display()})"

    @property
    def estado_stock(self):
        if self.stock_actual <= 0:
            return "AGOTADO"
        elif self.stock_actual <= self.stock_minimo:
            return "BAJO"
        return "OPTIMO"


class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código de Producto")
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Producto")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos', verbose_name="Categoría")
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio de Venta ($)"
    )
    costo = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Costo Estimado ($)"
    )
    stock_disponible = models.PositiveIntegerField(
        default=0, 
        verbose_name="Stock Disponible (Unidades)"
    )
    stock_minimo = models.PositiveIntegerField(
        default=5, 
        verbose_name="Stock Mínimo de Alerta"
    )
    descripcion = models.TextField(blank=True, verbose_name="Descripción de Ingredientes / Combo")
    emoji = models.CharField(max_length=50, default="🍔", verbose_name="Emoji Representativo")
    activo = models.BooleanField(default=True, verbose_name="Disponible para Venta")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Producto del Menú"
        verbose_name_plural = "Productos del Menú"
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return f"{self.emoji} {self.nombre} - ${self.precio:.2f} (Stock: {self.stock_disponible})"

    @property
    def estado_stock(self):
        if self.stock_disponible <= 0:
            return "AGOTADO"
        elif self.stock_disponible <= self.stock_minimo:
            return "BAJO"
        return "OPTIMO"

    @property
    def tiene_stock(self):
        return self.stock_disponible > 0


class MovimientoStock(models.Model):
    TIPOS_MOVIMIENTO = [
        ('ENTRADA', '📥 Entrada / Reabastecimiento'),
        ('SALIDA_MERMA', '🗑️ Salida por Merma / Vencimiento'),
        ('AJUSTE', '⚖️ Ajuste Manual de Inventario'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, null=True, blank=True, related_name='movimientos', verbose_name="Producto")
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, null=True, blank=True, related_name='movimientos', verbose_name="Insumo")
    tipo = models.CharField(max_length=20, choices=TIPOS_MOVIMIENTO, verbose_name="Tipo de Movimiento")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Cantidad")
    stock_anterior = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Stock Anterior")
    stock_nuevo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Stock Resultante")
    motivo = models.TextField(verbose_name="Motivo / Justificación")
    responsable = models.CharField(max_length=100, default="Admin", verbose_name="Responsable")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Movimiento")

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']

    def __str__(self):
        item = self.producto.nombre if self.producto else (self.insumo.nombre if self.insumo else "Desconocido")
        return f"{self.get_tipo_display()} - {item} ({self.cantidad}) [{self.fecha.strftime('%d/%m/%Y %H:%M')}]"


class Venta(models.Model):
    METODOS_PAGO = [
        ('EFECTIVO', '💵 Efectivo'),
        ('TARJETA', '💳 Tarjeta de Débito/Crédito'),
        ('TRANSFERENCIA', '📱 Transferencia / QR'),
    ]

    ESTADOS_VENTA = [
        ('COMPLETADA', '✅ Completada'),
        ('ANULADA', '❌ Anulada'),
    ]

    numero_ticket = models.CharField(max_length=30, unique=True, verbose_name="N° Ticket / Factura")
    cliente_nombre = models.CharField(max_length=150, default="Consumidor Final", verbose_name="Nombre del Cliente")
    cliente_identificacion = models.CharField(max_length=20, default="9999999999", verbose_name="RUC / Cédula")
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='EFECTIVO', verbose_name="Método de Pago")
    monto_recibido = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Monto Recibido ($)")
    cambio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Cambio ($)")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Subtotal ($)")
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="IVA (15%) ($)")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total ($)")
    estado = models.CharField(max_length=20, choices=ESTADOS_VENTA, default='COMPLETADA', verbose_name="Estado")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones / Nota")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas Realizadas"
        ordering = ['-creado_en']

    def __str__(self):
        return f"Ticket #{self.numero_ticket} - ${self.total:.2f} ({self.get_estado_display()})"

    @classmethod
    def generar_numero_ticket(cls):
        hoy = timezone.now().strftime("%Y%m%d")
        total_hoy = cls.objects.filter(creado_en__date=timezone.now().date()).count() + 1
        return f"TK-{hoy}-{total_hoy:04d}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles', verbose_name="Venta")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='ventas_detalle', verbose_name="Producto")
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario ($)")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal ($)")

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} - ${self.subtotal:.2f}"

    def save(self, *args, **kwargs):
        if not self.subtotal:
            self.subtotal = Decimal(self.cantidad) * self.precio_unitario
        super().save(*args, **kwargs)
