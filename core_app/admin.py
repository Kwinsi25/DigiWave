from django.contrib import admin
from .models import *
# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ('first_name','last_name','email','phone','designation')

# class HostDataInline(admin.TabularInline):
#     model = HostData
#     extra = 0
#     fields = ('company_name','hosting_provider','server_type','plan_package',
#               'server_ip','control_panel','login_url','username','password',
#               'ssh_ftp_access','database_name','db_username','db_password',
#               'purchase_date','expiry_date','server_cost','status','notes')

# class DomainInline(admin.TabularInline):
#     model = Domain
#     extra = 0
#     fields = ('domain_name','purchase_date','expiry_date','left_days','registrar','notes')

# @admin.register(Project)
# class ProjectAdmin(admin.ModelAdmin):
#     list_display = ('project_id','project_name','status','deadline','payment_status','payment_percentage')
#     inlines = [HostDataInline, DomainInline]
#     filter_horizontal = ('team_members',)
admin.site.register(Project)
admin.site.register(HostData)
admin.site.register(Domain)
admin.site.register(User)
admin.site.register(Quotation)
admin.site.register(Client)
admin.site.register(Folder)
admin.site.register(FileDoc)