# tienda/forms.py
# Importamos forms de Django para crear formularios
from django import forms
from .models import Producto, Categoria, Proveedor, Cliente, Venta, User  # Importamos nuestros modelos
from django_select2.forms import Select2MultipleWidget 

# ============ FORMULARIO PARA PRODUCTOS ============
from django import forms
from django_select2.forms import Select2MultipleWidget  # Asegúrate de tener instalado django-select2
from .models import Producto

class ProductoForm(forms.ModelForm):
    """Formulario para crear y editar productos"""
    
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'categoria', 'proveedores', 'activo']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ingrese una descripción del producto'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'proveedores': Select2MultipleWidget(attrs={
                'class': 'form-control'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

        labels = {
            'nombre': 'Nombre del Producto',
            'descripcion': 'Descripción',
            'precio': 'Precio ($)',
            'stock': 'Cantidad en Stock',
            'categoria': 'Categoría',
            'proveedores': 'Proveedores',
            'activo': '¿Producto Activo?',
        }



# ============ FORMULARIO PARA CATEGORÍAS ============
class CategoriaForm(forms.ModelForm):
    """Formulario para crear y editar categorías"""
    
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']  # Solo nombre y descripción
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la categoría'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ingrese una descripción (opcional)'
            }),
        }
        
        labels = {
            'nombre': 'Nombre de la Categoría',
            'descripcion': 'Descripción',
        }


# ============ FORMULARIO PARA PROVEEDORES ============
class ProveedorForm(forms.ModelForm):
    """Formulario para crear y editar proveedores"""
    
    class Meta:
        model = Proveedor
        fields = ['nombre', 'empresa', 'telefono', 'email', 'direccion']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del contacto'
            }),
            'empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto'
            }),
            'email': forms.EmailInput(attrs={  # EmailInput valida formato de email
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
        }
        
        labels = {
            'nombre': 'Nombre del Contacto',
            'empresa': 'Empresa',
            'telefono': 'Teléfono',
            'email': 'Correo Electrónico',
            'direccion': 'Dirección',
        }


# ============ FORMULARIO PARA CLIENTES ============
class ClienteForm(forms.ModelForm):
    """Formulario para crear y editar clientes"""
    
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'email', 'telefono', 'direccion']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del cliente'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido del cliente'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección de entrega'
            }),
        }
        
        labels = {
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
        }


# ============ FORMULARIO PARA VENTAS ============
class VentaForm(forms.ModelForm):
    """Formulario para registrar ventas"""
    class Meta:
        model = Venta
        fields = ['cliente', 'producto', 'cantidad']  # Solo solicita cliente, producto y cantidad (el precio se toma automático)

        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-control'  # Select (combobox) con clientes
            }),
            'producto': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_producto'  # ID para poder manipular con JavaScript si es necesario
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',  # Mínimo 1 unidad
                'value': '1'  # Valor por defecto
            }),
        }

        labels = {
            'cliente': 'Cliente',
            'producto': 'Producto',
            'cantidad': 'Cantidad',
        }

class UserForm(forms.ModelForm):
    """Formulario para que un cliente edite su propio perfil"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']  # Solo los campos que quieres que edite
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
        }
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
        }