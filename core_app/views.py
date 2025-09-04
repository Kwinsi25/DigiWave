from django.shortcuts import render, redirect,get_object_or_404
from django.http import JsonResponse,HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import *
from django.urls import reverse
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.dateparse import parse_date
from collections import defaultdict
import json
from datetime import date
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
# from reportlab.lib.units import mm
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib import colors
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout as django_logout
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Subquery, OuterRef
import os
from django.conf import settings
from decimal import Decimal, InvalidOperation
import asyncio
from playwright.async_api import async_playwright
from django.template.loader import render_to_string
from dateutil.relativedelta import relativedelta
from collections import OrderedDict

def parse_date(val):
    try:
        return datetime.strptime(val, "%Y-%m-%d").date() if val else None
    except (ValueError, TypeError):
        return None
# -----------------------------
# Login View
# -----------------------------
def login_view(request):
    """
    Render the login page.
    """
    return render(request, 'login.html')

def user_login(request):
    """
    Handle login for admin and staff.
    Superusers go to admin dashboard.
    Staff users go to staff dashboard.
    Other users are denied access.
    """
    if request.method == "POST":
        username = request.POST.get("email-username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                if user.is_superuser or user.is_staff:
                    login(request, user)
                    if user.is_superuser:
                        return redirect("admin_dashboard")
                    else:
                        return redirect("dashboard")
                else:
                    messages.error(request, "You are not authorized to access this portal.")
                    return redirect('login')
            else:
                messages.error(request, "Your account is inactive.")
        else:
            messages.error(request, "Invalid username or password.")

        return redirect("login")

    return render(request, "login.html")

# -----------------------------
# logout
# -----------------------------

@login_required
def user_logout(request):
    """
    Log out the user and redirect to login page.
    """
    django_logout(request)
    return redirect('login')

# -----------------------------
# Dashboard
# -----------------------------
@login_required
def admin_dashboard(request):
    """
    Admin dashboard view.
    """
    if not request.user.is_superuser:
        return redirect('login')  # redirect if not superuser
    return render(request, 'admin_dashboard.html')

@login_required
def dashboard(request):
    if not request.user.is_staff:
        return redirect('login')  # redirect if not staff
    return render(request, 'dashboard.html')

# -----------------------------
# Project View
# -----------------------------
def project_list(request): 
    """ Display a list of all projects with their assigned team members. """ 
    # Get dropdown value or default to 20 
    records_per_page = int(request.GET.get('recordsPerPage', 20)) 
    # Ensure page number is valid integer >= 1 
    try: 
        page_number = int(request.GET.get('page', 1)) 
    except ValueError: 
        page_number = 1 
    if page_number < 1: 
        page_number = 1 
    projects = Project.objects.all().prefetch_related('team_members') 
    users = User.objects.all() 
    
    # Paginate 
    paginator = Paginator(projects, records_per_page) 
    page_obj = paginator.get_page(page_number) # Safe pagination 
    print(users) 
    technologies = Technology.objects.all()      
    app_modes = AppMode.objects.all() 
    
    quotations = Quotation.objects.all()
    # Count stats
    total_projects = projects.count()
    ongoing_count = projects.filter(status="Ongoing").count()
    completed_count = projects.filter(status="Completed").count()
    cancelled_count = projects.filter(status="Cancelled").count()
    on_hold_count = projects.filter(status="On Hold").count()
    return render(request, 'project.html', 
                { 'projects': projects, 
                'users': users, 
                'page_obj': page_obj, 
                'quotations': quotations,
                'technologies': technologies,   
                'app_modes': app_modes,        
                'records_per_page': records_per_page, 
                'records_options': [20, 50, 100, 200, 300] ,
                'total_projects': total_projects,
                'ongoing_count': ongoing_count,
                'completed_count': completed_count,
                'cancelled_count': cancelled_count,
                'on_hold_count': on_hold_count,
                   })

def save_project(request):
    """
    Create and save a new project along with assigned team members.
    """
    if request.method == "POST":
        try:
            data = request.POST  # works for normal form POST
            # Get selected quotation object if any
            quotation_id = data.get("quotation")
            quotation = Quotation.objects.filter(id=quotation_id).first() if quotation_id else None
            # Create new Project object
            
            start_date_str = request.POST.get('start_date') or None
            deadline_str = request.POST.get('deadline') or None
            inquiry_date_str= request.POST.get("inquiry_date") or None
            completed_date_str =request.POST.get("completed_date") or None

            project = Project(
                project_name=data.get("project_name"),
                project_type = data.get("project_type"),
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None,
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date() if deadline_str else None,
                
                # app_mode=AppMode.objects.filter(id=data.get("app_mode")).first() if data.get("app_mode") else None,
                status=data.get("status"),
                
                payment_value=data.get("payment_value") or 0,
                payment_status=data.get("payment_status"),
                
                live_link=data.get("live_link"),
                expense=data.get("expense") or None,

                developer_charge=data.get("developer_charge") or None,
                server_charge=data.get("server_charge") or None,
                third_party_api_charge=data.get("third_party_api_charge") or None,
                mediator_charge=data.get("mediator_charge") or None,
                income=Decimal(data.get("income")) if data.get("income") else None,
                free_service=data.get("free_service"),
                postman_collection=data.get("postman_collection"),
                data_folder=data.get("data_folder"),
                other_link=data.get("other_link"),
                
                
                inquiry_date = datetime.strptime(inquiry_date_str, "%Y-%m-%d").date() if inquiry_date_str else None,

                lead_source=data.get("lead_source"),
                quotation_sent=data.get("quotation_sent"),
                demo_given=data.get("demo_given"),
                
                quotation_amount=data.get("quotation_amount") or None,
                approval_amount=data.get("approval_amount") or None,
                
                
                completed_date = datetime.strptime(completed_date_str, "%Y-%m-%d").date() if completed_date_str else None,

                client_industry=data.get("client_industry"),
                contract_signed=data.get("contract_signed"),
                notes=data.get("notes"),
                quotation=quotation
            )

             #  Run backend validation
            project.full_clean()   
            project.save()
            # Handle ManyToMany: App Modes
            app_mode_ids = request.POST.getlist("app_mode")  # get multiple selected IDs
            if app_mode_ids:
                project.app_modes.set(AppMode.objects.filter(id__in=app_mode_ids))
            else:
                project.app_modes.clear()
            # Handle ManyToMany: Technologies
            tech_ids = request.POST.getlist("technologies")
            if tech_ids:
                project.technologies.set(Technology.objects.filter(id__in=tech_ids))
            else:
                project.technologies.clear()
            # Save team members (comma-separated usernames)
            team_member_ids = request.POST.getlist("team_members")  # <-- gets a list of selected IDs as strings
            print(team_member_ids, "team member IDs")

            if team_member_ids:
                members = User.objects.filter(id__in=team_member_ids)
                project.team_members.set(members)
            else:
                project.team_members.clear()

            return JsonResponse({"success": True, "message": "Project saved successfully."})

        except ValidationError as ve:
            return JsonResponse({"success": False, "errors": ve.message_dict}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)

    return JsonResponse({"success": False, "errors": {"__all__": ["Invalid request method."]}}, status=405)



def to_decimal(val):
    try:
        return Decimal(val)
    except (TypeError, ValueError, InvalidOperation):
        return Decimal(0)

def get_project_details(request):
    """
    Fetch details of a single project for viewing or editing.
    """
    project_pk = request.GET.get('id') or request.GET.get('project_id')
    mode = request.GET.get('mode', 'view')  # view or edit

    if not project_pk:
        return JsonResponse({"success": False, "error": "Missing project id"}, status=400)

    try:
        project_pk = int(project_pk)
    except (ValueError, TypeError):
        return JsonResponse({"success": False, "error": "Invalid project id"}, status=400)

    project = get_object_or_404(Project, id=project_pk)

    # Team members for display + ids for edit multi-select
    team_members_display = [
        {
            "id": m.id,
            "name": f"{m.first_name} {m.last_name}".strip(),
            "email": getattr(m, "email", ""),
            "phone": getattr(m, "phone", ""),
            "designation": getattr(m, "designation", ""),
        }
        for m in project.team_members.all()
    ]
     # App Modes for multi-select
    app_modes_display = [
        {"id": am.id, "name": am.name} for am in project.app_modes.all()
    ]
    app_modes_ids = list(project.app_modes.values_list("id", flat=True))
    app_modes_names = [am.name for am in project.app_modes.all()]

    data = {

        "id": project.id,   # numeric id (important)
        "project_id": project.project_id,  
        "project_type" : project.project_type,
        "start_date": project.start_date.strftime('%Y-%m-%d') if project.start_date else None,
        
        "project_name": project.project_name,
        #quotation  
        "quotation_id": project.quotation.id if project.quotation else None,
        "quotation_no": project.quotation.quotation_no if project.quotation else '',
        "client_name": project.quotation.client_name if project.quotation else '',

        "technologies": [t.name for t in project.technologies.all()],
        
         # App Modes
        "app_modes_display": app_modes_display,    
        "app_modes_ids": app_modes_ids,            
        "app_modes_names": app_modes_names,        

        "status": project.status,
        "deadline": project.deadline.strftime('%Y-%m-%d') if project.deadline else None,
        "payment_value": str(project.payment_value) if project.payment_value is not None else '',
        "payment_status": project.payment_status,
        
        "live_link": project.live_link,
        "expense": str(project.expense) if project.expense is not None else '',
        "developer_charge": str(project.developer_charge) if project.developer_charge is not None else '',
        "server_charge": str(project.server_charge) if project.server_charge is not None else '',
        "third_party_api_charge": str(project.third_party_api_charge) if project.third_party_api_charge is not None else '',
        "mediator_charge": str(project.mediator_charge) if project.mediator_charge is not None else '',
        "income": str(project.income) if project.income is not None else '',
        "free_service": project.free_service or '',
        
        "postman_collection": project.postman_collection,
        "data_folder": project.data_folder,
        "other_link": project.other_link,
        
        "inquiry_date": project.inquiry_date.strftime('%Y-%m-%d') if project.inquiry_date else None,
        "lead_source": project.lead_source,
        "quotation_sent": project.quotation_sent,
        "demo_given": project.demo_given,
        "quotation_amount": str(project.quotation_amount) if project.quotation_amount is not None else '',
        "quotation": project.quotation.quotation_no if project.quotation else None,
        # "client_name": project.quotation.client_name if project.quotation else None,
        "approval_amount": str(project.approval_amount) if project.approval_amount is not None else '',
        "completed_date": project.completed_date.strftime('%Y-%m-%d') if project.completed_date else None,
        "client_industry": project.client_industry,
        "contract_signed": project.contract_signed,
        "notes":project.notes,
        "team_members_display": team_members_display,
        "team_members_ids": list(project.team_members.values_list('id', flat=True)),
        # ManyToMany IDs
        "technologies_ids": list(project.technologies.values_list("id", flat=True)),
    }

    return JsonResponse({"success": True, "mode": mode, "project": data})

def update_project(request, id):
    """
    Update an existing project with new data from the form.
    """
    project = get_object_or_404(Project, id=id)
    # Now you have the full project object
    print(project.project_name)  # for testing
    if request.method == "POST":
        try:
            data = request.POST
            quotation_id = data.get("quotation")
            if quotation_id:
                try:
                    project.quotation = Quotation.objects.get(id=quotation_id)
                except Quotation.DoesNotExist:
                    project.quotation = None
            else:
                project.quotation = None
            # Basic info
            project.project_name = data.get("project_name")
            project.project_type = data.get("project_type")
            # project.start_date = data.get("start_date") or None
            project.start_date = parse_date(request.POST.get('start_date'))
            # project.deadline = data.get("deadline") or None
            project.deadline = parse_date(request.POST.get('deadline'))
            
            project.status = data.get("status")

            # Payment info
            project.payment_value = to_decimal(data.get("payment_value"))
            project.payment_status = data.get("payment_status")

            # Links
            project.live_link = data.get("live_link")
            project.postman_collection = data.get("postman_collection")
            project.data_folder = data.get("data_folder")
            project.other_link = data.get("other_link")

            # Financials
            project.expense = to_decimal(data.get("expense"))
            project.developer_charge = to_decimal(data.get("developer_charge"))
            project.server_charge = to_decimal(data.get("server_charge"))
            project.third_party_api_charge = to_decimal(data.get("third_party_api_charge"))
            project.mediator_charge = to_decimal(data.get("mediator_charge"))
            project.income = to_decimal(data.get("income"))
            project.free_service = data.get("free_service")

            # Sales / lead tracking
            # project.inquiry_date = parse_date(data.get("inquiry_date"))
            project.inquiry_date = parse_date(request.POST.get('inquiry_date'))
            project.lead_source = data.get("lead_source")
            project.quotation_sent = data.get("quotation_sent")
            project.demo_given = data.get("demo_given")
            project.quotation_amount = to_decimal(data.get("quotation_amount"))
            project.approval_amount = to_decimal(data.get("approval_amount"))

            # Completion / client info
            # project.completed_date = parse_date(data.get("completed_date"))
            project.completed_date = parse_date(request.POST.get('completed_date'))
            project.client_industry = data.get("client_industry")
            project.contract_signed = data.get("contract_signed")
            project.notes = data.get("notes")
            # Save project first before updating many-to-many
            project.full_clean()

            project.save()

            # ManyToMany: Technologies
            tech_ids = request.POST.getlist("technologies")
            project.technologies.set(Technology.objects.filter(id__in=tech_ids))
            
            # Team members (ManyToMany)
            team_member_ids = request.POST.getlist("team_members")
            members = User.objects.filter(id__in=team_member_ids)
            project.team_members.set(members)

             # ManyToMany: App Modes
            app_mode_ids = request.POST.getlist("app_mode")  # <-- multi-select field name
            project.app_modes.set(AppMode.objects.filter(id__in=app_mode_ids))
            
            return JsonResponse({"success": True, "message": "Project updated successfully!"})

        except ValidationError as ve:
            return JsonResponse({"success": False, "errors": ve.message_dict}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)

    return JsonResponse({"success": False, "errors": {"__all__": ["Invalid request method."]}}, status=405)


def delete_project(request, id):
    """
    Delete a project by its ID.
    """
    if request.method == "POST":
        try:
            project = get_object_or_404(Project, id=id)
            project.delete()
            return JsonResponse({"success": True, "message": "Project deleted successfully!"})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error deleting project: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

# -----------------------------
# Host View
# -----------------------------
def host_list(request):
    """
    Display all host/server records with related projects.
    """
    records_per_page = int(request.GET.get('recordsPerPage', 20))

    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    if page_number < 1:
        page_number = 1

    projects = Project.objects.all()
    host_data_list = HostData.objects.prefetch_related('project').all()
    print(host_data_list)

    # Dashboard counts
    total_servers = host_data_list.count()
    running_servers = host_data_list.filter(status="Active").count()
    down_servers = host_data_list.filter(status="Inactive").count()

     # Days left to expiry
    expiring_soon = host_data_list.filter(
        expiry_date__isnull=False,
        expiry_date__lte=date.today() + timedelta(days=30)
    ).count()  # optional card

    paginator = Paginator(host_data_list, records_per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, 'hosting.html', {
        'projects': projects,
        'page_obj': page_obj,
        'records_per_page': records_per_page,
        'records_options': [20, 50, 100, 200, 300],
        'total_servers': total_servers,
        'running_servers': running_servers,
        'down_servers': down_servers,
        'expiring_soon': expiring_soon,
    })


def add_host_data(request):
    """
    Create and save a new host/server record.
    """
    if request.method == "POST":
        try:
            # multiple projects selected
            project_ids = request.POST.getlist("project")
            projects = Project.objects.filter(id__in=project_ids) if project_ids else Project.objects.none()
            
            host_data = HostData(
                # project=project,
                hosting_provider=request.POST.get("hosting_provider"),
                server_name=request.POST.get("server_name"),
                server_type=request.POST.get("server_type"),
                plan_package=request.POST.get("plan_package"),
                server_ip = request.POST.get("server_ip") or None,
                operating_system=request.POST.get("operating_system"),
                login_url=request.POST.get("login_url"),
                username=request.POST.get("username"),
                password=request.POST.get("password"),
                ssh_username = request.POST.get("ssh_username"),
                ssh_ftp_access=request.POST.get("ssh_ftp_access"),
                database_name=request.POST.get("database_name"),
                db_username=request.POST.get("db_username"),
                db_password=request.POST.get("db_password"),
                purchase_date=parse_date(request.POST.get("purchase_date")),
                expiry_date=parse_date(request.POST.get("expiry_date")),
                server_cost=request.POST.get("server_cost") or None,
                memory=request.POST.get("memory_usage"),
                RAM=request.POST.get("disk_space"),
                backup_status=request.POST.get("backup_status"),
                linked_services=request.POST.get("linked_services"),
                status=request.POST.get("status"),
                notes=request.POST.get("notes"),
            )

            # run model-level validations
            host_data.full_clean()
            host_data.save()

            # set ManyToMany projects
            host_data.project.set(projects)

            return JsonResponse({"success": True, "message": "Host Data saved successfully!"})

        except ValidationError as ve:
            # ve.message_dict is a dict only if you raise ValidationError({'field': ['msg']})
            errors = ve.message_dict if hasattr(ve, "message_dict") else {"__all__": ve.messages}
            return JsonResponse({"success": False, "errors": errors}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)

    return JsonResponse({"success": False, "errors": {"__all__": ["Invalid request method."]}}, status=405)


def get_host_details(request):
    """
    Fetch details of a single host/server record.
    """
    host_id = request.GET.get('id')
    mode = request.GET.get('mode', 'view')  # view or edit

    if not host_id:
        return JsonResponse({"success": False, "error": "No host ID provided"}, status=400)

    try:
        host_id = int(host_id)
    except ValueError:
        return JsonResponse({"success": False, "error": "Invalid host ID"}, status=400)
    
    host = get_object_or_404(HostData, id=host_id)
    # ManyToMany → return list of {id, name}
    projects = [{"id": p.id, "name": p.project_name} for p in host.project.all()]
    data = {
        "host_id": host.id,
        "projects": projects,   # list of projects
        "server_name": host.server_name,
        "hosting_provider": host.hosting_provider,
        "server_type": host.server_type,
        "plan_package": host.plan_package,
        "server_ip": host.server_ip,
        "operating_system": host.operating_system,
        "login_url": host.login_url,
        "username": host.username,
        "password": host.password,
        "ssh_username": host.ssh_username,
        "ssh_ftp_access": host.ssh_ftp_access,
        "database_name": host.database_name,
        "db_username": host.db_username,
        "db_password": host.db_password,
        "purchase_date": host.purchase_date.strftime("%Y-%m-%d") if host.purchase_date else "",
        "expiry_date": host.expiry_date.strftime("%Y-%m-%d") if host.expiry_date else "",
        "server_cost": str(host.server_cost) if host.server_cost else None,
        "status": host.status,
       "memory": host.memory,
        "ram": host.RAM,  # send as ram

        "backup_status": host.backup_status,
        "linked_services": host.linked_services,
        "notes": host.notes,
    }
    
    return JsonResponse({"success": True, "host": data})

def update_host_data(request, id):
    """
    Update an existing host/server record.
    """
    if request.method == "POST":
        host_id = request.POST.get("host_id")
        if not host_id:
            messages.error(request, "Host ID is missing.")
            return redirect('host_list')

        try:
            host = get_object_or_404(HostData, id=int(host_id))

            # ---- Projects (ManyToMany) ----
            project_ids = request.POST.getlist("project")  # multiple selected
            if project_ids:
                projects = Project.objects.filter(id__in=project_ids)
                if not projects.exists():
                    messages.error(request, "Invalid project(s) selected.")
                    return redirect("host_list")
                host.project.set(projects)  
            else:
                host.project.clear()  # allow "no project"

            # Update all fields

            host.server_name = request.POST.get("server_name")
            host.hosting_provider = request.POST.get("hosting_provider")
            host.server_type = request.POST.get("server_type")
            host.plan_package = request.POST.get("plan_package")
            host.server_ip = request.POST.get("server_ip")

            host.operating_system = request.POST.get("operating_system")

            host.login_url = request.POST.get("login_url")
            host.username = request.POST.get("username")
            host.password = request.POST.get("password")
            host.ssh_username = request.POST.get("ssh_username")
            host.ssh_ftp_access = request.POST.get("ssh_ftp_access")
            host.database_name = request.POST.get("database_name")
            host.db_username = request.POST.get("db_username")
            host.db_password = request.POST.get("db_password")
            host.purchase_date = request.POST.get("purchase_date") or None
            host.expiry_date = request.POST.get("expiry_date") or None
            host.server_cost = request.POST.get("server_cost") or None

            host.memory = request.POST.get("memory_usage")
            host.RAM = request.POST.get("disk_space")
            host.backup_status = request.POST.get("backup_status")
            host.linked_services = request.POST.get("linked_services")
            host.status = request.POST.get("status")
            host.notes = request.POST.get("notes")

            host.full_clean()
            host.save()
            return JsonResponse({"success": True, "message": "Host Data updated successfully!"})

        except ValidationError as ve:
            return JsonResponse({"success": False, "errors": ve.message_dict}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)

    return JsonResponse({"success": False, "errors": {"__all__": ["Invalid request method."]}}, status=405)

def delete_host(request, id):
    """
    Delete a host/server record by its ID (AJAX).
    """
    if request.method == "POST":
        try:
            host = get_object_or_404(HostData, id=id)
            host.delete()
            return JsonResponse({"success": True, "message": "Host deleted successfully!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

# -----------------------------
# Domain View
# -----------------------------
def domain_list(request):
    """
    Display all domain records with related projects and hosting data, paginated.
    """
    records_per_page = int(request.GET.get('recordsPerPage', 20))

    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    if page_number < 1:
        page_number = 1

    projects = Project.objects.all()

    #For HostData also you changed to ManyToMany
    host_data_list = HostData.objects.prefetch_related("project").all()

    #For Domain use prefetch_related instead of select_related
    domains = Domain.objects.prefetch_related("project").order_by("id")

    # Paginate domains
    paginator = Paginator(domains, records_per_page)
    page_obj = paginator.get_page(page_number)

    #Dashboard counts
    today = timezone.now().date()

    total_domains = domains.count()

    active_domains = domains.filter(expiry_date__gte=today).count()

    expired_domains = domains.filter(expiry_date__lt=today).count()

    expiring_soon_domains = domains.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    ).count()

    return render(request, "domain.html", {
        "projects": projects,
        "host_data_list": host_data_list,
        "page_obj": page_obj,  # paginated domains
        "records_per_page": records_per_page,
        "records_options": [20, 50, 100, 200, 300],
        "total_domains": total_domains,
        "active_domains": active_domains,
        "expired_domains": expired_domains,
        "expiring_soon_domains": expiring_soon_domains,
    })


def add_domain(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "errors": {"__all__": ["Invalid request method."]}}, status=405)

    try:
        # Projects (ManyToMany)
        project_ids = request.POST.getlist('projects')
        projects = Project.objects.filter(id__in=project_ids) if project_ids else Project.objects.none()

        # Dates (optional)
        purchase_date = parse_date(request.POST.get("purchaseDate")) or None
        expiry_date = parse_date(request.POST.get("expiryDate")) or None
        ssl_expiry = parse_date(request.POST.get("sslExpiry")) or None

        # Payment details (optional)
        payment_method = request.POST.get('paymentMethod') or None
        payment_details = {}
        if payment_method == "Bank Transfer":
            payment_details = {
                "bank_name": request.POST.get("bank_name") or "",
                "account_no": request.POST.get("account_no") or "",
                "ifsc_code": request.POST.get("ifsc_code") or "",
            }
        elif payment_method == "UPI":
            payment_details = {"upi_id": request.POST.get("upi_id") or ""}
        elif payment_method == "Cheque":
            payment_details = {
                "cheque_no": request.POST.get("cheque_no") or "",
                "cheque_name": request.POST.get("cheque_name") or "",
            }
        elif payment_method == "Other":
            payment_details = {"other_details": request.POST.get("other_details") or ""}

        # Numeric field (optional)
        domain_charge = request.POST.get("domainCharge")
        if domain_charge:
            try:
                domain_charge = float(domain_charge)
            except ValueError:
                domain_charge = None
        else:
            domain_charge = None

        # Boolean fields
        dns_configured = request.POST.get('dnsConfigured') == "True"
        ssl_installed = request.POST.get('sslInstalled') == "True"

        # Create domain instance
        domain = Domain(
            domain_name=request.POST.get('domainName') or "",
            sub_domain1=request.POST.get('subDomain1') or "",
            sub_domain2=request.POST.get('subDomain2') or "",
            purchase_date=purchase_date,
            expiry_date=expiry_date,
            registrar=request.POST.get('registrar') or "",
            renewal_status=request.POST.get('renewalStatus') or "",
            auto_renewal=request.POST.get('autoRenewal') or "",
            dns_configured=dns_configured,
            nameservers=request.POST.get('nameservers') or "",
            ssl_installed=ssl_installed,
            ssl_expiry=ssl_expiry,
            credentials_user=request.POST.get('credentialsUser') or "",
            credentials_pass=request.POST.get('credentialsPass') or "",
            linked_services=request.POST.get('linkedServices') or "",
            notes=request.POST.get('notes') or "",
            domain_charge=domain_charge,
            client_payment_status=request.POST.get('clientPaymentStatus') or "",
            payment_method=payment_method,
            payment_mode=request.POST.get('paymentMode') or "",
            payment_details=payment_details or None
        )

        # Optional left_days calculation
        if expiry_date:
            today = timezone.now().date()
            domain.left_days = max((expiry_date - today).days, 0)

        domain.full_clean()  # still validate model fields
        domain.save()

        # Set ManyToMany
        domain.project.set(projects)

        return JsonResponse({
            "success": True,
            "message": f"Domain '{domain.domain_name}' added successfully!",
            "domain_id": domain.id
        })

    except ValidationError as ve:
        errors = ve.message_dict if hasattr(ve, "message_dict") else {"__all__": ve.messages}
        return JsonResponse({"success": False, "errors": errors}, status=400)

    except Exception as e:
        return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)


