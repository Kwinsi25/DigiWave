from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import os,re
from django.core.validators import RegexValidator, MinLengthValidator, EmailValidator

# -----------------------------
# User table for team members
# -----------------------------
class User(models.Model):
    first_name = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(2, "First name must be at least 2 characters.")]
    )
    last_name = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(2, "Last name must be at least 2 characters.")]
    )
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message="Username can contain letters, digits and @/./+/-/_ only."
        )]
    )
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message="Enter a valid email address.")]
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?\d{10,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    designation = models.CharField(max_length=100, blank=True, null=True)
    
    password = models.CharField(
        max_length=128,
        validators=[MinLengthValidator(8, "Password must be at least 8 characters.")]
    )
    
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        # Call the default clean first
        super().clean()

        #Password complexity: at least 1 uppercase, 1 lowercase, 1 digit, 1 special char
        if self.password:
            if not re.search(r'[A-Z]', self.password):
                raise ValidationError({'password': "Password must contain at least one uppercase letter."})
            if not re.search(r'[a-z]', self.password):
                raise ValidationError({'password': "Password must contain at least one lowercase letter."})
            if not re.search(r'\d', self.password):
                raise ValidationError({'password': "Password must contain at least one digit."})
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', self.password):
                raise ValidationError({'password': "Password must contain at least one special character."})


        # prevent first name = last name
        if self.first_name and self.last_name and self.first_name.lower() == self.last_name.lower():
            raise ValidationError("First name and last name cannot be the same.")
# -----------------------------
# Project model
# -----------------------------
class Project(models.Model):
    PROJECT_STATUS_CHOICES = [
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
        ('On Hold', 'On Hold'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Advanced', 'Advanced'),
        ('Paid', 'Paid'),
    ]

    YES_NO_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]

    project_id = models.CharField(max_length=10, unique=True, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=False, null=False)
    technologies = models.CharField(max_length=255, blank=True, null=True)
    app_mode = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default="Ongoing")

    deadline = models.DateField(blank=True, null=True)
    team_members = models.ManyToManyField(User, blank=True, related_name="projects")
    payment_percentage = models.PositiveIntegerField(default=0, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending")
    live_link = models.URLField(blank=True, null=True)

    # Expenses & Income
    expense = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    developer_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    server_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    third_party_api_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    income = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Free service
    free_service = models.TextField(blank=True, null=True)

    # Links
    postman_collection = models.URLField(blank=True, null=True)
    data_folder = models.URLField(blank=True, null=True)
    other_link = models.URLField(blank=True, null=True)

    #New Sales/Lead Tracking Fields
    inquiry_date = models.DateField(blank=True, null=True)
    lead_source = models.CharField(max_length=50, blank=True, null=True)
    quotation_sent = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    demo_given = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)
    quotation_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    approval_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    #Completion & Client Info
    completed_date = models.DateField(blank=True, null=True)
    client_industry = models.CharField(max_length=255, blank=True, null=True)
    contract_signed = models.CharField(max_length=3, choices=YES_NO_CHOICES, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.start_date and self.deadline:
            if self.deadline < self.start_date:
                raise ValidationError("Deadline cannot be before the start date.")
            
        if self.status == "Completed" and not self.completed_date:
            raise ValidationError("Completed projects must have a completion date.")

        if self.contract_signed == "Yes" and not self.approval_amount:
            raise ValidationError("Approval amount is required when contract is signed.")

        if self.quotation_sent == "Yes" and not self.quotation_amount:
            raise ValidationError("Quotation amount is required when quotation is sent.")
        
        if self.payment_percentage is not None and (self.payment_percentage < 0 or self.payment_percentage > 100):
            raise ValidationError("Payment percentage must be between 0 and 100.")

    def save(self, *args, **kwargs):
        if not self.project_id:
            last_project = Project.objects.order_by('-id').first()
            last_number = 0
            if last_project and last_project.project_id:
                # Extract only digits from project_id
                match = re.search(r'\d+', last_project.project_id)
                if match:
                    last_number = int(match.group())
            self.project_id = f"#P{last_number + 1:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project_id} - {self.project_name}"

# -----------------------------
# HostData model
# -----------------------------
class HostData(models.Model):
    HOST_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Expired', 'Expired'),
    ]

    project = models.ManyToManyField(Project, related_name='host_data',blank=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    hosting_provider = models.CharField(max_length=255, blank=True, null=True)
    server_name = models.CharField(max_length=255, blank=True, null=True)  # New
    server_type = models.CharField(max_length=50, blank=True, null=True)
    plan_package = models.CharField(max_length=100, blank=True, null=True)
    server_ip = models.GenericIPAddressField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)  # New
    operating_system = models.CharField(max_length=100, blank=True, null=True)  # New
    control_panel = models.CharField(max_length=50, blank=True, null=True)
    login_url = models.URLField(blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    ssh_username = models.CharField(max_length=100, blank=True, null=True)
    ssh_ftp_access = models.CharField(max_length=50, blank=True, null=True)
    database_name = models.CharField(max_length=100, blank=True, null=True)
    db_username = models.CharField(max_length=100, blank=True, null=True)
    db_password = models.CharField(max_length=255, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    server_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    uptime = models.CharField(max_length=50, blank=True, null=True)  # New
    cpu_usage = models.CharField(max_length=50, blank=True, null=True)  # New
    memory_usage = models.CharField(max_length=50, blank=True, null=True)  # New
    disk_space = models.CharField(max_length=50, blank=True, null=True)  # New
    backup_status = models.CharField(max_length=50, blank=True, null=True)  # New
    linked_services = models.TextField(blank=True, null=True)  # New
    status = models.CharField(max_length=20, choices=HOST_STATUS_CHOICES, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}

        # Expiry must be after purchase
        if self.purchase_date and self.expiry_date:
            if self.expiry_date < self.purchase_date:
                errors['expiry_date'] = ["Expiry date cannot be before purchase date."]

        # Cost must be non-negative
        if self.server_cost is not None and self.server_cost < 0:
            errors['server_cost'] = ["Server cost cannot be negative."]

        # At least one identifier should exist
        if not self.server_name and not self.hosting_provider:
            errors['server_name'] = ["Either server name or hosting provider must be provided."]

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.hosting_provider or 'No Provider'}"


# -----------------------------
# Domain model
# -----------------------------
class Domain(models.Model):
    project = models.ManyToManyField(Project, related_name='domains',blank=True)
    domain_name = models.CharField(max_length=255, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    left_days = models.PositiveIntegerField(blank=True, null=True)
    registrar = models.CharField(max_length=255, blank=True, null=True)
    renewal_status = models.CharField(max_length=50, blank=True, null=True)
    dns_configured = models.BooleanField(default=False)
    nameservers = models.TextField(blank=True, null=True)
    ssl_installed = models.BooleanField(default=False)
    ssl_expiry = models.DateField(blank=True, null=True)
    credentials_user = models.CharField(max_length=255, blank=True, null=True)
    credentials_pass = models.CharField(max_length=255, blank=True, null=True)
    linked_services = models.TextField(blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}

        # Expiry must be after purchase
        if self.purchase_date and self.expiry_date:
            if self.expiry_date < self.purchase_date:
                errors["expiry_date"] = "Expiry date cannot be before purchase date."

        # Auto-calc left_days if expiry exists
        if self.expiry_date:
            today = timezone.now().date()
            self.left_days = max((self.expiry_date - today).days, 0)
        if not self.domain_name:
            errors["domain_name"] = "Domain name is required."
        # Cost-related validation example
        if self.ssl_expiry and self.expiry_date and self.ssl_expiry > self.expiry_date:
            errors["ssl_expiry"] = "SSL expiry cannot be after domain expiry."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        project_list = ", ".join([p.project_id for p in self.project.all()]) or "No Project"
        return f"{self.domain_name or 'No Domain'} ({project_list})"


# from django.db import models
# from django.core.exceptions import ValidationError
# from django.utils import timezone
# import re

# class Quotation(models.Model):
#     QUOTATION_STATUS_CHOICES = [
#         ('Draft', 'Draft'),
#         ('Sent', 'Sent'),
#         ('Accepted', 'Accepted'),
#         ('Rejected', 'Rejected'),
#         ('Expired', 'Expired'),
#     ]

#     project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='quotations')
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_quotations')

#     quotation_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
#     date = models.DateField(default=timezone.now)
#     valid_until = models.DateField(blank=True, null=True)
#     status = models.CharField(max_length=20, choices=QUOTATION_STATUS_CHOICES, default='Draft')

#     # Financials
#     subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#     tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
#     tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#     discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
#     discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#     total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

#     # Notes & Terms
#     terms_conditions = models.TextField(blank=True, null=True)
#     additional_notes = models.TextField(blank=True, null=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def clean(self):
#         # Expiry after issue date
#         if self.valid_until and self.date and self.valid_until < self.date:
#             raise ValidationError("Quotation expiry date cannot be before the issue date.")

#         # Total must be positive
#         if self.total_amount <= 0:
#             raise ValidationError("Total amount must be greater than zero.")

#     def save(self, *args, **kwargs):
#         # Auto-generate quotation number
#         if not self.quotation_number:
#             last_quotation = Quotation.objects.order_by('-id').first()
#             last_number = 0
#             if last_quotation and last_quotation.quotation_number:
#                 match = re.search(r'\d+', last_quotation.quotation_number)
#                 if match:
#                     last_number = int(match.group())
#             self.quotation_number = f"Q{timezone.now().year}-{last_number + 1:04d}"

#         # Auto-calculate amounts
#         self.tax_amount = (self.subtotal * self.tax_percentage) / 100
#         self.discount_amount = (self.subtotal * self.discount_percentage) / 100
#         self.total_amount = self.subtotal + self.tax_amount - self.discount_amount

#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.quotation_number} for {self.project.project_name}"


# # -----------------------------
# # Quotation Item model
# # -----------------------------
# class QuotationItem(models.Model):
#     quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
#     description = models.CharField(max_length=255)
#     quantity = models.PositiveIntegerField(default=1)
#     unit_price = models.DecimalField(max_digits=12, decimal_places=2)
#     total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

#     def save(self, *args, **kwargs):
#         # Calculate total price per item
#         self.total_price = (self.unit_price or 0) * (self.quantity or 0)
#         super().save(*args, **kwargs)

#         # Update quotation subtotal after adding an item
#         if self.quotation:
#             subtotal = sum(item.total_price for item in self.quotation.items.all())
#             self.quotation.subtotal = subtotal
#             self.quotation.save()

#     def __str__(self):
#         return f"{self.description} ({self.quotation.quotation_number})"
