# tienda/views.py
from django.shortcuts import render, redirect, get_object_or_404 # Funciones comunes para renderizar, redirigir y obtener objetos.
from django.contrib.auth.decorators import login_required, permission_required # Decoradores para requerir autenticación y permisos.
from django.contrib.auth.views import LoginView, LogoutView # Vistas predefinidas de Django para autenticación.
from django.urls import reverse_lazy # Función para obtener URLs de forma perezosa.
from django.contrib.auth.models import Group # Modelo para gestionar grupos/roles de usuarios.
from django.contrib import messages # Módulo para enviar mensajes de notificación al usuario.
# from .models import Producto, Categoria # Importa los modelos necesarios.
# from .forms import ProductoForm # Importa el formulario de Producto.
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import Producto, Categoria, PerfilUsuario, Proveedor, Cliente, Venta # Importa los modelos necesarios.
from .forms import ProductoForm, CategoriaForm, ProveedorForm, UserForm,  ClienteForm, VentaForm # Importa el formulario de Producto.
from django.utils import timezone
from django.db.models import Sum, Count, F, Value
from django.db.models.functions import Concat
from datetime import timedelta, datetime
from django.urls import reverse
import pandas as pd
import plotly.express as px

# ============ DECORADOR PERSONALIZADO PARA PERMISOS POR ROL ============
def rol_requerido(*roles_permitidos):
    """
    Decorador personalizado que verifica si el usuario tiene uno de los roles permitidos.
    
    Uso:
        @rol_requerido('gerente', 'administrador')
        def mi_vista(request):
            ...
    
    Parámetros:
        *roles_permitidos: Lista de roles que pueden acceder a la vista
        Opciones: 'vendedor', 'gerente', 'administrador'
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # 1. Verificar si el usuario está autenticado
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para acceder')
                return redirect('login')
            
            # 2. Si es superusuario, permitir acceso siempre
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # 3. Verificar si el usuario tiene perfil con rol asignado
            try:
                perfil = request.user.perfil  # Obtener perfil del usuario
                # 4. Verificar si su rol está en los roles permitidos
                if perfil.rol in roles_permitidos:
                    return view_func(request, *args, **kwargs)  # Permitir acceso
                else:
                    # Mostrar mensaje de error indicando roles necesarios
                    roles_texto = ', '.join([r.capitalize() for r in roles_permitidos])
                    messages.error(request, f'⚠️ Acceso denegado. Se requiere rol: {roles_texto}')
                    return redirect('home')  # Redirigir al home
            except PerfilUsuario.DoesNotExist:
                # Si el usuario no tiene perfil asignado
                messages.error(request, '⚠️ Tu cuenta no tiene un perfil asignado. Contacta al administrador.')
                return redirect('home')
        
        return _wrapped_view
    return decorator


# ============ VISTA DE LOGIN ============
def login_view(request):
    """Vista para el inicio de sesión de usuarios"""
    # Si el usuario ya está autenticado, redirigir al home
    if request.user.is_authenticated:
        return redirect('home')
    
    # Si el método es POST, procesamos el formulario de login
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)  # Creamos el formulario con los datos enviados
        if form.is_valid():  # Si el formulario es válido
            username = form.cleaned_data.get('username')  # Obtenemos el nombre de usuario
            password = form.cleaned_data.get('password')  # Obtenemos la contraseña
            user = authenticate(username=username, password=password)  # Autenticamos al usuario
            if user is not None:  # Si la autenticación fue exitosa
                login(request, user)  # Iniciamos sesión
                messages.success(request, f'Bienvenido {username}!')  # Mensaje de bienvenida
                return redirect('home')  # Redirigimos al home
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')  # Mensaje de error
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')  # Mensaje de error si el formulario no es válido
    else:
        form = AuthenticationForm()  # Si es GET, creamos un formulario vacío
    
    return render(request, 'tienda/login.html', {'form': form})  # Renderizamos el template de login


# ============ VISTA DE LOGOUT ============
def logout_view(request):
    """Vista para cerrar sesión"""
    logout(request)  # Cerramos la sesión del usuario
    messages.info(request, 'Sesión cerrada correctamente')  # Mensaje informativo
    return redirect('login')  # Redirigimos al login

@login_required
def home(request):
    """Dashboard principal con totales generales y total de ventas del día."""

    total_productos = Producto.objects.count()
    total_categorias = Categoria.objects.count()
    total_proveedores = Proveedor.objects.count()
    total_clientes = Cliente.objects.count()

    productos_recientes = Producto.objects.all()[:5]

    # ✅ Obtener fecha actual en zona horaria local (ya ajustada)
    hoy_local = timezone.localtime(timezone.now()).date()

    # ✅ Determinar inicio y fin del día actual (zona local)
    inicio_dia = timezone.make_aware(
        timezone.datetime.combine(hoy_local, timezone.datetime.min.time())
    )
    fin_dia = inicio_dia + timedelta(days=1)

    # ✅ Calcular total vendido hoy (usando rango local correcto)
    total_ventas = (
        Venta.objects
        .filter(fecha_venta__gte=inicio_dia, fecha_venta__lt=fin_dia)
        .aggregate(total=Sum('total'))['total'] or 0
    )

    context = {
        'total_productos': total_productos,
        'total_categorias': total_categorias,
        'total_proveedores': total_proveedores,
        'total_clientes': total_clientes,
        'productos_recientes': productos_recientes,
        'total_ventas': total_ventas,
    }

    return render(request, 'tienda/dashboard.html', context)


# ============ VISTAS CRUD PARA PRODUCTOS ============
@login_required
def producto_lista(request):
    """Vista que lista todos los productos"""
    productos = Producto.objects.all()  # Obtenemos todos los productos de la base de datos
    return render(request, 'tienda/producto_lista.html', {'productos': productos})  # Renderizamos template con la lista

@rol_requerido('administrador', 'gerente', 'admin')
@login_required
def producto_crear(request):
    """Vista para crear un nuevo producto"""
    if request.method == 'POST':  # Si se envió el formulario
        form = ProductoForm(request.POST)  # Creamos el formulario con los datos enviados
        if form.is_valid():  # Si el formulario es válido (todos los campos correctos)
            form.save()  # Guardamos el producto en la base de datos
            messages.success(request, 'Producto creado exitosamente')  # Mensaje de éxito
            return redirect('producto_lista')  # Redirigimos a la lista de productos
    else:
        form = ProductoForm()  # Si es GET, creamos un formulario vacío
    
    return render(request, 'tienda/producto_form.html', {'form': form, 'accion': 'Crear'})  # Renderizamos el formulario



@rol_requerido('gerente', 'administrador','admin')
@login_required  # Solo Gerente y Administrador pueden editar
def producto_editar(request, pk):
    """Vista para editar un producto existente"""
    producto = get_object_or_404(Producto, pk=pk)  # Obtenemos el producto por su ID (Primary Key), si no existe muestra 404
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)  # Creamos el formulario con los datos del producto existente
        if form.is_valid():
            form.save()  # Guardamos los cambios
            messages.success(request, 'Producto actualizado exitosamente')
            return redirect('producto_lista')
    else:
        form = ProductoForm(instance=producto)  # Mostramos el formulario con los datos actuales del producto
    
    return render(request, 'tienda/producto_form.html', {'form': form, 'accion': 'Editar'})


@login_required
@rol_requerido('administrador','admin')  # Solo Administrador puede eliminar
def producto_eliminar(request, pk):
    """Vista para eliminar un producto"""
    producto = get_object_or_404(Producto, pk=pk)  # Obtenemos el producto
    if request.method == 'POST':  # Confirmación de eliminación debe ser POST por seguridad
        producto.delete()  # Eliminamos el producto de la base de datos
        messages.success(request, 'Producto eliminado exitosamente')
        return redirect('producto_lista')
    
    return render(request, 'tienda/producto_confirm_delete.html', {'producto': producto})  # Mostramos página de confirmación


# ============ VISTAS CRUD PARA CATEGORÍAS ============
@login_required
@rol_requerido('gerente', 'administrador', 'vendedor', 'cliente','admin')  # Vendedor NO puede ver categorías
def categoria_lista(request):
    """Vista que lista todas las categorías"""
    # categorias = Categoria.objects.all()
    categorias = Categoria.objects.annotate(total_productos=Count('productos'))
    return render(request, 'tienda/categoria_lista.html', {'categorias': categorias})


@login_required
@rol_requerido('gerente', 'administrador','admin')  # Solo Gerente y Administrador
def categoria_crear(request):
    """Vista para crear una nueva categoría"""
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente')
            return redirect('categoria_lista')
    else:
        form = CategoriaForm()
    
    return render(request, 'tienda/categoria_form.html', {'form': form, 'accion': 'Crear'})


@login_required
@rol_requerido('gerente', 'administrador','admin')
def categoria_editar(request, pk):
    """Vista para editar una categoría existente"""
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente')
            return redirect('categoria_lista')
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'tienda/categoria_form.html', {'form': form, 'accion': 'Editar'})


@login_required
@rol_requerido('administrador','admin')  # Solo Administrador
def categoria_eliminar(request, pk):
    """Vista para eliminar una categoría"""
    categoria = get_object_or_404(Categoria, pk=pk)

    # 🔹 Contar los productos asociados a la categoría
    productos_asociados = categoria.productos.count()

    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada exitosamente')
        return redirect('categoria_lista')
    
    # 🔹 Enviamos también el conteo al template
    return render(request, 'tienda/categoria_eliminar.html', {
        'categoria': categoria,
        'productos_asociados': productos_asociados
    })

# ============ VISTAS CRUD PARA PROVEEDORES ============
@login_required
@rol_requerido('gerente', 'administrador', 'vendedor','admin')  # Vendedor NO puede ver proveedores
def proveedor_lista(request):
    """Vista que lista todos los proveedores"""
    proveedores = Proveedor.objects.all()
    return render(request, 'tienda/proveedor_lista.html', {'proveedores': proveedores})


@login_required
@rol_requerido('gerente', 'administrador','admin')  # Solo Gerente y Administrador
def proveedor_crear(request):
    """Vista para crear un nuevo proveedor"""
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor creado exitosamente')
            return redirect('proveedor_lista')
    else:
        form = ProveedorForm()
    
    return render(request, 'tienda/proveedor_form.html', {'form': form, 'accion': 'Crear'})


@login_required
@rol_requerido('gerente', 'administrador','admin')
def proveedor_editar(request, pk):
    """Vista para editar un proveedor existente"""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado exitosamente')
            return redirect('proveedor_lista')
    else:
        form = ProveedorForm(instance=proveedor)
    
    return render(request, 'tienda/proveedor_form.html', {'form': form, 'accion': 'Editar'})


@login_required
@rol_requerido('administrador','admin')
def proveedor_eliminar(request, pk):
    """Vista para eliminar un proveedor"""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, 'Proveedor eliminado exitosamente')
        return redirect('proveedor_lista')
    
    return render(request, 'tienda/proveedor_eliminar.html', {'proveedor': proveedor})


# ============ VISTAS CRUD PARA CLIENTES ============
@login_required
@rol_requerido('administrador','admin','vendedor', 'gerente')
def cliente_lista(request):
    """Vista que lista todos los clientes"""
    clientes = Cliente.objects.all()
    return render(request, 'tienda/cliente_lista.html', {'clientes': clientes})


@login_required
@rol_requerido('administrador','admin', 'gerente')
def cliente_crear(request):
    """Vista para crear un nuevo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado exitosamente')
            return redirect('cliente_lista')
    else:
        form = ClienteForm()
    
    return render(request, 'tienda/cliente_form.html', {'form': form, 'accion': 'Crear'})