def get_domain_details(request):
    """
    Fetch details of a single domain record.
    """
    domain_id = request.GET.get('id')
    mode = request.GET.get('mode', 'view')  # 'view' or 'edit'

    if not domain_id:
        return JsonResponse({"success": False, "error": "No domain ID provided"}, status=400)

    try:
        domain_id = int(domain_id)
    except ValueError:
        return JsonResponse({"success": False, "error": "Invalid domain ID"}, status=400)

    domain = get_object_or_404(Domain, id=domain_id)
    print(domain.credentials_pass)
    data = {
        "id": domain.id,
        # ManyToMany projects → return both IDs and names
        "projects": [
            {"id": p.id, "name": p.project_name, "code": p.project_id}
            for p in domain.project.all()
        ],
        "domain_name": domain.domain_name,
        "sub_domain1": domain.sub_domain1,
        "sub_domain2": domain.sub_domain2,
        "registrar": domain.registrar,
        "purchase_date": domain.purchase_date.strftime("%Y-%m-%d") if domain.purchase_date else None,
        "expiry_date": domain.expiry_date.strftime("%Y-%m-%d") if domain.expiry_date else None,
        "renewal_status": domain.renewal_status,
        "auto_renewal": domain.auto_renewal,
        "dns_configured": domain.dns_configured,
        "nameservers": domain.nameservers,
        "ssl_installed": domain.ssl_installed,
        "ssl_expiry": domain.ssl_expiry.strftime("%Y-%m-%d") if domain.ssl_expiry else None,
        "credentials_user": domain.credentials_user,
        "credentials_pass": domain.credentials_pass ,
        "linked_services": domain.linked_services,
        "notes": domain.notes,
        "domain_charge": str(domain.domain_charge) if domain.domain_charge else "0.00",
        "client_payment_status": domain.client_payment_status,
        "payment_method": domain.payment_method,
        "payment_mode": domain.payment_mode,
        "payment_details": domain.payment_details, 
    }

    return JsonResponse({"success": True, "domain": data})

