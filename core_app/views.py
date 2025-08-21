from django.shortcuts import render
from django.shortcuts import render, redirect,get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import *
from django.urls import reverse
from datetime import datetime
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_date
from collections import defaultdict
import json
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from django.http import HttpResponse
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout as django_logout
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Subquery, OuterRef


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

            # Create new Project object
            project = Project(
                project_name=data.get("project_name"),
                start_date=data.get("start_date") or None,
                deadline=data.get("deadline") or None,
                technologies=data.get("technologies"),
                app_mode=data.get("app_mode"),
                status=data.get("status"),
                payment_percentage=data.get("payment_percentage") or 0,
                payment_status=data.get("payment_status"),
                live_link=data.get("live_link"),
                expense=data.get("expense") or None,
                developer_charge=data.get("developer_charge") or None,
                server_charge=data.get("server_charge") or None,
                third_party_api_charge=data.get("third_party_api_charge") or None,
                income=data.get("income") or None,
                free_service=data.get("free_service"),
                postman_collection=data.get("postman_collection"),
                data_folder=data.get("data_folder"),
                other_link=data.get("other_link"),
                inquiry_date=data.get("inquiry_date") or None,
                lead_source=data.get("lead_source"),
                quotation_sent=data.get("quotation_sent"),
                demo_given=data.get("demo_given"),
                quotation_amount=data.get("quotation_amount") or None,
                approval_amount=data.get("approval_amount") or None,
                completed_date=data.get("completed_date") or None,
                client_industry=data.get("client_industry"),
                contract_signed=data.get("contract_signed")
            )

             #  Run backend validation
            project.full_clean()   # will call clean() + field validations
            project.save()

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
    print(team_members_display)
    data = {
        "id": project.id,   # numeric id (important)
        "project_id": project.project_id,  
        "start_date": project.start_date.strftime('%Y-%m-%d') if project.start_date else '',
        "project_name": project.project_name,
        "technologies": project.technologies,
        "app_mode": project.app_mode,
        "status": project.status,
        "deadline": project.deadline.strftime('%Y-%m-%d') if project.deadline else '',
        "payment_percentage": project.payment_percentage,
        "payment_status": project.payment_status,
        "live_link": project.live_link,
        "expense": str(project.expense) if project.expense is not None else '',
        "developer_charge": str(project.developer_charge) if project.developer_charge is not None else '',
        "server_charge": str(project.server_charge) if project.server_charge is not None else '',
        "third_party_api_charge": str(project.third_party_api_charge) if project.third_party_api_charge is not None else '',
        "income": str(project.income) if project.income is not None else '',
        "free_service": project.free_service or '',
        "postman_collection": project.postman_collection,
        "data_folder": project.data_folder,
        "other_link": project.other_link,
        "inquiry_date": project.inquiry_date.strftime('%Y-%m-%d') if project.inquiry_date else '',
        "lead_source": project.lead_source,
        "quotation_sent": project.quotation_sent,
        "demo_given": project.demo_given,
        "quotation_amount": str(project.quotation_amount) if project.quotation_amount is not None else '',
        "approval_amount": str(project.approval_amount) if project.approval_amount is not None else '',
        "completed_date": project.completed_date.strftime('%Y-%m-%d') if project.completed_date else '-',
        "client_industry": project.client_industry,
        "contract_signed": project.contract_signed,
        "team_members_display": team_members_display,
        "team_members_ids": list(project.team_members.values_list('id', flat=True)),
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

            # Basic info
            project.project_name = data.get("project_name")
            project.start_date = data.get("start_date") or None
            project.deadline = data.get("deadline") or None
            project.technologies = data.get("technologies")
            project.app_mode = data.get("app_mode")
            project.status = data.get("status")

            # Payment info
            project.payment_percentage = data.get("payment_percentage") or 0
            project.payment_status = data.get("payment_status")

            # Links
            project.live_link = data.get("live_link")
            project.postman_collection = data.get("postman_collection")
            project.data_folder = data.get("data_folder")
            project.other_link = data.get("other_link")

            # Financials
            project.expense = data.get("expense") or 0
            project.developer_charge = data.get("developer_charge") or 0
            project.server_charge = data.get("server_charge") or 0
            project.third_party_api_charge = data.get("third_party_api_charge") or 0
            project.income = data.get("income") or 0
            project.free_service = data.get("free_service")

            # Sales / lead tracking
            project.inquiry_date = data.get("inquiry_date") or None
            project.lead_source = data.get("lead_source")
            project.quotation_sent = data.get("quotation_sent")
            project.demo_given = data.get("demo_given")
            project.quotation_amount = data.get("quotation_amount") or 0
            project.approval_amount = data.get("approval_amount") or 0

            # Completion / client info
            project.completed_date = data.get("completed_date") or None
            project.client_industry = data.get("client_industry")
            project.contract_signed = data.get("contract_signed")

            # Save project first before updating many-to-many
            project.full_clean()

            project.save()

            # Team members (ManyToMany)
            team_member_ids = request.POST.getlist("team_members")
            members = User.objects.filter(id__in=team_member_ids)
            project.team_members.set(members)

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

    # High CPU Load -> assume > 80% 
    high_cpu_servers = host_data_list.filter(
        cpu_usage__regex=r'^\d+%'  # ensure valid percentage
    ).filter(
        cpu_usage__gte="80%"  # adjust based on how you store cpu_usage
    ).count()

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
        'high_cpu_servers': high_cpu_servers,
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
                company_name=request.POST.get("company_name"),
                hosting_provider=request.POST.get("hosting_provider"),
                server_name=request.POST.get("server_name"),
                server_type=request.POST.get("server_type"),
                plan_package=request.POST.get("plan_package"),
                server_ip = request.POST.get("server_ip") or None,
                location=request.POST.get("location"),
                operating_system=request.POST.get("operating_system"),
                control_panel=request.POST.get("control_panel"),
                login_url=request.POST.get("login_url"),
                username=request.POST.get("username"),
                password=request.POST.get("password"),
                ssh_username = request.POST.get("ssh_username"),
                ssh_ftp_access=request.POST.get("ssh_ftp_access"),
                database_name=request.POST.get("database_name"),
                db_username=request.POST.get("db_username"),
                db_password=request.POST.get("db_password"),
                purchase_date=request.POST.get("purchase_date") or None,
                expiry_date=request.POST.get("expiry_date") or None,
                server_cost=request.POST.get("server_cost") or None,
                uptime=request.POST.get("uptime"),
                cpu_usage=request.POST.get("cpu_usage"),
                memory_usage=request.POST.get("memory_usage"),
                disk_space=request.POST.get("disk_space"),
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
        "company_name": host.company_name,
        "server_name": host.server_name,
        "hosting_provider": host.hosting_provider,
        "server_type": host.server_type,
        "plan_package": host.plan_package,
        "server_ip": host.server_ip,
        "location": host.location,
        "operating_system": host.operating_system,
        "control_panel": host.control_panel,
        "login_url": host.login_url,
        "username": host.username,
        "password": host.password,
        "ssh_username": host.ssh_username,
        "ssh_ftp_access": host.ssh_ftp_access,
        "database_name": host.database_name,
        "db_username": host.db_username,
        "db_password": host.db_password,
        "purchase_date": host.purchase_date.strftime("%Y-%m-%d") if host.purchase_date else None,
        "expiry_date": host.expiry_date.strftime("%Y-%m-%d") if host.expiry_date else None,
        "server_cost": str(host.server_cost) if host.server_cost else None,
        "status": host.status,
        "uptime": host.uptime,
        "cpu_usage": host.cpu_usage,
        "memory_usage": host.memory_usage,
        "disk_space": host.disk_space,
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
            host.company_name = request.POST.get("company_name")
            host.server_name = request.POST.get("server_name")
            host.hosting_provider = request.POST.get("hosting_provider")
            host.server_type = request.POST.get("server_type")
            host.plan_package = request.POST.get("plan_package")
            host.server_ip = request.POST.get("server_ip")
            host.location = request.POST.get("location")
            host.operating_system = request.POST.get("operating_system")
            host.control_panel = request.POST.get("control_panel")
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
            host.uptime = request.POST.get("uptime")
            host.cpu_usage = request.POST.get("cpu_usage")
            host.memory_usage = request.POST.get("memory_usage")
            host.disk_space = request.POST.get("disk_space")
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
    """
    Create and save a new domain record.
    """
    if request.method == "POST":
        try:
            # Multiple projects allowed (can also be none)
            project_ids = request.POST.getlist('projects')  # <-- multiple
            projects = Project.objects.filter(id__in=project_ids)
            # Convert date strings to date objects
            purchase_date_str = request.POST.get('purchaseDate')
            expiry_date_str = request.POST.get('expiryDate')
            ssl_expiry_str = request.POST.get('sslExpiry')

            purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date() if purchase_date_str else None
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date() if expiry_date_str else None
            ssl_expiry = datetime.strptime(ssl_expiry_str, "%Y-%m-%d").date() if ssl_expiry_str else None

            domain = Domain(
                domain_name=request.POST.get('domainName'),
                purchase_date=purchase_date,
                expiry_date=expiry_date,
                registrar=request.POST.get('registrar'),
                renewal_status=request.POST.get('renewalStatus'),
                dns_configured=True if request.POST.get('dnsConfigured') == "True" else False,
                nameservers=request.POST.get('nameservers'),
                ssl_installed=True if request.POST.get('sslInstalled') == "True" else False,
                ssl_expiry=ssl_expiry,
                credentials_user=request.POST.get('credentialsUser'),
                credentials_pass=request.POST.get('credentialsPass'),
                linked_services=request.POST.get('linkedServices'),
                notes=request.POST.get('notes')
            )

            # Calculate left_days
            if expiry_date:
                today = timezone.now().date()
                domain.left_days = max((expiry_date - today).days, 0)
            domain.full_clean()
            domain.save()
           # Attach selected projects (can be empty also)
            if projects.exists():
                domain.project.set(projects)   # ✅ correct, matches model field


            messages.success(request, f"Domain '{domain.domain_name}' added successfully!")

        except Exception as e:
            messages.error(request, f"Error saving domain: {str(e)}")

        return redirect('domain_list')

    messages.warning(request, "Invalid request method.")
    return redirect('domain_list')

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

    data = {
        "id": domain.id,
        # ManyToMany projects → return both IDs and names
        "projects": [
            {"id": p.id, "name": p.project_name, "code": p.project_id}
            for p in domain.project.all()
        ],
        "domain_name": domain.domain_name,
        "registrar": domain.registrar,
        "purchase_date": domain.purchase_date.strftime("%Y-%m-%d") if domain.purchase_date else None,
        "expiry_date": domain.expiry_date.strftime("%Y-%m-%d") if domain.expiry_date else None,
        "renewal_status": domain.renewal_status,
        "dns_configured": domain.dns_configured,
        "nameservers": domain.nameservers,
        "ssl_installed": domain.ssl_installed,
        "ssl_expiry": domain.ssl_expiry.strftime("%Y-%m-%d") if domain.ssl_expiry else None,
        "credentials_user": domain.credentials_user,
        "credentials_pass": domain.credentials_pass if mode == "edit" else "********",
        "linked_services": domain.linked_services,
        "notes": domain.notes,
    }

    return JsonResponse({"success": True, "domain": data})

def update_domain(request, id):
    """
    Update existing domain record
    """
    if request.method == "POST":
        try:
            domain = get_object_or_404(Domain, id=id)

            # Get project from project name
            project_ids = request.POST.getlist('projects')  # Multiple project IDs from the form
            if project_ids:
                projects = Project.objects.filter(id__in=project_ids)
                domain.project.set(projects)  # Replace all projects
            else:
                domain.project.clear()
            # Convert dates
            purchase_date_str = request.POST.get('purchaseDate')
            expiry_date_str = request.POST.get('expiryDate')
            ssl_expiry_str = request.POST.get('sslExpiry')

            domain.purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date() if purchase_date_str else None
            domain.expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date() if expiry_date_str else None
            domain.ssl_expiry = datetime.strptime(ssl_expiry_str, "%Y-%m-%d").date() if ssl_expiry_str else None

            # Text fields
            domain.domain_name = request.POST.get('domainName')
            domain.registrar = request.POST.get('registrar')
            domain.renewal_status = request.POST.get('renewalStatus')
            domain.nameservers = request.POST.get('nameservers')
            domain.credentials_user = request.POST.get('credentialsUser')
            domain.credentials_pass = request.POST.get('credentialsPass')
            domain.linked_services = request.POST.get('linkedServices')
            domain.notes = request.POST.get('notes')

            # Boolean fields
            domain.dns_configured = True if request.POST.get('dnsConfigured') == "True" or request.POST.get('dnsConfigured') == "on" else False
            domain.ssl_installed = True if request.POST.get('sslInstalled') == "True" or request.POST.get('sslInstalled') == "on" else False

            # Calculate left_days
            if domain.expiry_date:
                today = timezone.now().date()
                domain.left_days = max((domain.expiry_date - today).days, 0)
            else:
                domain.left_days = None

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

    context = {
        "page_obj": page_obj,  # paginated domains
        "records_per_page": records_per_page,
        "records_options": [20, 50, 100, 200, 300],
        'total_users': total_users,
        'active_users': active_users,
        'new_users_this_month': new_users_this_month,
        'inactive_users': inactive_users,
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
                designation=request.POST.get("designation") or None,
                password=request.POST.get("password"),
                is_active=True if request.POST.get("is_active") == "on" else False,
            )

            # Handle profile picture upload
            if "profile_picture" in request.FILES:
                user.profile_picture = request.FILES["profile_picture"]

            # run model validations
            user.full_clean()
            user.save()

            return JsonResponse({"success": True, "message": "User added successfully!"})
        except ValidationError as ve:
            return JsonResponse({"success": False, "errors": ve.message_dict}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)

    return JsonResponse({"success": False, "errors": {"__all__": ["Invalid request method"]}}, status=405)

def get_user(request, id):
    """
    Return JSON details of a user for editing in modal.
    """
    user = get_object_or_404(User, id=id)
    print(f"Fetching details for user ID: {user.id}, Picture: {user.profile_picture.url if user.profile_picture else 'No picture'}")

    return JsonResponse({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "designation": user.designation,
        "is_active": user.is_active,
        "projects": [p.project_name for p in user.projects.all()],
        "profile_picture_url": request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,

    })

def update_user(request, id):
    print(f"Updating user with ID: {id}")
    """
    Update an existing user record via AJAX.
    """
    if request.method == "POST":
        try:
            user = get_object_or_404(User, id=id)

            # Update fields
            user.first_name = request.POST.get("first_name")
            user.last_name = request.POST.get("last_name")
            user.username = request.POST.get("username")
            user.email = request.POST.get("email")
            user.phone = request.POST.get("phone") or None
            user.designation = request.POST.get("designation") or None

            # Update password only if provided
            password = request.POST.get("password")
            if password:
                user.password = password  # (⚠️ plain-text in your model)

            # Profile picture
            if request.FILES.get("profile_picture"):
                user.profile_picture = request.FILES["profile_picture"]

            # Checkbox
            user.is_active = True if request.POST.get("is_active") else False

            user.full_clean()
            user.save()

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

    context = {
        "page_obj": page_obj,
        "records_per_page": records_per_page,
        "records_options": [20, 50, 100, 200, 300],
        "today": today,
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
                

                web_services=services["web"],
                mobile_services=services["mobile"],
                cloud_services=services["cloud"],
                ai_ml_services=services["ai_ml"],

                domain_registration = extract_json("domain_registration"),
                server_hosting = extract_json("server_hosting"),
                ssl_certificate = extract_json("ssl_certificate"),
                email_hosting = extract_json("email_hosting"),
                
                discount_type=data.get("discount_type", "flat"),
                discount_value=Decimal(data.get("discount_value") or 0),
                tax_rate=Decimal(data.get("tax_rate") or 18),
                
                payment_terms=data.get("payment_terms", ""),
                additional_notes=data.get("additional_notes", ""),
                signatory_name=data.get("signatory_name", ""),
                signatory_designation=data.get("signatory_designation", ""),
                signature=files.get("signature"),
            )

            messages.success(request, "Quotation added successfully!")
            return redirect("quotation_list")

        except Exception as e:
            messages.error(request, f"Error adding quotation: {str(e)}")
            return redirect("quotation_list")
        
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
        "prepared_by": str(quotation.prepared_by) if quotation.prepared_by else "",
        "company_name": quotation.company_name,
        "company_phone": quotation.company_phone,
        "company_email": quotation.company_email,
        "company_address": quotation.company_address,
        "client_name": quotation.client_name,
        "client_contact": quotation.client_contact,
        "client_email": quotation.client_email,
        "client_address": quotation.client_address,
        "prepared_by": quotation.prepared_by.id if quotation.prepared_by else None,

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
            quotation.discount_type = data.get("discount_type", "flat")
            quotation.discount_value = Decimal(data.get("discount_value") or 0)
            quotation.tax_rate = Decimal(data.get("tax_rate") or 18)
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

def download_quotation(request, id):
    quotation = get_object_or_404(Quotation, pk=id)

    # Prepare HTTP response as PDF
    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="quotation_{quotation.quotation_no}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # --- Title ---
    elements.append(Paragraph(f"Quotation #{quotation.quotation_no}", styles['Title']))
    elements.append(Spacer(1, 12))

    # --- Company & Client Info ---
    company_client_table = [
        ["Company", quotation.company_name or "-"],
        ["Address", quotation.company_address or "-"],
        ["Phone", quotation.company_phone or "-"],
        ["Email", quotation.company_email or "-"],
        ["Quotation Date", quotation.date.strftime("%Y-%m-%d")],
        ["Valid Until", quotation.valid_until.strftime("%Y-%m-%d")],
        ["Prepared By", str(quotation.prepared_by) if quotation.prepared_by else "-"],
        ["Client Name", quotation.client_name],
        ["Client Contact", quotation.client_contact or "-"],
        ["Client Email", quotation.client_email or "-"],
        ["Client Address", quotation.client_address or "-"],
    ]
    t = Table(company_client_table, colWidths=[120, 350])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                           ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # --- Service Charges ---
    elements.append(Paragraph("1. Service Charges", styles['Heading2']))
    service_data = [["Category", "Description", "Qty", "Unit Price", "Total"]]

    def add_services(services, label):
        if services:
            for s in services:
                total = float(s.get("quantity", 0)) * float(s.get("unit_price", 0))
                service_data.append([
                    label,
                    s.get("description", ""),
                    str(s.get("quantity", 0)),
                    f"₹ {s.get('unit_price', 0)}",
                    f"₹ {total}"
                ])

    add_services(quotation.web_services, "Web Development")
    add_services(quotation.mobile_services, "Mobile Development")
    add_services(quotation.cloud_services, "Cloud Services")
    add_services(quotation.ai_ml_services, "AI/ML Algorithms")

    if len(service_data) == 1:
        service_data.append(["-", "No services", "-", "-", "-"])

    t = Table(service_data, colWidths=[100, 150, 60, 80, 80])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    elements.append(t)
    elements.append(Paragraph(f"Total Service Charge: ₹ {quotation.total_service_charge}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # --- Server & Domain Charges ---
    elements.append(Paragraph("2. Server & Domain Charges", styles['Heading2']))
    infra_data = [["Type", "Duration", "Unit Price", "Total"]]

    def add_infra(items, label):
        if items:
            for i in items:
                if i.get("included"):
                    infra_data.append([
                        label,
                        i.get("duration", "-"),
                        f"₹ {i.get('unit_price', 0)}",
                        f"₹ {i.get('total', 0)}"
                    ])

    add_infra(quotation.domain_registration, "Domain Registration")
    add_infra(quotation.server_hosting, "Server Hosting")
    add_infra(quotation.ssl_certificate, "SSL Certificate")
    add_infra(quotation.email_hosting, "Email Hosting")

    if len(infra_data) == 1:
        infra_data.append(["-", "-", "-", "-"])

    t = Table(infra_data, colWidths=[150, 100, 100, 100])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    elements.append(t)
    elements.append(Paragraph(f"Total Infra Charge: ₹ {quotation.total_server_domain_charge}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # --- Summary ---
    elements.append(Paragraph("3. Summary", styles['Heading2']))
    summary_table = [
        ["Subtotal (Services)", f"₹ {quotation.total_service_charge}"],
        ["Subtotal (Infra)", f"₹ {quotation.total_server_domain_charge}"],
        [f"Discount ({quotation.discount_type})", str(quotation.discount_value)],
        ["Tax Rate", f"{quotation.tax_rate}%"],
        ["Tax Amount", f"₹ {quotation.tax_amount}"],
        ["Grand Total", f"₹ {quotation.grand_total}"],
    ]
    t = Table(summary_table, colWidths=[200, 200])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # --- Notes ---
    elements.append(Paragraph("Payment Terms:", styles['Heading3']))
    elements.append(Paragraph(quotation.payment_terms or "-", styles['Normal']))
    elements.append(Paragraph("Additional Notes:", styles['Heading3']))
    elements.append(Paragraph(quotation.additional_notes or "-", styles['Normal']))
    elements.append(Spacer(1, 12))

    # --- Signatory ---
    elements.append(Paragraph("Authorized Signatory", styles['Heading2']))
    sign_table = [
        ["Name", quotation.signatory_name or "-"],
        ["Designation", quotation.signatory_designation or "-"]
    ]
    t = Table(sign_table, colWidths=[150, 250])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    elements.append(t)

    # Build PDF
    doc.build(elements)
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

     # Paginate
    paginator = Paginator(clients, records_per_page)
    page_obj = paginator.get_page(page_number)

    total_clients = clients.count()
    
    context = {
        "page_obj": page_obj,  # paginated domains
        "records_per_page": records_per_page,
        "total_clients": total_clients,
        "records_options": [20, 50, 100, 200, 300],
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

            messages.success(request, "Client added successfully!")
            return redirect("client_list")  # Redirect to your client list page

        except ValidationError as e:
            # Convert error dict to readable messages
            for field, errors in e.message_dict.items():
                for err in errors:
                    messages.error(request, f"{field}: {err}")
            return redirect("client_list")

        except Exception as e:
            messages.error(request, f"Error adding client: {str(e)}")
            return redirect("client_list")

    # If GET request → redirect to list
    return redirect("client_list")

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

            messages.success(request, "Client updated successfully!")
            return redirect("client_list")

        except Client.DoesNotExist:
            messages.error(request, "Client not found.")
            return redirect("client_list")
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for err in errors:
                    messages.error(request, f"{field}: {err}")
            return redirect("client_list")
        except Exception as e:
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

    projects = Project.objects.all()

    latest_file_name = FileDoc.objects.filter(
        folder=OuterRef("pk")
    ).order_by("-created_at").values("name")[:1]

    latest_file_time = FileDoc.objects.filter(
        folder=OuterRef("pk")
    ).order_by("-created_at").values("created_at")[:1]
    
    folders = Folder.objects.select_related("project").annotate(
        file_count=Count("files"),
        last_file_name=Subquery(latest_file_name),
        last_file_time=Subquery(latest_file_time),
    )
    
    paginator = Paginator(projects, records_per_page)
    page_obj = paginator.get_page(page_number)

    total_projects = projects.count()
    total_folders = folders.count()
    total_files = FileDoc.objects.count()
    recent_file = FileDoc.objects.order_by('-created_at').first()
    recent_file_name = recent_file.name if recent_file else "No files uploaded"

    # Prepare folder data for template
    folder_data = []
    for folder in folders:
        folder_data.append({
            "id": folder.id,
            "name": folder.name,
            "project_id": folder.project.project_id if folder.project else None,
            "project_id_for_option": folder.project.id if folder.project else None,
            "project_name": folder.project.project_name if folder.project else None,
            "file_count":folder.file_count,
            "last_file_name": folder.last_file_name if folder.last_file_name else "No files",

        })

    context = {
        "page_obj": page_obj,
        "folders": folder_data,
        "records_per_page": records_per_page,
        "records_options": [20, 50, 100, 200, 300],
        "total_projects": total_projects,
        "total_folders": total_folders,
        "total_files": total_files,
        "recent_file_name": recent_file_name,
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

def add_file(request):
    if request.method == "POST":
        try:
            folder_id = request.POST.get("folder")
            project_id = request.POST.get("project")
            files = request.FILES.getlist("files")

            if not folder_id:
                return JsonResponse({"success": False, "error": "Folder is required"})

            folder = Folder.objects.filter(id=folder_id).first()
            if not folder:
                return JsonResponse({"success": False, "error": "Invalid folder"})

            # project comes indirectly from folder, but we can still accept project_id
            project = Project.objects.filter(id=project_id).first() if project_id else folder.project

            if not files:
                return JsonResponse({"success": False, "error": "No files provided"})

            for f in files:
                FileDoc.objects.create(
                    name=f.name,
                    folder=folder,
                    file=f
                )

            return JsonResponse({"success": True, "folder_id": folder.id})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})

def get_files(request):
    project_id = request.GET.get("id")
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        raise Http404("Project not found")

    folders_data = []
    for folder in project.folders.all():
        folders_data.append({
            "id": folder.id,
            "name": folder.name,
            "created_at": folder.created_at.strftime("%Y-%m-%d %H:%M"),
            "updated_at": folder.updated_at.strftime("%Y-%m-%d %H:%M"),
            "files": [
                {
                    "id": f.id,
                    "name": f.name,
                    "file_url": f.file.url if f.file else None,
                    "created_at": f.created_at.strftime("%Y-%m-%d %H:%M"),
                }
                for f in folder.files.all()
            ]
        })

    return JsonResponse({
        "id": project.id,
        "project_id": getattr(project, "project_id", None),
        "name": getattr(project, "project_name", ""),
        "description": getattr(project, "description", ""),
        "created_at": project.created_at.strftime("%Y-%m-%d %H:%M"),
        "updated_at": project.updated_at.strftime("%Y-%m-%d %H:%M"),
        "folders": folders_data,
    })