@login_required
@rol_requerido('gerente', 'administrador','admin', 'gerente')
def cliente_editar(request, pk):
    """Vista para editar un cliente existente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente')
            return redirect('cliente_lista')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'tienda/cliente_form.html', {'form': form, 'accion': 'Editar'})

@login_required
@rol_requerido('cliente')
def cliente_mi_perfil(request):
    """Permite al usuario con rol 'cliente' editar solo su propio perfil"""
    
    usuario = request.user  # el usuario logueado

    if request.method == 'POST':
        form = UserForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('cliente_mi_perfil')
    else:
        form = UserForm(instance=usuario)

    return render(request, 'tienda/cliente_form.html', {
        'form': form,
        'accion': 'Mi Perfil'
    })

@login_required
@rol_requerido('administrador', 'admin')
def cliente_eliminar(request, pk):
    """Vista para eliminar un cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado exitosamente')
        return redirect('cliente_lista')
    
    return render(request, 'tienda/cliente_eliminar.html', {'cliente': cliente})

@login_required
@rol_requerido('cliente')
def mis_compras(request):
    """Muestra solo las ventas del cliente logueado"""
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        ventas = Venta.objects.filter(cliente=cliente).order_by('-id')  # Últimas primero
    except Cliente.DoesNotExist:
        ventas = []  # Si no tiene cliente asociado

    return render(request, 'tienda/mis_compras.html', {
        'ventas': ventas
    })