def update_domain(request, id):
    """
    Update existing domain record
    """
    if request.method == "POST":
        try:
            domain = get_object_or_404(Domain, id=id)

            # ==================== PROJECTS ====================
            project_ids = request.POST.getlist('projects')
            if project_ids:
                projects = Project.objects.filter(id__in=project_ids)
                domain.project.set(projects)  # Replace all projects
            else:
                domain.project.clear()

            # ==================== DATES ====================

            domain.purchase_date = parse_date(request.POST.get('purchaseDate'))
            domain.expiry_date = parse_date(request.POST.get('expiryDate'))
            domain.ssl_expiry = parse_date(request.POST.get('sslExpiry'))

            # ==================== TEXT FIELDS ====================
            domain.domain_name = request.POST.get('domainName')
            domain.sub_domain1 = request.POST.get('subDomain1')
            domain.sub_domain2 = request.POST.get('subDomain2')
            domain.registrar = request.POST.get('registrar')
            domain.renewal_status = request.POST.get('renewalStatus')
            domain.nameservers = request.POST.get('nameservers')
            domain.credentials_user = request.POST.get('credentialsUser')
            domain.credentials_pass = request.POST.get('credentialsPass')
            domain.linked_services = request.POST.get('linkedServices')
            domain.notes = request.POST.get('notes')

            # ==================== BOOLEAN FIELDS ====================
            domain.dns_configured = request.POST.get('dnsConfigured') in ["True", "on", "1"]
            domain.ssl_installed = request.POST.get('sslInstalled') in ["True", "on", "1"]

            # ==================== EXTRA FIELDS ====================
            domain.auto_renewal = request.POST.get('autoRenewal')  # On / Off
            domain.domain_charge = request.POST.get('domainCharge') or None
            domain.client_payment_status = request.POST.get('clientPaymentStatus')  # Pending / Received
            domain.payment_mode = request.POST.get('paymentMode')  # Client / Company
            domain.payment_method = request.POST.get('paymentMethod')  # Bank Transfer / UPI / Cash / Cheque / Other

            # ==================== PAYMENT DETAILS ====================
            payment_details = {}
            if domain.payment_method == "Bank Transfer":
                payment_details = {
                    "bank_name": request.POST.get("bank_name"),
                    "account_no": request.POST.get("account_no"),
                    "ifsc_code": request.POST.get("ifsc_code"),
                }
            elif domain.payment_method == "UPI":
                payment_details = {
                    "upi_id": request.POST.get("upi_id"),
                }
            elif domain.payment_method == "Cheque":
                payment_details = {
                    "cheque_no": request.POST.get("cheque_no"),
                    "cheque_name": request.POST.get("cheque_name"),
                }
            elif domain.payment_method == "Other":
                payment_details = {
                    "description": request.POST.get("other_details"),
                }

            domain.payment_details = payment_details

            # ==================== LEFT DAYS ====================
            if domain.expiry_date:
                today = timezone.now().date()
                domain.left_days = max((domain.expiry_date - today).days, 0)
            else:
                domain.left_days = None

            # ==================== SAVE ====================
            domain.save()
            messages.success(request, f"Domain '{domain.domain_name}' updated successfully!")

        except Exception as e:
            messages.error(request, f"Error updating domain: {str(e)}")

        return redirect('domain_list')

    messages.warning(request, "Invalid request method.")
    return redirect('domain_list')

