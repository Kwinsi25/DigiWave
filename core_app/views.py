from django.shortcuts import render
from django.shortcuts import render, redirect,get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import *
from django.urls import reverse
from datetime import datetime
from django.core.paginator import Paginator

# -----------------------------
# Dashboard
# -----------------------------
def dashboard(request):
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
    # Fetch all users for the dropdown 
    # # Paginate 
    paginator = Paginator(projects, records_per_page) 
    page_obj = paginator.get_page(page_number) # Safe pagination 
    print(users) 
    return render(request, 'project.html', 
                  { 'projects': projects, 
                   'users': users, 
                   'page_obj': page_obj, 
                   'records_per_page': records_per_page, 
                   'records_options': [20, 50, 100, 200, 300] })

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

            project.save()

            # Save team members (comma-separated usernames)
            team_member_ids = request.POST.getlist("team_members")  # <-- gets a list of selected IDs as strings
            print(team_member_ids, "team member IDs")

            if team_member_ids:
                members = User.objects.filter(id__in=team_member_ids)
                project.team_members.set(members)
            else:
                project.team_members.clear()

            messages.success(request, "Project saved successfully.")
        except Exception as e:
            #Add error message
            messages.error(request, f"Failed to save project: {str(e)}")

        # Always redirect to project list
        return redirect('project_list')

    messages.error(request, "Invalid request method.")
    return redirect('project_list')

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
        project.save()

        # Team members (ManyToMany)
        team_member_ids = request.POST.getlist("team_members")
        members = User.objects.filter(id__in=team_member_ids)
        project.team_members.set(members)

        messages.success(request, "Project updated successfully!")
        return redirect("project_list")  # Change to your project list URL name

    messages.error(request, "Invalid request method.")
    return redirect("project_list")

def delete_project(request, id):
    """
    Delete a project by its ID.
    """
    project = get_object_or_404(Project, id=id)
    project.delete()
    # Add message to request
    messages.success(request, "Project deleted successfully!")
    # Send JSON with redirect URL
    return JsonResponse({"success": True, "redirect_url": "/projects/"})

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
    host_data_list = HostData.objects.select_related('project').all()

    paginator = Paginator(host_data_list, records_per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, 'hosting.html', {
        'projects': projects,
        'page_obj': page_obj,
        'records_per_page': records_per_page,
        'records_options': [20, 50, 100, 200, 300],
    })


def add_host_data(request):
    """
    Create and save a new host/server record.
    """
    if request.method == "POST":
        try:
            project_id = request.POST.get("project")
            project = Project.objects.get(id=project_id)

            host_data = HostData.objects.create(
                project=project,
                company_name=request.POST.get("company_name"),
                hosting_provider=request.POST.get("hosting_provider"),
                server_name=request.POST.get("server_name"),
                server_type=request.POST.get("server_type"),
                plan_package=request.POST.get("plan_package"),
                server_ip=request.POST.get("server_ip"),
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

            host_data.full_clean()
            host_data.save()
            messages.success(request, "Host Data saved successfully.")

        except Exception as e:
            messages.error(request, f"Failed to save Host Data: {str(e)}")

        return redirect('host_list')

    messages.error(request, "Invalid request method.")
    return redirect('host_list')

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

    data = {
        "host_id": host.id,
        "project_id": host.project.id if host.project else None,
        "project": host.project.project_name if host.project else None,
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

            # Project
            project_id = request.POST.get("project")
            project = Project.objects.get(id=project_id) if project_id else None
            host.project = project

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
            messages.success(request, "Host Data updated successfully.")

        except Exception as e:
            messages.error(request, f"Failed to update Host Data: {str(e)}")

        return redirect('host_list')

    messages.error(request, "Invalid request method.")
    return redirect('host_list')

def delete_host(request, id):
    """
    Delete a host/server record by its ID.
    """
    if request.method == "POST":
        try:
            host = get_object_or_404(HostData, id=id)
            host.delete()
            messages.success(request, "Host deleted successfully.")
            return JsonResponse({
                "success": True,
                "redirect_url": reverse('host_list')  # Redirect back to list page
            })
        except Exception as e:
            messages.error(request, f"Failed to delete host: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request method"})

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
    host_data_list = HostData.objects.select_related('project').all()
    domains = Domain.objects.select_related('project').all()

    # Paginate domains
    paginator = Paginator(domains, records_per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, 'domain.html', {
        'projects': projects,
        'host_data_list': host_data_list,
        'page_obj': page_obj,  # Send paginated domains
        'records_per_page': records_per_page,
        'records_options': [20, 50, 100, 200, 300],
    })

def add_domain(request):
    """
    Create and save a new domain record.
    """
    if request.method == "POST":
        try:
            project_name = request.POST.get('project')
            project = get_object_or_404(Project, project_name=project_name)

            # Convert date strings to date objects
            purchase_date_str = request.POST.get('purchaseDate')
            expiry_date_str = request.POST.get('expiryDate')
            ssl_expiry_str = request.POST.get('sslExpiry')

            purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date() if purchase_date_str else None
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date() if expiry_date_str else None
            ssl_expiry = datetime.strptime(ssl_expiry_str, "%Y-%m-%d").date() if ssl_expiry_str else None

            domain = Domain(
                project=project,
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

            domain.save()
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
        "project_name": domain.project.project_name if domain.project else None,
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
            project_name = request.POST.get('project')
            if project_name:
                project = get_object_or_404(Project, project_name=project_name)
                domain.project = project

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