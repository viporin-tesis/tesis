from django.shortcuts import render, get_object_or_404 # Agregamos get_object_or_404
from .models import Lugar, Categoria
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404, redirect # Agregamos redirect
from django.contrib.auth.decorators import login_required
from .models import Lugar, Categoria, PerfilUsuario # Asegúrate de tener PerfilUsuario aquí

def index(request):
    # 1. Traemos todos los lugares y todas las categorías iniciales
    lugares_lista = Lugar.objects.all()
    categorias_lista = Categoria.objects.all()
    
    # 2. Capturamos lo que el usuario escribió o seleccionó (si es que lo hizo)
    busqueda = request.GET.get('buscar')
    categoria_id = request.GET.get('categoria')
    
    # 3. Aplicamos los filtros si hay datos
    if busqueda:
        # icontains busca palabras clave sin importar mayúsculas/minúsculas
        lugares_lista = lugares_lista.filter(nombre__icontains=busqueda)
        
    if categoria_id:
        # Filtramos por el ID de la categoría seleccionada
        lugares_lista = lugares_lista.filter(categoria_id=categoria_id)
        
    contexto = {
        'lugares': lugares_lista,
        'categorias': categorias_lista, # Enviamos las categorías al HTML
    }
    
    return render(request, 'index.html', contexto)

# NUEVA VISTA
def detalle_lugar(request, lugar_id):
    # Busca el lugar por su ID, si no existe, lanza error 404
    lugar = get_object_or_404(Lugar, id=lugar_id)
    contexto = {'lugar': lugar}
    return render(request, 'detalle.html', contexto)
# NUEVA VISTA: Registro de Usuarios
def registro(request):
    if request.method == 'POST':
        # Si el usuario envió sus datos, los procesamos
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save() # Guarda el usuario en la base de datos
            login(request, usuario) # Inicia sesión automáticamente
            return redirect('index') # Lo manda a la página principal
    else:
        # Si acaba de entrar a la página, le mostramos el formulario vacío
        form = UserCreationForm()
        
    contexto = {'form': form}
    return render(request, 'registro.html', contexto)
# NUEVA VISTA: Perfil e Intereses (HU06)
@login_required # Protege la página de usuarios sin sesión
def perfil(request):
    # Busca el perfil del usuario. Si es su primera vez, lo crea automáticamente.
    perfil_obj, creado = PerfilUsuario.objects.get_or_create(usuario=request.user)
    todas_categorias = Categoria.objects.all()

    if request.method == 'POST':
        # 1. Guardamos datos demográficos
        perfil_obj.edad = request.POST.get('edad')
        perfil_obj.nacionalidad = request.POST.get('nacionalidad')

        # 2. Guardamos los intereses (checkboxes)
        # getlist obtiene todos los valores de los checkboxes marcados
        intereses_seleccionados = request.POST.getlist('intereses') 
        perfil_obj.intereses.set(intereses_seleccionados) # Actualiza la base de datos
        perfil_obj.save()

        return redirect('perfil') # Recarga la página para mostrar los cambios guardados

    # Preparamos los datos para mandarlos al HTML
    contexto = {
        'perfil': perfil_obj,
        'categorias': todas_categorias,
        # Extraemos solo los IDs de los intereses guardados para marcar las casillas
        'intereses_actuales': perfil_obj.intereses.values_list('id', flat=True)
    }
    return render(request, 'perfil.html', contexto)