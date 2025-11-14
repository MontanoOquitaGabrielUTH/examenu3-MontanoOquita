# tienda/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ============ MODELO PERFIL DE USUARIO ============
class PerfilUsuario(models.Model):
    ROLES = (
        ('vendedor', 'Vendedor'),
        ('gerente', 'Gerente'),
        ('administrador', 'Administrador'),
        ('cliente','Cliente'),
        ('admin','Admin')
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='vendedor')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    fecha_contratacion = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        ordering = ['-fecha_contratacion']

    # Métodos de utilidad
    def es_vendedor(self): return self.rol == 'vendedor'
    def es_gerente(self): return self.rol == 'gerente'
    def es_administrador(self): return self.rol == 'administrador' or self.rol == 'admin'
    def es_cliente(self): return self.rol == 'cliente'
    def tiene_permiso_lectura(self): return True
    def tiene_permiso_escritura(self): return self.rol in ['gerente', 'administrador']
    def tiene_permiso_eliminacion(self): return self.rol == 'administrador'
    # ------------------ PERMISOS ESPECÍFICOS ------------------
    # Productos y Categorías
    def puede_ver_productos(self):
        # Todos los roles pueden ver productos y categorías
        return True

    # Clientes
    def puede_ver_clientes(self):
        # Solo administrador y gerente pueden ver otros clientes
        return self.rol in ['administrador', 'gerente']

    # Ventas
    def puede_ver_ventas(self):
        # Administrador y gerente ven todas las ventas, vendedor puede consultar, cliente solo sus propias compras
        return self.rol in ['administrador', 'gerente', 'vendedor', 'cliente']

    # Perfil propio
    def puede_editar_perfil_propio(self):
        # Solo el cliente puede editar su propio perfil
        return self.rol == 'cliente'

# ============ MODELO CATEGORÍA ============
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']


# ============ MODELO PROVEEDOR ============
class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    empresa = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)  # <--- Campo agregado
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['empresa']


# ============ MODELO PRODUCTO ============
class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(                 # Precio con decimales
        max_digits=10,                            # Máx: 99999999.99
        decimal_places=2                          # 2 decimales
    )
    stock = models.IntegerField(default=0)        # Cantidad en inventario
    categoria = models.ForeignKey(                # Llave foránea a Categoría
        Categoria,
        on_delete=models.CASCADE,                 # Si borras categoría, borras productos
        related_name='productos'                  # categoria.productos.all()
    )
    proveedores = models.ManyToManyField('Proveedor', blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(   # Se actualiza automáticamente
        auto_now=True
    )
    activo = models.BooleanField(default=True)

    
    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


class Cliente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(max_length=191, unique=True)
    telefono = models.CharField(max_length=15)
    direccion = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['apellido', 'nombre']


# ============ MODELO VENTA ============
class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ventas')
    vendedor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ventas_realizadas')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='ventas')
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateTimeField(default=timezone.now)  # ✅


    def __str__(self):
        return f"Venta #{self.id} - {self.producto.nombre} - ${self.total}"

    def save(self, *args, **kwargs):
        # Si no hay precio_unitario, tomarlo del producto
        if not self.precio_unitario and self.producto:
            self.precio_unitario = self.producto.precio_venta  # Usa tu campo correcto

        # Calcula total
        self.total = (self.cantidad or 0) * (self.precio_unitario or 0)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha_venta']
