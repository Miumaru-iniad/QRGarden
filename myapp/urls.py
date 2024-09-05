from django.urls import path
from myapp import views

urlpatterns = [
    path('<crop_name_en>', views.top, name='top'),
    path('<crop_name_en>/chat', views.chat, name='chat'),
    path('<crop_name_en>/schedule', views.schedule, name='schedule'),
    path('<crop_name_en>/calendar_api/', views.calendar_api, name='calendar_api'),
]