from .models import PerfilUsuario

def alerta_perfil(request):
    mostrar = False
    
    # Solo revisamos si el usuario ya inició sesión
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfilusuario
            # La alerta salta si no ha elegido NINGÚN interés o si le falta la edad
            if perfil.intereses.count() == 0 or not perfil.edad:
                mostrar = True
        except PerfilUsuario.DoesNotExist:
            # Si es un usuario nuevo (o el superusuario admin) y aún no tiene tabla de perfil
            mostrar = True
            
    # Esto envía la variable 'mostrar_alerta_perfil' a todos los HTML de tu proyecto
    return {'mostrar_alerta_perfil': mostrar}