# ============ VISTAS PARA VENTAS ============
@rol_requerido('administrador', 'gerente','admin')
@login_required
def venta_crear(request):
    """Vista para registrar una nueva venta"""
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.vendedor = request.user
            venta.precio_unitario = venta.producto.precio
            venta.save()
            messages.success(request, f'Venta registrada exitosamente - Total: ${venta.total}')

            # Recuperar los parámetros del periodo si existen
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')

            # Redirigir manteniendo el rango de fechas usando reverse
            if fecha_inicio and fecha_fin:
                return redirect(f"{reverse('reporte_ventas')}?inicio={fecha_inicio}&fin={fecha_fin}")
            else:
                hoy = timezone.now().date()
                return redirect(f"{reverse('reporte_ventas')}?inicio={hoy}&fin={hoy}")

    else:
        form = VentaForm()
        # Capturamos las fechas si vienen desde la URL
        fecha_inicio = request.GET.get('inicio', '')
        fecha_fin = request.GET.get('fin', '')

    return render(request, 'tienda/venta_form.html', {
        'form': form,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })



@rol_requerido('administrador', 'gerente', 'vendedor', 'admin')
@login_required
def reporte_ventas(request):
    """Muestra el reporte de ventas con filtrado por fechas y estadísticas."""

    # === Filtro de fechas ===
    inicio_str = request.GET.get('inicio')
    fin_str = request.GET.get('fin')

    hoy = timezone.localdate()
    es_periodo = False

    if inicio_str and fin_str:
        try:
            inicio_date = datetime.strptime(inicio_str, '%Y-%m-%d').date()
            fin_date = datetime.strptime(fin_str, '%Y-%m-%d').date()

            # Se incluye TODO el último día
            inicio = timezone.make_aware(datetime.combine(inicio_date, datetime.min.time()))
            fin = timezone.make_aware(datetime.combine(fin_date, datetime.max.time()))

            es_periodo = inicio_date != fin_date

        except ValueError:
            inicio = timezone.make_aware(datetime.combine(hoy, datetime.min.time()))
            fin = timezone.make_aware(datetime.combine(hoy, datetime.max.time()))
    else:
        inicio = timezone.make_aware(datetime.combine(hoy, datetime.min.time()))
        fin = timezone.make_aware(datetime.combine(hoy, datetime.max.time()))

    ventas = (
        Venta.objects
        .select_related('cliente', 'vendedor', 'producto')
        .filter(fecha_venta__gte=inicio, fecha_venta__lte=fin)
        .order_by('-fecha_venta'))

    # === Estadísticas ===
    total_ventas = ventas.aggregate(total=Sum('total'))['total'] or 0
    cantidad_ventas = ventas.count()
    promedio_venta = total_ventas / cantidad_ventas if cantidad_ventas else 0

    context = {
        'ventas': ventas,
        'total_ventas_dia': total_ventas,
        'cantidad_ventas': cantidad_ventas,
        'promedio_venta': promedio_venta,
        'fecha_inicio': inicio.date(),
        'fecha_fin': fin.date(),         # ← AQUÍ LA CORRECCIÓN REAL
        'fecha_actual': hoy,
        'es_periodo': es_periodo,
    }

    # === Reportes adicionales ===
    if 'generar_reporte' in request.GET and ventas.exists():

        clientes_frecuentes = (
            ventas.annotate(
                nombre_completo=Concat(
                    F('cliente__nombre'), Value(' '), F('cliente__apellido')
                )
            )
            .values('nombre_completo')
            .annotate(
                total_compras=Count('id'),
                total_gastado=Sum('total')
            )
            .order_by('-total_gastado')[:5]
        )

        top_productos = (
            ventas.values('producto__nombre')
            .annotate(cantidad_total=Sum('cantidad'))
            .order_by('-cantidad_total')[:5]
        )

        # Gráfica con Plotly
        df = pd.DataFrame(list(top_productos))
        if not df.empty:
            fig = px.bar(
                df,
                x='producto__nombre',
                y='cantidad_total',
                title='Ventas por Producto',
                labels={'producto__nombre': 'Producto', 'cantidad_total': 'Cantidad Vendida'}
            )
            ventas_por_producto_html = fig.to_html(full_html=False)
        else:
            ventas_por_producto_html = None

        context.update({
            'clientes_frecuentes': clientes_frecuentes,
            'top_productos': top_productos,
            'ventas_por_producto_html': ventas_por_producto_html,
        })

    # === Permisos ===
    try:
        perfil = request.user.perfil
        puede_generar_reporte = perfil.rol in ['administrador', 'gerente']
    except PerfilUsuario.DoesNotExist:
        puede_generar_reporte = False

    context['puede_generar_reporte'] = puede_generar_reporte

    return render(request, 'tienda/reporte_ventas.html', context)



