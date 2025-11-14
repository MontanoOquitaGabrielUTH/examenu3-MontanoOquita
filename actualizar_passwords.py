# Script para establecer contraseñas a los usuarios
# Ejecutar con: python manage.py shell < actualizar_passwords.py

from django.contrib.auth.models import User

print("=" * 70)
print("🔐 ESTABLECIENDO CONTRASEÑAS PARA TODOS LOS USUARIOS")
print("=" * 70)
print()

# Lista de usuarios con sus contraseñas
usuarios = [
    {'username': 'vendedor', 'password': 'vendedor123', 'rol': 'Vendedor'},
    {'username': 'gerente', 'password': 'gerente123', 'rol': 'Gerente'},
    {'username': 'administrador', 'password': 'admin123', 'rol': 'Administrador'},
    {'username': 'admin', 'password': 'admin123', 'rol': 'Superusuario'},
    {'username': 'cliente', 'password': 'cliente123', 'rol': 'Cliente'},
]

for user_data in usuarios:
    try:
        user = User.objects.get(username=user_data['username'])
        user.set_password(user_data['password'])
        user.save()
        print(f"✅ {user_data['rol']:15} | Usuario: {user_data['username']:15} | Contraseña: {user_data['password']}")
    except User.DoesNotExist:
        print(f"⚠️  Usuario '{user_data['username']}' no existe")

print()
print("=" * 70)
print("✅ CONTRASEÑAS ACTUALIZADAS")
print("=" * 70)
print()
print("📋 CREDENCIALES DE ACCESO:")
print()
print("┌─────────────────┬─────────────────┬─────────────────┐")
print("│ ROL             │ USUARIO         │ CONTRASEÑA      │")
print("├─────────────────┼─────────────────┼─────────────────┤")
print("│ Vendedor        │ vendedor        │ vendedor123     │")
print("│ Gerente         │ gerente         │ gerente123      │")
print("│ Administrador   │ administrador   │ admin123        │")
print("│ Superusuario    │ admin           │ admin123        │")
print("│ Cliente         │ cliente         │ cliente123      │")
print("└─────────────────┴─────────────────┴─────────────────┘")
print()
