from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cadastros/', include('cadastros.urls', namespace='cadastros')),
]
