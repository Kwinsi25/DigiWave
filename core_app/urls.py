
from django.urls import path
from .views import *
urlpatterns = [
  
    path('', dashboard, name='dashboard'),

    #projects
    path('projects/', project_list, name='project_list'),
    path('projects/save/', save_project, name='save_project'),
    path('get_project_details/', get_project_details, name='get_project_details'),
    path('update_project/<int:id>/', update_project, name='update_project'),
    path('delete_project/<int:id>/', delete_project, name='delete_project'),

    #host
    path('host/', host_list, name='host_list'),
    path('add_host_data/', add_host_data, name='add_host_data'),
    path('get_host_details/', get_host_details, name='get_host_details'),
    path('update_host_data/<int:id>/', update_host_data, name='update_host_data'),
    path('delete_host/<int:id>/', delete_host, name='delete_host'),

    #domain
    path('domain/', domain_list, name='domain_list'),
    path('add-domain/', add_domain, name='add_domain'),
    path('get_domain_details/', get_domain_details, name='get_domain_details'),
    path("update_domain/<int:id>/", update_domain, name="update_domain"),
    path('delete_domain/<int:id>/', delete_domain, name='delete_domain'),

]