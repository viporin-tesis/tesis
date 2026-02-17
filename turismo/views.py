from django.shortcuts import render

def index(request):
    # Esta función busca el archivo 'index.html' y se lo muestra al usuario
    return render(request, 'index.html')