@rol_requerido('administrador', 'gerente','admin')
@login_required
def venta_nueva(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.vendedor = request.user
            venta.save()
            messages.success(request, "Venta registrada exitosamente.")
            return redirect('reporte_ventas')
    else:
        form = VentaForm()
    return render(request, 'tienda/venta_form.html', {'form': form})

@login_required
def ventas_estadisticas(request):
    ventas = Venta.objects.all()

    # --- FILTRO POR FECHA ---
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio and fecha_fin:
        ventas = ventas.filter(fecha_venta__date__range=[fecha_inicio, fecha_fin])

    # --- ESTADÍSTICAS ---
    total_ventas = ventas.aggregate(Sum('total'))['total__sum'] or 0
    numero_ventas = ventas.count()
    productos_mas_vendidos = (
        ventas.values('producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:5]
    )

    ventas_por_producto = (
        ventas.values('producto__nombre')
        .annotate(total=Sum('total'))
        .order_by('producto__nombre')
    )

    context = {
        'ventas': ventas,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_ventas': total_ventas,
        'numero_ventas': numero_ventas,
        'productos_mas_vendidos': productos_mas_vendidos,
        'ventas_por_producto': ventas_por_producto,
    }

    return render(request, 'tienda/ventas_estadisticas.html', context)