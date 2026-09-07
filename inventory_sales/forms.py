from decimal import Decimal
from django import forms
from .models import Categoria, Insumo, Producto, MovimientoStock, Venta


class BaseStyledForm(forms.ModelForm):
    """Clase base para aplicar estilos CSS consistentes y modernos a los formularios."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class CategoriaForm(BaseStyledForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'icono', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Hamburguesas Gourmet, Bebidas, etc.'}),
            'descripcion': forms.Textarea(attrs={'placeholder': 'Breve descripción de la categoría...'}),
            'icono': forms.TextInput(attrs={'placeholder': 'Ej. 🍔, 🥤, 🍟, 🍦, 🌭'}),
        }


class InsumoForm(BaseStyledForm):
    class Meta:
        model = Insumo
        fields = ['codigo', 'nombre', 'unidad_medida', 'stock_actual', 'stock_minimo', 'costo_unitario', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'placeholder': 'Ej. INS-001'}),
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Pan de Hamburguesa Brioche, Carne Angus...'}),
            'stock_actual': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'costo_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def clean_stock_actual(self):
        stock = self.cleaned_data.get('stock_actual')
        if stock is not None and stock < 0:
            raise forms.ValidationError("El stock actual no puede ser negativo.")
        return stock

    def clean_costo_unitario(self):
        costo = self.cleaned_data.get('costo_unitario')
        if costo is not None and costo < 0:
            raise forms.ValidationError("El costo unitario no puede ser negativo.")
        return costo


class ProductoForm(BaseStyledForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'categoria', 'precio', 'costo', 'stock_disponible', 'stock_minimo', 'descripcion', 'emoji', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'placeholder': 'Ej. PRD-001'}),
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Hamburguesa Doble Queso Tocino'}),
            'precio': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'costo': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00'}),
            'stock_disponible': forms.NumberInput(attrs={'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'min': '0'}),
            'descripcion': forms.Textarea(attrs={'placeholder': 'Detalles de ingredientes, acompañamientos incluidos...'}),
            'emoji': forms.TextInput(attrs={'placeholder': 'Ej. 🍔'}),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio <= 0:
            raise forms.ValidationError("El precio de venta debe ser mayor a 0.")
        return precio


class MovimientoStockForm(forms.Form):
    item_tipo = forms.ChoiceField(
        choices=[('PRODUCTO', '🍔 Producto del Menú'), ('INSUMO', '📦 Insumo / Materia Prima')],
        label="¿Qué elemento desea ajustar?",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_item_tipo'})
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        required=False,
        label="Seleccione el Producto",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_producto_select'})
    )
    insumo = forms.ModelChoiceField(
        queryset=Insumo.objects.filter(activo=True),
        required=False,
        label="Seleccione el Insumo",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_insumo_select'})
    )
    tipo = forms.ChoiceField(
        choices=MovimientoStock.TIPOS_MOVIMIENTO,
        label="Tipo de Movimiento",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cantidad = forms.DecimalField(
        min_value=Decimal('0.01'),
        decimal_places=2,
        max_digits=10,
        label="Cantidad a mover / ajustar",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ej. 10.00'})
    )
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ej. Compra a proveedor, caducidad, conteo físico...'}),
        label="Motivo o Justificación"
    )
    responsable = forms.CharField(
        initial="Administrador",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del operador'}),
        label="Responsable del Registro"
    )

    def clean(self):
        cleaned_data = super().clean()
        item_tipo = cleaned_data.get('item_tipo')
        producto = cleaned_data.get('producto')
        insumo = cleaned_data.get('insumo')

        if item_tipo == 'PRODUCTO' and not producto:
            self.add_error('producto', 'Debe seleccionar un producto.')
        elif item_tipo == 'INSUMO' and not insumo:
            self.add_error('insumo', 'Debe seleccionar un insumo.')

        return cleaned_data