def delete_domain(request, id):
    """
    Delete a domain record by its ID.
    """
    if request.method == "POST":
        try:
            domain = get_object_or_404(Domain, id=id)
            domain_name = domain.domain_name
            domain.delete()

            #Add Django success message
            messages.success(request, f"Domain '{domain_name}' deleted successfully!")

            #Redirect URL to the domain list page
            return JsonResponse({
                "success": True,
                "redirect_url": redirect('domain_list').url
            })
        except Exception as e:
            messages.error(request, f"Error deleting domain: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": str(e),
                "redirect_url": redirect('domain_list').url
            })

    messages.warning(request, "Invalid request method.")
    return JsonResponse({
        "success": False,
        "error": "Invalid request method",
        "redirect_url": redirect('domain_list').url
    })

# -----------------------------
# User Management
# -----------------------------
def user_list(request):
    records_per_page = int(request.GET.get('recordsPerPage', 20))

    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    if page_number < 1:
        page_number = 1
    users = User.objects.all().order_by('id')
     # Paginate
    paginator = Paginator(users, records_per_page)
    page_obj = paginator.get_page(page_number)

    # Statistics
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    new_users_this_month = users.filter(
        created_at__year=timezone.now().year,
        created_at__month=timezone.now().month
    ).count()
    inactive_users = users.filter(is_active=False).count()
    designations = Designation.objects.all().order_by("title")
    technologies = Technology.objects.all().order_by("name") 
    context = {
        "page_obj": page_obj,  # paginated domains
        'users':users,
        "records_per_page": records_per_page,
        "records_options": [20, 50, 100, 200, 300],
        'total_users': total_users,
        'active_users': active_users,
        'new_users_this_month': new_users_this_month,
        'inactive_users': inactive_users,
        "designations": designations,
        "technologies": technologies
    }

    return render(request, 'user.html', context)

def add_user(request):
    if request.method == "POST":
        try:
            user = User(
                first_name=request.POST.get("first_name"),
                last_name=request.POST.get("last_name"),
                username=request.POST.get("username"),
                email=request.POST.get("email"),
                phone=request.POST.get("phone") or None,
                password=request.POST.get("password"),
                salary=request.POST.get("salary") or None,
                joining_date=parse_date(request.POST.get("joining_date")),
                last_date=parse_date(request.POST.get("last_date")),
                birth_date=parse_date(request.POST.get("birth_date")),
                gender=request.POST.get("gender") or None,
                marital_status=request.POST.get("marital_status") or None,
                employee_type=request.POST.get("employee_type") or None,
                current_address=request.POST.get("current_address") or None,
                permanent_address=request.POST.get("permanent_address") or None,
                document_link=request.POST.get("document_link") or None,
                account_holder=request.POST.get("account_holder") or None,
                account_number=request.POST.get("account_number") or None,
                ifsc_code=request.POST.get("ifsc_code") or None,
                branch=request.POST.get("branch") or None,
                is_active=True if request.POST.get("is_active") == "on" else False,
            )

            # Handle profile picture upload
            if "profile_picture" in request.FILES:
                user.profile_picture = request.FILES["profile_picture"]

            # run model validations
            user.full_clean()
            user.save()
            # Handle many-to-many designations
            designation_ids = request.POST.getlist("designations")
            if designation_ids:
                user.designations.set(designation_ids)

            # Handle many-to-many technologies
            technology_ids = request.POST.getlist("technologies")
            if technology_ids:
                user.technologies.set(technology_ids)

            return JsonResponse({"success": True, "message": "User added successfully!"})
        except ValidationError as ve:
            flat_errors = []
            detailed_errors = {}

            for field, messages in ve.message_dict.items():
                for msg in messages:
                    flat_errors.append(msg)   # just the text messages
                detailed_errors[field] = messages

            return JsonResponse(
                {
                    "success": False,
                    "flat_errors": flat_errors,
                    "detailed_errors": detailed_errors
                },
                status=400
            )

        except Exception as e:
            return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)

    return JsonResponse({"success": False, "errors": {"__all__": ["Invalid request method"]}}, status=405)

def add_fixed_details(request):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "errors": {"__all__": ["Invalid request method"]}
        }, status=405)

    try:
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, pk=user_id)

        if user.employee_type != "fixed":
            return JsonResponse({
                "success": False,
                "errors": {"__all__": ["Details can only be added for fixed employees."]}
            }, status=400)

        # Collect data from form
        amount = request.POST.get("amount")
        date = request.POST.get("date")
        description = request.POST.get("description")

         # Get existing entries or initialize empty list
        existing_details = user.fixed_employee_details or []
        if not isinstance(existing_details, list):
            # In case the old data is a dict, convert it to list
            existing_details = [existing_details]

        # Append new entry
        new_entry = {
            "amount": float(amount) if amount else 0,
            "date": date,
            "description": description
        }
        existing_details.append(new_entry)

        # Save back to JSONField
        user.fixed_employee_details = existing_details
        user.save()

        return JsonResponse({
            "success": True,
            "message": "Fixed employee details saved successfully!"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "errors": {"__all__": [str(e)]}
        }, status=500)
    

def add_hourly_details(request):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "errors": {"__all__": ["Invalid request method"]}
        }, status=405)

    try:
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, pk=user_id)

        if user.employee_type != "hourly":
            return JsonResponse({
                "success": False,
                "errors": {"__all__": ["Details can only be added for hourly employees."]}
            }, status=400)

        # Collect data from form
        amount = float(request.POST.get("amount") or 0)
        total_hours = float(request.POST.get("working_hours") or 0)
        date = request.POST.get("date")
        description = request.POST.get("description") or ""

        if amount <= 0 or total_hours <= 0:
            return JsonResponse({
                "success": False,
                "errors": {"__all__": ["Amount and working hours must be greater than zero."]}
            }, status=400)

        if not date:
            return JsonResponse({
                "success": False,
                "errors": {"__all__": ["Date is required."]}
            }, status=400)

        final_total = round(amount * total_hours, 2)

        # Get existing entries or initialize empty list
        existing_details = user.hourly_employee_details or []
        if not isinstance(existing_details, list):
            existing_details = [existing_details]

        # Append new entry
        new_entry = {
            "amount": amount,
            "date": date,
            "description": description,
            "total_hours": total_hours,
            "final_total": final_total
        }
        existing_details.append(new_entry)

        # Save back to JSONField
        user.hourly_employee_details = existing_details
        user.save()

        return JsonResponse({
            "success": True,
            "message": "Hourly employee details saved successfully!"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "errors": {"__all__": [str(e)]}
        }, status=500)

def get_user(request, id):
    """
    Return JSON details of a user for editing in modal.
    """
    user = get_object_or_404(User, id=id)
    print(f"Fetching details for user ID: {user.id}, Picture: {user.profile_picture.url if user.profile_picture else 'No picture'}")
     # Calculate total salary/fixed amount
    total_paid = 0
    fixed_details = []
    if user.employee_type == "salary" and user.joining_date and user.salary:
        today = date.today()
        months_diff = (today.year - user.joining_date.year) * 12 + (today.month - user.joining_date.month) + 1
        total_paid = float(user.salary) * months_diff

    elif user.employee_type == "fixed" and user.fixed_employee_details:
        # fixed_employee_details can be list or single dict
        details = user.fixed_employee_details
        if isinstance(details, dict):
            details = [details]
        total_paid = sum(d.get("amount", 0) for d in details)
        fixed_details = details 

   
    hourly_details = []
    month_filter = request.GET.get("month") 
    print(month_filter)
    hourwise = []
    if user.employee_type == "hourly" and user.hourly_employee_details:
        today = date.today()
        five_months_ago = today - relativedelta(months=5)

        combined = defaultdict(lambda: {"total_hours": 0, "final_total": 0, "descriptions": []})

        for d in user.hourly_employee_details:
            try:
                entry_date = datetime.strptime(d["date"], "%Y-%m-%d").date()
            except Exception:
                continue

            if entry_date >= five_months_ago.replace(day=1):
                month_key = entry_date.strftime("%Y-%m")

                combined[month_key]["total_hours"] += d.get("total_hours", 0)
                combined[month_key]["final_total"] += d.get("final_total", 0)
                combined[month_key]["descriptions"].append(d.get("description", "-"))

                # Apply month filter for raw rows
                if not month_filter or month_key == month_filter:
                    hourwise.append(d)

        hourly_details = [
            {
                "month": month_key,
                "total_hours": info["total_hours"],
                "final_total": info["final_total"],
                "description": " | ".join(info["descriptions"]),
            }
            for month_key, info in sorted(combined.items(), reverse=True)
        ]
        print(hourwise)
    return JsonResponse({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "password": user.password,
        "email": user.email,
        "phone": user.phone,
        "gender": user.gender if user.gender else None,
        "employee_type": user.employee_type if user.employee_type else None,
        "salary": total_paid,
        "joining_date": user.joining_date.strftime("%Y-%m-%d") if user.joining_date else None,
    
        "last_date": user.last_date.strftime("%Y-%m-%d") if user.last_date else None,
        "birth_date": user.birth_date.strftime("%Y-%m-%d") if user.birth_date else None,
        "marital_status": user.marital_status if user.marital_status else None,
        "current_address": user.current_address if user.current_address else None,
        "permanent_address": user.permanent_address if user.permanent_address else None,
        "document_link": user.document_link,
        "account_holder": user.account_holder if user.account_holder else None,
        "account_number": user.account_number if user.account_number else None,
        "ifsc_code": user.ifsc_code if user.ifsc_code else None,
        "branch": user.branch if user.branch else None,
        # Return many-to-many relationships as id + name
        "designations": [{"id": d.id, "title": d.title} for d in user.designations.all()],
        "technologies": [{"id": t.id, "name": t.name} for t in user.technologies.all()],
        "is_active": user.is_active,
        "projects": [p.project_name for p in getattr(user, "projects").all()] if hasattr(user, "projects") else [],
        "profile_picture_url": request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
         "fixed_employee_details": fixed_details,
        "hourly_employee_details": hourly_details,
        "hourwise":hourwise

    })

