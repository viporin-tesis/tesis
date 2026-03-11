from django.shortcuts import render, get_object_or_404 # Agregamos get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404, redirect # Agregamos redirect
from django.contrib.auth.decorators import login_required
from .models import Lugar, Categoria, PerfilUsuario # Asegúrate de tener PerfilUsuario aquí
from django.shortcuts import render, get_object_or_404, redirect
from .models import Lugar, Categoria, PerfilUsuario, Resena # <--- Asegúrate de importar Resena
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count
from .ml_engine import obtener_recomendaciones_rf

# NUEVA VISTA: Portada de Bienvenida
def landing(request):
    # Si el usuario ya está logueado (tiene cuenta), lo mandamos directo al catálogo
    if request.user.is_authenticated:
        return redirect('index')
    # Si es visitante nuevo, le mostramos la portada
    return render(request, 'landing.html')

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
        
    # 4. APLICAMOS LA INTELIGENCIA ARTIFICIAL (HU11b)
    # Iniciamos la lista vacía por si es un visitante o un admin
    recomendados_ids = [] 
    
    if request.user.is_authenticated and not request.user.is_staff:
        # Le pasamos a la IA la lista de lugares (ya sea completa o filtrada)
        # para que calcule las probabilidades y ponga el mejor al principio
        lugares_lista, recomendados_ids = obtener_recomendaciones_rf(request.user, lugares_lista)
        
    # 5. Enviamos todo al HTML
    contexto = {
        'lugares': lugares_lista,
        'categorias': categorias_lista, 
        'recomendados_ids': recomendados_ids, # ¡Vital para que aparezca la etiqueta amarilla!
    }
    
    return render(request, 'index.html', contexto)
# NUEVA VISTA
def detalle_lugar(request, lugar_id):
    lugar = get_object_or_404(Lugar, id=lugar_id)
    
    # 1. Traemos todas las reseñas de este lugar, de la más nueva a la más vieja
    resenas = lugar.resenas.all().order_by('-fecha')

    # 2. Lógica para guardar un nuevo comentario
    if request.method == 'POST' and request.user.is_authenticated:
        comentario_texto = request.POST.get('comentario')
        calificacion_num = request.POST.get('calificacion')
        
        if comentario_texto and calificacion_num:
            # Creamos la reseña en la base de datos
            Resena.objects.create(
                lugar=lugar,
                usuario=request.user,
                calificacion=int(calificacion_num),
                comentario=comentario_texto
            )
            # Recargamos la página para que aparezca el nuevo comentario
            return redirect('detalle_lugar', lugar_id=lugar.id)

    # 3. Enviamos el lugar y sus reseñas al HTML
    contexto = {
        'lugar': lugar,
        'resenas': resenas
    }
    return render(request, 'detalle.html', contexto)
def registro(request):
    if request.method == 'POST':
        # Si el usuario envió sus datos, los procesamos
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save() # Guarda el usuario en la base de datos
            login(request, usuario) # Inicia sesión automáticamente
            return redirect('perfil') # Lo manda a la página principal
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
# NUEVA VISTA: Dashboard Municipal con Chart.js (HU11a)
@staff_member_required # Solo usuarios marcados como "Staff" pueden entrar
def dashboard_municipal(request):
    # 1. Gráfico de Dona: ¿Cuántos lugares hay por categoría?
    categorias = Categoria.objects.annotate(total=Count('lugar'))
    nombres_categorias = [c.nombre for c in categorias]
    totales_categorias = [c.total for c in categorias]

    # 2. Gráfico de Barras: Top 5 lugares con mejor calificación
    lugares_top = Lugar.objects.annotate(promedio=Avg('resenas__calificacion')).order_by('-promedio')[:5]
    nombres_lugares = [l.nombre for l in lugares_top]
    # Si un lugar no tiene reseñas, su promedio es None, lo convertimos a 0
    promedios_lugares = [float(l.promedio or 0) for l in lugares_top]

    # Enviamos las listas al HTML
    contexto = {
        'nombres_categorias': nombres_categorias,
        'totales_categorias': totales_categorias,
        'nombres_lugares': nombres_lugares,
        'promedios_lugares': promedios_lugares,
    }
    return render(request, 'dashboard.html', contexto)