from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count

# Importamos nuestros modelos y el motor de IA
from .models import Lugar, Categoria, PerfilUsuario, Resena 
from .ml_engine import obtener_recomendaciones_rf


# NUEVA VISTA: Portada de Bienvenida
def landing(request):
    # Si el usuario ya está logueado (tiene cuenta), lo mandamos directo al catálogo
    if request.user.is_authenticated:
        return redirect('index')
    # Si es visitante nuevo, le mostramos la portada
    return render(request, 'landing.html')


# VISTA PRINCIPAL: Catálogo con Inteligencia Artificial
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
    recomendados_ids = [] 
    
    if request.user.is_authenticated and not request.user.is_staff:
        # Le pasamos a la IA la lista de lugares 
        lugares_lista, recomendados_ids = obtener_recomendaciones_rf(request.user, lugares_lista)
        
    # 5. Enviamos todo al HTML
    contexto = {
        'lugares': lugares_lista,
        'categorias': categorias_lista, 
        'recomendados_ids': recomendados_ids, 
    }
    
    return render(request, 'index.html', contexto)


# NUEVA VISTA: Detalle del Lugar y Reseñas
def detalle_lugar(request, lugar_id):
    lugar = get_object_or_404(Lugar, id=lugar_id)
    
    # 1. Traemos todas las reseñas de este lugar, de la más nueva a la más vieja
    resenas = lugar.resenas.all().order_by('-fecha')

    # 2. Lógica para guardar un nuevo comentario
    if request.method == 'POST' and request.user.is_authenticated:
        comentario_texto = request.POST.get('comentario')
        calificacion_num = request.POST.get('calificacion')
        
        if comentario_texto and calificacion_num:
            Resena.objects.create(
                lugar=lugar,
                usuario=request.user,
                calificacion=int(calificacion_num),
                comentario=comentario_texto
            )
            return redirect('detalle_lugar', lugar_id=lugar.id)

    # 3. Enviamos el lugar y sus reseñas al HTML
    contexto = {
        'lugar': lugar,
        'resenas': resenas
    }
    return render(request, 'detalle.html', contexto)


# VISTA DE REGISTRO
def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save() 
            login(request, usuario) 
            return redirect('perfil') 
    else:
        form = UserCreationForm()
        
    contexto = {'form': form}
    return render(request, 'registro.html', contexto)


# NUEVA VISTA: Perfil e Intereses (HU06) - ¡CORREGIDA!
@login_required 
def perfil(request):
    perfil_obj, creado = PerfilUsuario.objects.get_or_create(usuario=request.user)
    todas_categorias = Categoria.objects.all()

    if request.method == 'POST':
        # 1. Guardamos datos demográficos
        perfil_obj.edad = request.POST.get('edad')
        perfil_obj.nacionalidad = request.POST.get('nacionalidad')

        # 2. Guardamos los intereses (checkboxes)
        intereses_seleccionados = request.POST.getlist('intereses') 
        perfil_obj.intereses.set(intereses_seleccionados) 
        perfil_obj.save()

        # 🌟 Redirigimos automáticamente al catálogo usando el nombre correcto de la ruta
        return redirect('index') 

    # 3. Preparamos los datos para mandarlos al HTML
    contexto = {
        'perfil': perfil_obj,
        'categorias': todas_categorias,
        'intereses_actuales': perfil_obj.intereses.values_list('id', flat=True)
    }
    
    # 4. Y finalmente dibujamos la página (eliminamos el render intruso que estaba arriba)
    return render(request, 'perfil.html', contexto)


# NUEVA VISTA: Dashboard Municipal con Chart.js (HU11a)
@staff_member_required 
def dashboard_municipal(request):
    categorias = Categoria.objects.annotate(total=Count('lugar'))
    nombres_categorias = [c.nombre for c in categorias]
    totales_categorias = [c.total for c in categorias]

    lugares_top = Lugar.objects.annotate(promedio=Avg('resenas__calificacion')).order_by('-promedio')[:5]
    nombres_lugares = [l.nombre for l in lugares_top]
    promedios_lugares = [float(l.promedio or 0) for l in lugares_top]

    contexto = {
        'nombres_categorias': nombres_categorias,
        'totales_categorias': totales_categorias,
        'nombres_lugares': nombres_lugares,
        'promedios_lugares': promedios_lugares,
    }
    return render(request, 'dashboard.html', contexto)