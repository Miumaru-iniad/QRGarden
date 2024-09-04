from django.urls import path
from myapp import views

urlpatterns = [
    path('<name>', views.top, name='top'),
    path('<name>/chat', views.chat, name='chat'),
    path('<name>/schedule', views.schedule, name='schedule'),
]