def update_user(request, id):
    print(f"Updating user with ID: {id}")
    """
    Update an existing user record via AJAX.
    """
    if request.method == "POST":
        try:
            user = get_object_or_404(User, id=id)

            # Basic fields
            user.first_name = request.POST.get("first_name") or ""
            user.last_name = request.POST.get("last_name") or ""
            user.username = request.POST.get("username") or ""
            user.email = request.POST.get("email") or ""
            user.phone = request.POST.get("phone") or None

            # Password (update only if provided)
            password = request.POST.get("password")
            if password:
                user.password = password  # 

            # Job details
            user.employee_type = request.POST.get("employee_type") or None
            salary = request.POST.get("salary")
            user.salary = salary if salary else None
            user.joining_date = parse_date(request.POST.get("joining_date"))
            user.last_date = parse_date(request.POST.get("last_date"))
            # Personal details
            user.gender = request.POST.get("gender") or None
            user.birth_date = parse_date(request.POST.get("birth_date"))
            user.marital_status = request.POST.get("marital_status") or None

            # Addresses and document link
            user.current_address = request.POST.get("current_address") or None
            user.permanent_address = request.POST.get("permanent_address") or None
            user.document_link = request.POST.get("document_link") or None

            # Bank details
            user.account_holder = request.POST.get("account_holder") or None
            user.account_number = request.POST.get("account_number") or None
            user.ifsc_code = request.POST.get("ifsc_code") or None
            user.branch = request.POST.get("branch") or None

            # Checkbox
            user.is_active = True if request.POST.get("is_active") else False

            # Profile picture
            if request.FILES.get("profile_picture"):
                user.profile_picture = request.FILES["profile_picture"]

            # Validate and save
            user.full_clean()
            user.save()

            # ManyToMany updates
            designations = request.POST.getlist("designations")
            technologies = request.POST.getlist("technologies")
            user.designations.set(designations)
            user.technologies.set(technologies)

            return JsonResponse({"success": True, "message": "User updated successfully!"})
        except ValidationError as ve:
            return JsonResponse({"success": False, "errors": ve.message_dict})
        except Exception as e:
            return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}})

    return JsonResponse({"success": False, "errors": {"__all__": ["Invalid request method."]}})

