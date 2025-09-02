
from django.urls import path
from .views import *
urlpatterns = [
  
    path('', login_view, name='login'),
    
    #login
    path('login/', login_view, name='login'),
    path('user_login/', user_login, name='user_login'),

    # Dashboards
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/', dashboard, name='dashboard'),

    #logout
    path('logout/', user_logout, name='logout'),

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

    #employees
    path('employees/', user_list, name='user_list'),
    path('add_user/', add_user, name='add_user'),
    path('add_fixed_details/', add_fixed_details, name='add_fixed_details'),
    path("get_user/<int:id>/", get_user, name="get_user"),
    path('update_user/<int:id>/', update_user, name='update_user'),
    path('delete_user/<int:id>/', delete_user, name='delete_user'),


    #quotation
    path('quotation/', quotation_list, name='quotation_list'),
    path('add_quotation/', add_quotation, name='add_quotation'),
    path('get_quotation/', get_quotation, name='get_quotation'),
    path('update_quotation/<int:id>/', update_quotation, name='update_quotation'),
    path("download_quotation/<int:id>/", download_quotation, name="download_quotation"),

    #client
    path('client/', client_list, name='client_list'),
    path('add_client/', add_client, name='add_client'),
    path('get_client/', get_client, name='get_client'),
    path('update_client/', update_client, name='update_client'),
    path('delete_client/<int:id>/', delete_client, name='delete_client'),

    #file_docs
    path('file_docs/', file_docs, name='file_docs'),
    path('create_folder/', create_folder, name='create_folder'),
    path('add_file/', add_file, name='add_file'),
    path('get_files/', get_files, name='get_files'),
    path('delete_file/<int:file_id>/', delete_file, name='delete_file'),
    path("delete_files/", delete_files, name="delete_files"),
    path('delete_folder/<int:id>/', delete_folder, name='delete_folder'),
    path('folder/<int:id>/', view_folder, name='view_folder'),


    #payment
    path('payment/', payment_list, name='payment_list'),
    path('add_payment/', add_payment, name='add_payment'),
    path('get_payment/', get_payment, name='get_payment'),

    #designation
    path('designations/', designation_list, name='designation_list'),
    path('add_designation/', add_designation, name='add_designation'),
    path('update_designation/', update_designation, name='update_designation'),
    path('delete_designation/<int:id>/', delete_designation, name='delete_designation'),
    path('get_designation/', get_designation, name='get_designation'),

    # Technology 
    path('technologies/', technology_list, name='technology_list'),
    path('add_technology/', add_technology, name='add_technology'),
    path('get_technology/', get_technology, name='get_technology'),
    path('update_technology/', update_technology, name='update_technology'),
    path('delete_technology/<int:id>/', delete_technology, name='delete_technology'),
]