def delete_user(request, id):
    if request.method == "POST":
        try:
            user = get_object_or_404(User, id=id)
            user.delete()
            return JsonResponse({"success": True, "message": "User deleted successfully!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)


# -----------------------------
# Quotation View
# -----------------------------

def quotation_list(request):
    records_per_page = int(request.GET.get('recordsPerPage', 20))

    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    if page_number < 1:
        page_number = 1
    quotations = Quotation.objects.all()

     # Paginate
    paginator = Paginator(quotations, records_per_page)
    page_obj = paginator.get_page(page_number)
    
    
    # Today date for status check
    today = timezone.now().date()

    # Stats (optional, for cards like servers)
    total_quotations = quotations.count()
    active_quotations = quotations.filter(valid_until__gte=today).count()
    expired_quotations = quotations.filter(valid_until__lt=today).count()
    this_month_quotations = quotations.filter(date__month=today.month, date__year=today.year).count()

    # get all users
    users = User.objects.all()
    next_no = Quotation.get_next_quotation_no()
    print(next_no) 
    context = {
        "page_obj": page_obj,
        "records_per_page": records_per_page,
        "records_options": [20, 50, 100, 200, 300],
        "today": today,
        "quotation_no":next_no,
        "total_quotations": total_quotations,
        "active_quotations": active_quotations,
        "expired_quotations": expired_quotations,
        "this_month_quotations": this_month_quotations,
        "users": users,
    }
    return render(request, "quotation.html", context)


def add_quotation(request):
    if request.method == "POST":
        try:
            data = request.POST
            files = request.FILES

            # prepared_by user (by ID)
            prepared_by_user = None
            prepared_by_value = data.get("prepared_by")
            if prepared_by_value:
                try:
                    prepared_by_user = User.objects.get(id=prepared_by_value)
                except User.DoesNotExist:
                    prepared_by_user = None
            
            # Helper: parse dynamic service rows
            def parse_services():
                services = {"web": [], "mobile": [], "cloud": [], "ai_ml": []}

                # Find all indices by checking keys like service[1][category]
                indices = set()
                for key in data:
                    if key.startswith("service[") and key.endswith("][category]"):
                        idx = key.split("[")[1].split("]")[0]
                        indices.add(idx)

                for index in indices:
                    category = data.get(f"service[{index}][category]")
                    description = data.get(f"service[{index}][description]")
                    quantity = int(data.get(f"service[{index}][quantity]") or 1)
                    unit_price = float(data.get(f"service[{index}][unit_price]") or 0)
                    if category in services:
                        services[category].append({
                            "description": description,
                            "quantity": quantity,
                            "unit_price": unit_price
                        })

                return services


            services = parse_services()
            
            # helper for JSON fields
            def extract_json(prefix):
                included = data.get(f"{prefix}[included]") == "true"
                if not included:
                    return []  # empty list if not selected

                duration_raw = data.get(f"{prefix}[duration]") or ""
                
                import re
                # Match number + optional unit
                match = re.match(r'(\d+)\s*(\w+)?', duration_raw.strip())
                if match:
                    duration_value = int(match.group(1))       # numeric part
                    duration_unit = match.group(2) or ""       # "day", "month", "year", etc.
                else:
                    duration_value = 0
                    duration_unit = ""

                return [{
                    "included": True,
                    "duration": str(duration_value) + " " + duration_unit,
                    "unit_price": float(data.get(f"{prefix}[unit_price]") or 0),
                }]

            Quotation.objects.create(
                company_name=data.get("company_name"),
                company_address=data.get("company_address", ""),
                company_phone=data.get("company_phone", ""),
                company_email=data.get("company_email", ""),

                # quotation_no=data.get("quotation_no") or "",  # auto-generated if blank
                
                date=parse_date(data.get("date")),
                valid_until=parse_date(data.get("valid_until")),
                prepared_by=prepared_by_user,
                
                client_name=data.get("client_name"),
                client_contact=data.get("client_contact", ""),
                client_address=data.get("client_address", ""),
                lead_source = data.get("lead_source",""),

                web_services=services["web"],
                mobile_services=services["mobile"],
                cloud_services=services["cloud"],
                ai_ml_services=services["ai_ml"],

                domain_registration = extract_json("domain_registration"),
                server_hosting = extract_json("server_hosting"),
                ssl_certificate = extract_json("ssl_certificate"),
                email_hosting = extract_json("email_hosting"),
                
                discount_type=data.get("discount_type", "none"),
                discount_value=Decimal(data.get("discount_value") or 0),
                tax_rate=Decimal(data.get("tax_rate") or 0.00),
                
                payment_terms=data.get("payment_terms", ""),
                additional_notes=data.get("additional_notes", ""),
                signatory_name=data.get("signatory_name", ""),
                signatory_designation=data.get("signatory_designation", ""),
                signature=files.get("signature"),
            )

            return JsonResponse({"success": True, "message": "Quotation added successfully!"})

        except ValidationError as ve:
            if hasattr(ve, "message_dict"):
                flat_errors = []
                for field, msgs in ve.message_dict.items():
                    for msg in msgs:
                        flat_errors.append(f"{field}: {msg}" if field != "__all__" else msg)
            else:
                flat_errors = ve.messages

            return JsonResponse({"success": False, "flat_errors": flat_errors}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)

    return JsonResponse({"success": False, "errors": {"__all__": ["Invalid request method"]}}, status=405)
        
def get_quotation(request):
    quotation_id = request.GET.get("id")
    quotation = Quotation.objects.get(id=quotation_id)


    # Merge services into single list with category
    def add_category(services, category_label):
        items = []
        if services and isinstance(services, list):
            for s in services:
                items.append({
                    "category": category_label,
                    "description": s.get("description", "").strip().lower(),
                    "quantity": int(s.get("quantity", 0)),
                    "unit_price": float(s.get("unit_price", 0)),
                    "total": float(s.get("total", 0)),
                })
        return items

    raw_services = []
    raw_services += add_category(quotation.web_services, "Web Development")
    raw_services += add_category(quotation.mobile_services, "Mobile Development")
    raw_services += add_category(quotation.cloud_services, "Cloud Services")
    raw_services += add_category(quotation.ai_ml_services, "AI/ML Algorithms")

    # Group by (category, description, unit_price)
    grouped = defaultdict(lambda: {"quantity": 0, "total": 0})
    for s in raw_services:
        # key = (s["category"], s["description"], s["unit_price"])
        key = (s["category"],)

        grouped[key].update({
            "category": s["category"],
            "description": s["description"],
            "unit_price": s["unit_price"],
        })
        print(f"Processing service: {s}")  # Debugging output
        grouped[key]["quantity"] += s["quantity"]
        grouped[key]["total"] += s["total"]

    services = list(grouped.values())
    print(f"Grouped services: {services}")  # Debugging output

    # Helper for server/domain charges
    def format_infra(items):
        result = []
        if items and isinstance(items, list):
            for f in items:
                if f.get("included"):
                    result.append({
                        "included": True,
                        "duration": f.get("duration", ""),
                        "unit_price": f.get("unit_price", 0),
                        "total": f.get("total", 0),
                    })
        return result  # return list, can be empty



    return JsonResponse({
        # --- Company & Client Info ---
        "quotation_no": quotation.quotation_no,
        "date": quotation.date.strftime("%Y-%m-%d"),
        "valid_until": quotation.valid_until.strftime("%Y-%m-%d"),
        # "prepared_by": str(quotation.prepared_by) if quotation.prepared_by else "",
        "company_name": quotation.company_name,
        "company_phone": quotation.company_phone,
        "company_email": quotation.company_email,
        "company_address": quotation.company_address,
        "client_name": quotation.client_name,
        "client_contact": quotation.client_contact,
        "client_email": quotation.client_email,
        "client_address": quotation.client_address,
        "lead_source": quotation.lead_source,
        "prepared_by": {
            "id": quotation.prepared_by.id if quotation.prepared_by else None,
            "name": quotation.prepared_by.username   if quotation.prepared_by else ""
        },

        # --- Services ---
        "services": services,
        "total_service_charge": str(quotation.total_service_charge),

        # --- Server & Domain ---
       "infra": {
        "domain_registration": format_infra(quotation.domain_registration),
        "server_hosting": format_infra(quotation.server_hosting),
        "ssl_certificate": format_infra(quotation.ssl_certificate),
        "email_hosting": format_infra(quotation.email_hosting),
        },
        "total_server_domain_charge": str(quotation.total_server_domain_charge),
        

        # --- Summary ---
        "subtotal_services": str(quotation.total_service_charge),
        "subtotal_infra": str(quotation.total_server_domain_charge),
        "discount_type": quotation.discount_type,
        "discount_value": str(quotation.discount_value),
        "after_discount_total": str(quotation.after_discount_total),
        "tax_rate": str(quotation.tax_rate),
        "tax_amount": str(quotation.tax_amount),
        "grand_total": str(quotation.grand_total),

        # --- Other ---
        "payment_terms": quotation.payment_terms,
        "additional_notes": quotation.additional_notes,

        # --- Signatory ---
        "signature_url": quotation.signature.url if quotation.signature else None,
        "sign_name": quotation.signatory_name,
        "sign_designation": quotation.signatory_designation,
    })

def update_quotation(request, id):
    from decimal import Decimal
    quotation = get_object_or_404(Quotation, pk=id)

    if request.method == "POST":
        try:
            data = request.POST
            files = request.FILES

            # prepared_by user (by ID) — same approach as add_quotation
            prepared_by_user = None
            prepared_by_value = data.get("prepared_by")
            if prepared_by_value:
                try:
                    prepared_by_user = User.objects.get(id=prepared_by_value)
                except User.DoesNotExist:
                    prepared_by_user = None
            print(f"Updating quotation prepared by: {prepared_by_user}")
            # Helper: parse dynamic service rows (category-aware)
            def parse_services():
                services = {"web": [], "mobile": [], "cloud": [], "ai_ml": []}

                indices = set()
                for key in data:
                    if key.startswith("service[") and key.endswith("][category]"):
                        idx = key.split("[")[1].split("]")[0]
                        indices.add(idx)

                for index in indices:
                    category = data.get(f"service[{index}][category]")
                    description = data.get(f"service[{index}][description]")
                    quantity = int(data.get(f"service[{index}][quantity]") or 1)
                    unit_price = float(data.get(f"service[{index}][unit_price]") or 0)
                    if category in services:
                        services[category].append({
                            "description": description,
                            "quantity": quantity,
                            "unit_price": unit_price
                        })
                return services

            # Helper for JSON infra fields (domain/server/ssl/email)
            def extract_json(prefix):
                included = data.get(f"{prefix}[included]") == "true"
                if not included:
                    return []  # keep empty list when not selected

                duration_raw = data.get(f"{prefix}[duration]") or ""
                import re
                match = re.match(r'(\d+)\s*(\w+)?', duration_raw.strip())
                if match:
                    duration_value = int(match.group(1))
                    duration_unit = match.group(2) or ""
                else:
                    duration_value = 0
                    duration_unit = ""

                return [{
                    "included": True,
                    "duration": str(duration_value) + " " + duration_unit,
                    "unit_price": float(data.get(f"{prefix}[unit_price]") or 0),
                }]

            # ---------- Assign simple fields ----------
            quotation.company_name = data.get("company_name")
            quotation.company_address = data.get("company_address", "")
            quotation.company_phone = data.get("company_phone", "")
            quotation.company_email = data.get("company_email", "")

            quotation.date = parse_date(data.get("date"))
            quotation.valid_until = parse_date(data.get("valid_until"))
            quotation.prepared_by = prepared_by_user

            quotation.client_name = data.get("client_name")
            quotation.client_contact = data.get("client_contact", "")  # save() validates phone/email
            quotation.client_address = data.get("client_address", "")
            quotation.lead_source = data.get("lead_source", "") 
            # ---------- Services (category-split) ----------
            services = parse_services()
            quotation.web_services = services["web"]
            quotation.mobile_services = services["mobile"]
            quotation.cloud_services = services["cloud"]
            quotation.ai_ml_services = services["ai_ml"]

            # ---------- Infra JSON blocks ----------
            quotation.domain_registration = extract_json("domain_registration")
            quotation.server_hosting = extract_json("server_hosting")
            quotation.ssl_certificate = extract_json("ssl_certificate")
            quotation.email_hosting = extract_json("email_hosting")

            # ---------- Summary ----------
            
            quotation.discount_type = data.get("discount_type", "none")
            quotation.discount_value = Decimal(data.get("discount_value") or 0)
            quotation.tax_rate = Decimal(data.get("tax_rate") or 0.00)
            quotation.payment_terms = data.get("payment_terms", "")
            quotation.additional_notes = data.get("additional_notes", "")

            # ---------- Signature / Signatory ----------
            if files.get("signature"):
                quotation.signature = files.get("signature")
            quotation.signatory_name = data.get("signatory_name", "")
            quotation.signatory_designation = data.get("signatory_designation", "")

            # Persist (recalculations happen in model.save())
            quotation.save()
            messages.success(request, "Quotation updated successfully!")
            return redirect("quotation_list")

        except Exception as e:
            messages.error(request, f"Error updating quotation: {str(e)}")
            return redirect("quotation_list")

    # Non-POST: just go back to list (same pattern used elsewhere)
    return redirect("quotation_list")

async def generate_pdf(html):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)
        pdf = await page.pdf()
        await browser.close()
        return pdf

def download_quotation(request, id):
    quotation = get_object_or_404(Quotation, pk=id)
    # helper to flatten services with category name
    def add_category(services, category):
        if services and isinstance(services, list):
            return [
                {
                    "name": s.get("name", ""),
                    "description": s.get("description", ""),
                    "quantity": s.get("quantity", 1),
                    "unit_price": s.get("unit_price", 0),
                    "total": s.get("total", 0),
                    "category": category,
                }
                for s in services if s
            ]
        return []

    # combine all lists
    all_items = []
    all_items += add_category(quotation.web_services, "Web Development")
    all_items += add_category(quotation.mobile_services, "Mobile Development")
    all_items += add_category(quotation.cloud_services, "Cloud Services")
    all_items += add_category(quotation.ai_ml_services, "AI / ML Services")
    

    # Tax logic → front side decision
    if quotation.tax_rate and quotation.tax_rate > 0:
        tax_rate = quotation.tax_rate
        tax_amount = quotation.tax_amount if quotation.tax_amount and quotation.tax_amount > 0 else 0
    else:
        tax_rate = "-"
        tax_amount = "-"

    # Discount logic → front side decision
    
    if quotation.discount_type is None or quotation.discount_type.lower() == "none":
        discount_display = "-"
        after_discount_t = "-"
    elif quotation.discount_type.lower() == "flat":
        discount_display = "Flat"
        after_discount_t = f"₹{quotation.after_discount_total:.2f}" if quotation.after_discount_total else "-"
    elif quotation.discount_type.lower() == "percent":
        discount_display = "%"
        after_discount_t = f"₹{quotation.after_discount_total:.2f}" if quotation.after_discount_total else "-"
    else:
        discount_display = "-"
        after_discount_t = "-"


        

    html = render_to_string(
        "quotation_pdf.html",
        {
            "quotation": quotation,
            "all_items": all_items,
            # Subtotal
        "subtotals": quotation.total_service_charge or 0,

        # Tax → show "-" if tax is 0
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,

        # Domain
        "domain_total": (
            sum(f.get("total", 0) for f in (quotation.domain_registration or [])) or "-"
        ),
        "domain_duration": ", ".join(
            f.get("duration", "-") for f in (quotation.domain_registration or []) if f.get("duration")
        ) or "-",


        # Server
        "server_total": (
            sum(f.get("total", 0) for f in (quotation.server_hosting or [])) or "-"
        ),

        "server_duration": ", ".join(
            f.get("duration", "-") for f in (quotation.server_hosting or []) if f.get("duration")
        ) or "-",

        # Discount → show "-" if None or 0
        "discount_display": discount_display,
        "after_discount_total": after_discount_t,

        # Grand total → always show (never blank)
        "grand_total": quotation.grand_total or 0,
        }
    )

    pdf_bytes = asyncio.run(generate_pdf(html))

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="{quotation.client_name}_{quotation.quotation_no}.pdf"'
    return response


# -----------------------------
# client Management
# -----------------------------
def client_list(request):
    records_per_page = int(request.GET.get('recordsPerPage', 20))

    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    if page_number < 1:
        page_number = 1
    clients = Client.objects.all().order_by('id')

    query = request.POST.get("q", "")

    if query:
        search_filter = Q()
        for field in Client._meta.get_fields():
            if isinstance(field, (CharField, TextField)):
                field_name = field.name
                search_filter |= Q(**{f"{field_name}__icontains": query})
        clients = clients.filter(search_filter)
     # Paginate
    paginator = Paginator(clients, records_per_page)
    page_obj = paginator.get_page(page_number)

    total_clients = clients.count()
    
    context = {
        "page_obj": page_obj,  # paginated domains
        "records_per_page": records_per_page,
        "total_clients": total_clients,
        "records_options": [20, 50, 100, 200, 300],
        "search_action": reverse("client_list"),
        "search_placeholder": "Search clients...",
    }

    return render(request, 'client.html', context)


def add_client(request):
    if request.method == "POST":
        try:
            # Collect data from form
            data = request.POST

            client = Client(
                name=data.get("name"),
                email=data.get("email"),
                phone=data.get("phone"),
                address=data.get("address"),
                city=data.get("city"),
                state=data.get("state"),
                country=data.get("country"),
                pincode=data.get("pincode"),
                company_name=data.get("company_name"),
                gst_number=data.get("gst_number"),
                website=data.get("website"),
            )

            # Run model validations (uses clean() + field validators)
            client.full_clean()  
            client.save()

            return JsonResponse({"success": True, "message": "Client added successfully!"})

        except ValidationError as ve:
            if hasattr(ve, "message_dict"):
                flat_errors = []
                for field, msgs in ve.message_dict.items():
                    for msg in msgs:
                        flat_errors.append(f"{field}: {msg}" if field != "__all__" else msg)
            else:
                flat_errors = ve.messages

            return JsonResponse({"success": False, "flat_errors": flat_errors}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)

    return JsonResponse({"success": False, "errors": {"__all__": ["Invalid request method"]}}, status=405)

def get_client(request):
    client_id = request.GET.get("id")
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        raise Http404("Client not found")

    return JsonResponse({
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "address": client.address,
        "city": client.city,
        "state": client.state,
        "country": client.country,
        "pincode": client.pincode,
        "company_name": client.company_name,
        "gst_number": client.gst_number,
        "website": client.website,
        "created_at": client.created_at.strftime("%Y-%m-%d %H:%M"),
        "updated_at": client.updated_at.strftime("%Y-%m-%d %H:%M"),
    })

def update_client(request):
    if request.method == "POST":
        client_id = request.POST.get("id")
        print(f"Updating client with ID: {client_id}")
        try:
            client = Client.objects.get(id=client_id)
            data = request.POST

            client.name = data.get("name")
            client.email = data.get("email")
            client.phone = data.get("phone")
            client.address = data.get("address")
            client.city = data.get("city")
            client.state = data.get("state")
            client.country = data.get("country")
            client.pincode = data.get("pincode")
            client.company_name = data.get("company_name")
            client.gst_number = data.get("gst_number")
            client.website = data.get("website")

            client.full_clean()
            client.save()

            # ✅ JSON response for AJAX
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True})

            # Fallback for non-AJAX
            messages.success(request, "Client updated successfully!")
            return redirect("client_list")

        except Client.DoesNotExist:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": "Client not found."})
            messages.error(request, "Client not found.")
            return redirect("client_list")

        except ValidationError as e:
            errors = {field: errs for field, errs in e.message_dict.items()}
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": errors})
            for field, errs in errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
            return redirect("client_list")

        except Exception as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": str(e)})
            messages.error(request, f"Error updating client: {str(e)}")
            return redirect("client_list")

    return redirect("client_list")

def delete_client(request, id):

    if request.method == "POST":
        try:
            client = Client.objects.get(id=id)
            client.delete()
            return JsonResponse({"success": True, "message": "Client deleted successfully!"})
        except Client.DoesNotExist:
            return JsonResponse({"success": False, "error": "Client not found."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request."})


# -----------------------------
# File & Docs View
# -----------------------------

def file_docs(request):
    records_per_page = int(request.GET.get('recordsPerPage', 20))
    page_number = int(request.GET.get('page', 1) or 1)

    all_projects = Project.objects.all()
    all_folders = Folder.objects.select_related("project").all()
    all_subfolders = SubFolder.objects.select_related("folder__project").all()


    display_all_folders = Folder.objects.all()
    display_all_subfolders = SubFolder.objects.all()

    # Total folders: main + subfolders
    total_folders = display_all_folders.count() + display_all_subfolders.count()

    # Total files: files in folders + files in subfolders
    total_files = FileDoc.objects.count()

    # Recent file
    recent_file = FileDoc.objects.order_by("-created_at").first()

    # Prepare recent file info with folder/subfolder
    if recent_file:
        if recent_file.subfolder:  # file is in subfolder
            recent_location = f"{recent_file.subfolder.folder.name} / {recent_file.subfolder.name}"
        elif recent_file.folder:  # file is in main folder
            recent_location = f"{recent_file.folder.name}"
        else:
            recent_location = "No folder info"
    else:
        recent_location = "No recent files"

    # Flatten to folders directly
    folder_rows = []
    for f in all_folders:
        file_count = FileDoc.objects.filter(folder=f).count()
        last_file = FileDoc.objects.filter(folder=f).order_by("-created_at").first()

        folder_rows.append({
            "id": f.id,
            "name": f.name,
            "created_at": f.created_at,
            "project_id": f.project.project_id if f.project else "-",
            "project_name": f.project.project_name if f.project else "No Project",
            "file_count": file_count,
            "last_file_name": last_file.name if last_file else "No Files",
        })
    # -----------------------------
    # SubFolder rows
    # -----------------------------
    subfolder_rows = []
    for sf in all_subfolders:
        file_count = FileDoc.objects.filter(subfolder=sf).count()
        last_file = FileDoc.objects.filter(subfolder=sf).order_by("-created_at").first()

        subfolder_rows.append({
            "id": sf.id,
            "name": sf.name,
            "parent_folder_id": sf.folder.id,
            "parent_folder_name": sf.folder.name,
            "project_id": sf.folder.project.project_id if sf.folder.project else "-",
            "project_name": sf.folder.project.project_name if sf.folder.project else "No Project",
            "created_at": sf.created_at,
            "file_count": file_count,
            "last_file_name": last_file.name if last_file else "No Files",
        })
    paginator = Paginator(folder_rows, records_per_page)
    page_obj = paginator.get_page(page_number)

    # recent_file = FileDoc.objects.order_by("-created_at").first()  # returns single object or None
    print(recent_file)
    

    context = {
        "display_all_folders": display_all_folders,
        "display_all_subfolders": display_all_subfolders,
        "all_projects": all_projects,
        "all_folders": all_folders,
        "all_subfolders": all_subfolders,
        "page_obj": page_obj,
        "records_per_page": records_per_page,
        "records_options": [20, 50, 100, 200, 300],
        "total_projects": all_projects.count(),
        "total_folders": total_folders,
        "total_files": total_files,
        "recent_file": recent_file,
        "recent_location": recent_location,
    }
    return render(request, 'file_docs.html', context)

def create_folder(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            name = data.get("name")
            project_id = data.get("project_id")

            if not name:
                return JsonResponse({"success": False, "error": "Folder name is required."})

            project = Project.objects.filter(id=project_id).first() if project_id else None

            folder = Folder.objects.create(
                name=name,
                project=project
            )

            return JsonResponse({
                "success": True,
                "folder_id": folder.id,
                "folder_name": folder.name,
                "project_name": project.project_name if project else ""
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@csrf_exempt
def create_subfolder(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name", "").strip()
            folder_id = data.get("folder_id")

            if not name:
                return JsonResponse({"success": False, "error": "SubFolder name is required."})

            if not folder_id:
                return JsonResponse({"success": False, "error": "Parent folder is required."})

            # Get parent folder
            try:
                folder = Folder.objects.get(id=folder_id)
            except Folder.DoesNotExist:
                return JsonResponse({"success": False, "error": "Parent folder does not exist."})

            # Create subfolder
            subfolder = SubFolder.objects.create(name=name, folder=folder)

            return JsonResponse({
                "success": True,
                "subfolder_id": subfolder.id,
                "subfolder_name": subfolder.name,
                "folder_name": folder.name,
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})

def add_file(request):
    if request.method == "POST":
        try:
            folder_id = request.POST.get("folder")
            subfolder_id = request.POST.get("subfolder")
            project_id = request.POST.get("project")
            files = request.FILES.getlist("files")

            if not folder_id:
                return JsonResponse({"success": False, "error": "Folder is required"})

            folder = Folder.objects.filter(id=folder_id).first()
            if not folder:
                return JsonResponse({"success": False, "error": "Invalid folder"})

            # project comes indirectly from folder, but we can still accept project_id
            project = Project.objects.filter(id=project_id).first() if project_id else folder.project

            # get subfolder if provided
            subfolder = None
            if subfolder_id:
                subfolder = SubFolder.objects.filter(id=subfolder_id, folder=folder).first()
                if not subfolder:
                    return JsonResponse({"success": False, "error": "Invalid subfolder for selected folder"})
            if not files:
                return JsonResponse({"success": False, "error": "No files provided"})

            for f in files:
                FileDoc.objects.create(
                    name=f.name,
                    folder=folder,
                    subfolder=subfolder,
                    file=f
                )

            return JsonResponse({"success": True, "folder_id": folder.id})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})

def get_files(request):
    folder_id = request.GET.get("id")
    try:
        folder = Folder.objects.get(id=folder_id)
    except Folder.DoesNotExist:
        raise Http404("Folder not found")

    files_data = [
        {
            "id": f.id,
            "name": f.name,
            "file_url": f.file.url if f.file else None,
            "created_at": f.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for f in folder.files.filter(subfolder__isnull=True)
    ]
    subfolders_data = [
        {
            "id": sf.id,
            "name": sf.name,
            "file_count": sf.files.count(),
            "created_at": sf.created_at.strftime("%Y-%m-%d %H:%M"), 
           
        }
        for sf in folder.subfolders.all()
    ]
    print(files_data)
    return JsonResponse({
        "id": folder.id,
        "name": folder.name,
        "project": folder.project.project_name if folder.project else "No Project",
        "created_at": folder.created_at.strftime("%Y-%m-%d %H:%M"),
        "updated_at": folder.updated_at.strftime("%Y-%m-%d %H:%M"),
        "files": files_data,
        "subfolders": subfolders_data,
    })

def get_subfolder_files(request):
    subfolder_id = request.GET.get("id")
    try:
        subfolder = SubFolder.objects.get(id=subfolder_id)
    except SubFolder.DoesNotExist:
        raise Http404("SubFolder not found")

    files_data = [
        {
            "id": f.id,
            "name": f.name,
            "file_url": f.file.url if f.file else None,
            "created_at": f.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for f in subfolder.files.all()
    ]

    
    print(files_data)
    return JsonResponse({
        "id": subfolder.id,
        "name": subfolder.name,
        "folder": subfolder.folder.name,
        "created_at": subfolder.created_at.strftime("%Y-%m-%d %H:%M"),
        "files": files_data,
        #  "subfolders": subfolders_data,
    })


def delete_file(request, file_id):
    """
    Deletes a FileDoc instance along with its physical file from storage.
    """
    if request.method == "POST":
        file_obj = get_object_or_404(FileDoc, id=file_id)
        try:
            # Delete the actual file from storage
            if file_obj.file:
                file_obj.file.delete(save=False)

            # Delete the database record
            file_obj.delete()
            return JsonResponse({"success": True, "message": "File deleted successfully."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    else:
        return JsonResponse({"success": False, "error": "Invalid request method."})

def delete_subfolder(request, subfolder_id):
    if request.method == "POST":
        try:
            subfolder = SubFolder.objects.get(id=subfolder_id)
            
            # Delete all files in the subfolder
            subfolder.files.all().delete()
            
            # Delete the subfolder itself
            subfolder.delete()
            
            return JsonResponse({"success": True})
        except SubFolder.DoesNotExist:
            return JsonResponse({"success": False, "error": "Subfolder not found"})
    return JsonResponse({"success": False, "error": "Invalid request method"})

def delete_folder(request, id):
    if request.method == "POST":
        folder = get_object_or_404(Folder, id=id)
        folder_name = folder.name
        folder.delete()  # This will also delete all FileDoc linked due to CASCADE
        return JsonResponse({"success": True, "message": f"Folder '{folder_name}' and its files deleted successfully."})

    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

def view_folder(request, id):
    folder = get_object_or_404(Folder, id=id)
    files = folder.files.filter(subfolder__isnull=True)  # Related FileDoc objects

    context = {
        "folder": folder,
        "files": files,
    }
    return render(request, "view_folder.html", context)

def view_subfolder(request, id):
    subfolder = get_object_or_404(SubFolder, id=id)
    files = subfolder.files.all()  # all files in this subfolder

    context = {
        "subfolder": subfolder,
        "files": files,
    }
    return render(request, "view_subfolder.html", context)

# -----------------------------
# Payment View  
# -----------------------------

def payment_list(request):
    records_per_page = int(request.GET.get('recordsPerPage', 20))

    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    if page_number < 1:
        page_number = 1

    # All projects for dropdown
    projects = Project.objects.order_by('id').all()

    # Get distinct projects that have payments
    project_ids = ProjectPayment.objects.values_list("project_id", flat=True).distinct()
    
    grouped_data = []
    for pid in project_ids:
        project_payments = ProjectPayment.objects.filter(project_id=pid).select_related("project")

        if not project_payments.exists():
            continue

        project = project_payments.first().project

        # Collect all methods
        methods = list(project_payments.values_list("payment_method", flat=True).distinct())

        # Determine payment status (if any paid)
        is_paid = project_payments.filter(amount__gt=0).exists()

        grouped_data.append({
            "project": project,
            "methods": ", ".join(methods),
            "status": "PAID" if is_paid else "NOT PAID",
        })

    # Manual pagination
    paginator = Paginator(grouped_data, records_per_page)
    page_obj = paginator.get_page(page_number)


     # Overall counts
    total_payments = ProjectPayment.objects.count()
    bank_transfer_count = ProjectPayment.objects.filter(payment_method="Bank Transfer").count()
    upi_count = ProjectPayment.objects.filter(payment_method="UPI").count()
    cash_count = ProjectPayment.objects.filter(payment_method="Cash").count()
    
    context = {
        "page_obj": page_obj,
        "records_per_page": records_per_page,
        "projects": projects, 
        "total_payments": total_payments,
        "bank_transfer_count": bank_transfer_count,
        "upi_count": upi_count,
        "cash_count": cash_count,
        
        "records_options": [20, 50, 100, 200, 300],
    }
    return render(request, "payment.html", context)

def add_payment(request):
    if request.method == "POST":
        try:
            project_id = request.POST.get("project")
            milestone_name = request.POST.get("milestone_name") 
            amount = request.POST.get("amount")
            payment_date = request.POST.get("payment_date")
            payment_method = request.POST.get("payment_method")

            # Validate project
            project = get_object_or_404(Project, pk=project_id)

            # Prepare dynamic payment details
            payment_details = {}
            if payment_method == "Bank Transfer":
                payment_details = {
                    "bank_name": request.POST.get("bank_name"),
                    "account_no": request.POST.get("account_no"),
                    "ifsc_code": request.POST.get("ifsc_code")
                }
            elif payment_method == "UPI":
                payment_details = {
                    "upi_id": request.POST.get("upi_id")
                }
            elif payment_method == "Cheque":
                payment_details = {
                    "cheque_no": request.POST.get("cheque_no"),
                    "cheque_name": request.POST.get("cheque_name")
                }
            elif payment_method == "Other":
                payment_details = {
                    "other_details": request.POST.get("other_details")
                }

            # Create ProjectPayment instance
            payment = ProjectPayment(
                project=project,
                milestone_name = milestone_name,
                amount=amount,
                payment_date=payment_date,
                payment_method=payment_method,
                payment_details=payment_details
            )

            # Run model validation
            payment.full_clean()
            payment.save()

            # Update project income
            project.income = project.total_paid
            project.save(update_fields=["income"])

                # ✅ Return JSON for AJAX
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True, "message": "Payment added successfully!"})

            # Fallback for normal form submit
            messages.success(request, "Payment added successfully!")
            return redirect("payment_list")

        except ValidationError as ve:
            errors = ve.message_dict
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": errors}, status=400)

            for field, errs in errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
            return redirect("payment_list")

        except Exception as e:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)
            messages.error(request, f"Error: {str(e)}")
            return redirect("payment_list")

    return redirect("payment_list")

def get_payment(request):
    project_id = request.GET.get("id")
    if not project_id:
        return JsonResponse({"success": False, "error": "Missing project id"}, status=400)

    project = get_object_or_404(Project, id=project_id)

    # Get all payments for this project
    all_payments = ProjectPayment.objects.filter(project=project).order_by("id")

    payments_data = []
    total_paid = 0
    for p in all_payments:
        total_paid += float(p.amount)
        payments_data.append({
            "id": p.id,
            "milestone": p.milestone_name or "",
            "amount": str(p.amount),
            "method": p.payment_method,
            "details": p.payment_details or {},
            "notes": p.notes or "",
            "date": p.payment_date.strftime("%Y-%m-%d") if p.payment_date else "",
            
        })

    approval_amount = float(project.approval_amount or 0)
    remaining_amount = approval_amount - total_paid

    data = {
        "project_id": project.project_id,
        "project_name": project.project_name,
        "approval_amount": approval_amount,
        "total_paid": total_paid,
        "remaining_amount": remaining_amount,
        "payments": payments_data,
    }
    return JsonResponse({"success": True, "data": data})


# -----------------------------
# Designation  View  
# -----------------------------

def designation_list(request):
    records_per_page = int(request.GET.get('recordsPerPage', 20))

    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    if page_number < 1:
        page_number = 1
    designations = Designation.objects.all().order_by('id')
    # Manual pagination
    paginator = Paginator(designations, records_per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, 'designation.html', {
        "page_obj": page_obj,
        "records_per_page": records_per_page,
       "records_options": [20, 50, 100, 200, 300],
        'total_designations': Designation.objects.count(),
    })


def add_designation(request):
    if request.method == "POST":
        try:
            title = request.POST.get("title")
            designation = Designation(title=title)
            designation.full_clean()
            designation.save()
            messages.success(request, "Designation added successfully!")
            return redirect("designation_list")

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for err in errors:
                    messages.error(request, f"{field}: {err}")
            return redirect("designation_list")

        except Exception as e:
            messages.error(request, f"Error adding designation: {str(e)}")
            return redirect("designation_list")

    return redirect("designation_list")

def get_designation(request):
    desig_id = request.GET.get("id")
    try:
        designation = Designation.objects.get(id=desig_id)
    except Designation.DoesNotExist:
        raise Http404("Designation not found")

    return JsonResponse({
        "id": designation.id,
        "title": designation.title,
    })

def update_designation(request):
    if request.method == "POST":
        desig_id = request.POST.get("id")
        try:
            designation = Designation.objects.get(id=desig_id)
            designation.title = request.POST.get("title")
            designation.full_clean()
            designation.save()
            messages.success(request, "Designation updated successfully!")
            return redirect("designation_list")

        except Designation.DoesNotExist:
            messages.error(request, "Designation not found.")
            return redirect("designation_list")

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for err in errors:
                    messages.error(request, f"{field}: {err}")
            return redirect("designation_list")

        except Exception as e:
            messages.error(request, f"Error updating designation: {str(e)}")
            return redirect("designation_list")

    return redirect("designation_list")


def delete_designation(request, id):
    if request.method == "POST":
        try:
            designation = Designation.objects.get(id=id)
            designation.delete()
            return JsonResponse({"success": True, "message": "Designation deleted successfully!"})

        except Designation.DoesNotExist:
            return JsonResponse({"success": False, "error": "Designation not found."})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request."})

# -----------------------------
# Technology Views
# -----------------------------

def technology_list(request):
    records_per_page = int(request.GET.get('recordsPerPage', 20))

    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    if page_number < 1:
        page_number = 1

    technologies = Technology.objects.all().order_by('id')
    paginator = Paginator(technologies, records_per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, 'technology.html', {
        "page_obj": page_obj,
        "records_per_page": records_per_page,
        "records_options": [20, 50, 100, 200, 300],
        'total_technologies': Technology.objects.count(),
    })


def add_technology(request):
    if request.method == "POST":
        try:
            name = request.POST.get("name")
            technology = Technology(name=name)
            technology.full_clean()
            technology.save()
            messages.success(request, "Technology added successfully!")
            return redirect("technology_list")

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for err in errors:
                    messages.error(request, f"{field}: {err}")
            return redirect("technology_list")

        except Exception as e:
            messages.error(request, f"Error adding technology: {str(e)}")
            return redirect("technology_list")

    return redirect("technology_list")


def get_technology(request):
    tech_id = request.GET.get("id")
    try:
        technology = Technology.objects.get(id=tech_id)
    except Technology.DoesNotExist:
        raise Http404("Technology not found")

    return JsonResponse({
        "id": technology.id,
        "name": technology.name,
    })


def update_technology(request):
    if request.method == "POST":
        tech_id = request.POST.get("id")
        try:
            technology = Technology.objects.get(id=tech_id)
            technology.name = request.POST.get("name")
            technology.full_clean()
            technology.save()
            messages.success(request, "Technology updated successfully!")
            return redirect("technology_list")

        except Technology.DoesNotExist:
            messages.error(request, "Technology not found.")
            return redirect("technology_list")

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for err in errors:
                    messages.error(request, f"{field}: {err}")
            return redirect("technology_list")

        except Exception as e:
            messages.error(request, f"Error updating technology: {str(e)}")
            return redirect("technology_list")

    return redirect("technology_list")


def delete_technology(request, id):
    if request.method == "POST":
        try:
            technology = Technology.objects.get(id=id)
            technology.delete()
            return JsonResponse({"success": True, "message": "Technology deleted successfully!"})

        except Technology.DoesNotExist:
            return JsonResponse({"success": False, "error": "Technology not found."})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request."})


# -----------------------------
# AppMode Views
# -----------------------------

def appmode_list(request):
    records_per_page = int(request.GET.get('recordsPerPage', 20))

    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    if page_number < 1:
        page_number = 1

    app_modes = AppMode.objects.all().order_by('id')
    paginator = Paginator(app_modes, records_per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, 'appmode.html', {
        "page_obj": page_obj,
        "records_per_page": records_per_page,
        "records_options": [20, 50, 100, 200, 300],
        'total_app_modes': AppMode.objects.count(),
    })


def add_appmode(request):
    if request.method == "POST":
        try:
            name = request.POST.get("name")
            app_mode = AppMode(name=name)
            app_mode.full_clean()
            app_mode.save()
            messages.success(request, "App Mode added successfully!")
            return redirect("appmode_list")

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for err in errors:
                    messages.error(request, f"{field}: {err}")
            return redirect("appmode_list")

        except Exception as e:
            messages.error(request, f"Error adding App Mode: {str(e)}")
            return redirect("appmode_list")

    return redirect("appmode_list")


def get_appmode(request):
    mode_id = request.GET.get("id")
    try:
        app_mode = AppMode.objects.get(id=mode_id)
    except AppMode.DoesNotExist:
        raise Http404("App Mode not found")

    return JsonResponse({
        "id": app_mode.id,
        "name": app_mode.name,
    })


def update_appmode(request):
    if request.method == "POST":
        mode_id = request.POST.get("id")
        try:
            app_mode = AppMode.objects.get(id=mode_id)
            app_mode.name = request.POST.get("name")
            app_mode.full_clean()
            app_mode.save()
            messages.success(request, "App Mode updated successfully!")
            return redirect("appmode_list")

        except AppMode.DoesNotExist:
            messages.error(request, "App Mode not found.")
            return redirect("appmode_list")

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for err in errors:
                    messages.error(request, f"{field}: {err}")
            return redirect("appmode_list")

        except Exception as e:
            messages.error(request, f"Error updating App Mode: {str(e)}")
            return redirect("appmode_list")

    return redirect("appmode_list")


def delete_appmode(request, id):
    if request.method == "POST":
        try:
            app_mode = AppMode.objects.get(id=id)
            app_mode.delete()
            return JsonResponse({"success": True, "message": "App Mode deleted successfully!"})

        except AppMode.DoesNotExist:
            return JsonResponse({"success": False, "error": "App Mode not found."})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request."})