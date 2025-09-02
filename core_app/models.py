from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator,URLValidator
from django.utils import timezone
import os,re
from django.core.validators import RegexValidator, MinLengthValidator, EmailValidator,MinValueValidator
from django.db.models import *
from decimal import Decimal

# -----------------------------
# User table for team members
# -----------------------------
class Designation(models.Model):
    """Separate table for designations."""
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title
    
class User(models.Model):
    MARITAL_STATUS_CHOICES = [
        ("single", "Single"),
        ("married", "Married"),
        ("divorced", "Divorced"),
        ("widowed", "Widowed"),
    ]
    EMPLOYEE_TYPE_CHOICES = [
        ("fixed", "Fixed"),
        ("salary", "Salary"),
    ]
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]
    first_name = models.CharField(
        max_length=50,
        blank=True,
        validators=[MinLengthValidator(2, "First name must be at least 2 characters.")]
    )
    last_name = models.CharField(
        max_length=50,
         blank=True,
        validators=[MinLengthValidator(2, "Last name must be at least 2 characters.")]
    )
    username = models.CharField(
        max_length=30,
        unique=True,
         blank=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message="Username can contain letters, digits and @/./+/-/_ only."
        )]
    )
    email = models.EmailField(
        unique=True,
         blank=True,
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
    designations = models.ManyToManyField(Designation, blank=True, related_name="users")
    technologies = models.ManyToManyField('Technology', blank=True, related_name="users")
    employee_type = models.CharField(
        max_length=10,
        choices=EMPLOYEE_TYPE_CHOICES,
        blank=True,
        null=True
    )
    fixed_employee_details = models.JSONField(
        blank=True,
        null=True,
        help_text="Stores amount, date, description for fixed employees in JSON format"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    joining_date = models.DateField(blank=True, null=True)
    last_date = models.DateField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )
    marital_status = models.CharField(
        max_length=10,
        choices=MARITAL_STATUS_CHOICES,
        blank=True,
        null=True
    )
    current_address = models.TextField(blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)
    document_link = models.URLField(
            max_length=500,
            blank=True,
            null=True,
            help_text="Paste a valid document link (e.g., Google Drive, Dropbox, etc.)"
        )

    # Bank details
    account_holder = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=30, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    branch = models.CharField(max_length=100, blank=True, null=True)


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
                raise ValidationError("Password must contain at least one uppercase letter.")
            if not re.search(r'[a-z]', self.password):
                raise ValidationError("Password must contain at least one lowercase letter.")
            if not re.search(r'\d', self.password):
                raise ValidationError("Password must contain at least one digit.")
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', self.password):
                raise ValidationError("Password must contain at least one special character.")


        # prevent first name = last name
        if self.first_name and self.last_name and self.first_name.lower() == self.last_name.lower():
            raise ValidationError("First name and last name cannot be the same.")

        # -----------------------------
        # Force bank details to uppercase
        # -----------------------------
        if self.account_holder:
            self.account_holder = self.account_holder.upper()
        if self.account_number:
            self.account_number = self.account_number.upper()
        if self.ifsc_code:
            self.ifsc_code = self.ifsc_code.upper()
        if self.branch:
            self.branch = self.branch.upper()


# -----------------------------
# Project model
# -----------------------------
class Technology(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class AppMode(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

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

    PROJECT_TYPE_CHOICES = [
        ('Fixed', 'Fixed'),
        ('Salary', 'Salary Based'),
    ]

    project_id = models.CharField(max_length=10, unique=True, blank=True, null=True)
    quotation = models.ForeignKey(
        "Quotation",
        on_delete=models.SET_NULL,   # if quotation deleted, keep project but null this field
        blank=True,
        null=True,
    )
    project_name = models.CharField(max_length=255,  unique=True,blank=False, null=False)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default="Fixed")
    start_date = models.DateField(blank=True, null=True)
    technologies = models.ManyToManyField(Technology, blank=True)
    app_mode = models.ForeignKey(AppMode, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default="Ongoing")

    deadline = models.DateField(blank=True, null=True)
    team_members = models.ManyToManyField(User, blank=True, related_name="projects")
    payment_value = models.PositiveIntegerField(default=0, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending")
    live_link = models.URLField(blank=True, null=True)

    # Expenses & Income
    expense = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    developer_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    server_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    third_party_api_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mediator_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) 
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
        
        if self.payment_value is not None and (self.payment_value < 0):
            raise ValidationError("Payment value not in negative.")
    
        if self.project_name:
            qs = Project.objects.filter(project_name__iexact=self.project_name).exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("A project with this name already exists.")

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
        

        # ==== Auto-fill only when creating and quotation exists ====
        if self._state.adding and self.quotation:
            if not self.lead_source:
                self.lead_source = self.quotation.lead_source

            if not self.inquiry_date and hasattr(self.quotation, "date"):
                self.inquiry_date = self.quotation.date

            if not self.quotation_amount and hasattr(self.quotation, "grand_total"):
                self.quotation_amount = self.quotation.grand_total

            if not self.quotation_sent:
                self.quotation_sent = "Yes"
        super().save(*args, **kwargs)
        # ===== Update income with total_paid =====
        self.income = self.total_paid
        super().save(update_fields=["income"])
    
    # ==== Payment Helpers ====
    @property
    def total_paid(self):
        return self.payments.aggregate(total=Sum('amount'))['total'] or 0

    @property
    def remaining_payment(self):
        if self.approval_amount:
            return self.approval_amount - self.total_paid
        return None

    def __str__(self):
        return f"{self.project_id} - {self.project_name}"


# -----------------------------
# Payment model
# -----------------------------
class ProjectPayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Bank Transfer', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('Cash', 'Cash'),
        ('Cheque', 'Cheque'),
        ('Other', 'Other'),
    ]

    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="payments")
    milestone_name = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)

    # Dynamic details
    payment_details = models.JSONField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validate amount
        if self.amount <= 0:
            raise ValidationError("Payment amount must be greater than zero.")

        # Validate method-specific details
        details = self.payment_details or {}

        if self.payment_method == "Bank Transfer":
            required_fields = ["bank_name", "account_no", "ifsc_code"]
        elif self.payment_method == "UPI":
            required_fields = ["upi_id"]
        elif self.payment_method == "Cheque":
            required_fields = ["cheque_no", "cheque_name"]
        else:
            required_fields = []

        for field in required_fields:
            if field not in details or not details[field]:
                raise ValidationError({ "payment_details": f"'{field}' is required for {self.payment_method}." })

        # Prevent overpayment
        if self.project.approval_amount:
            total_other_payments = self.project.payments.exclude(pk=self.pk).aggregate(total=models.Sum('amount'))['total'] or 0
            if total_other_payments + self.amount > self.project.approval_amount:
                raise ValidationError("Payment exceeds project approval amount.")

    def __str__(self):
        return f"{self.project.project_name} - {self.payment_method} - {self.amount}"
    

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
    hosting_provider = models.CharField(max_length=255, blank=True, null=True)
    server_name = models.CharField(max_length=255, blank=True, null=True)  # New
    server_type = models.CharField(max_length=50, blank=True, null=True)
    plan_package = models.CharField(max_length=100, blank=True, null=True)
    server_ip = models.GenericIPAddressField(blank=True, null=True, unique=True)
    operating_system = models.CharField(max_length=100, blank=True, null=True)  # New
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
    memory = models.CharField(max_length=50, blank=True, null=True)  
    RAM = models.CharField(max_length=50, blank=True, null=True)  
    backup_status = models.CharField(max_length=50, blank=True, null=True)  
    linked_services = models.TextField(blank=True, null=True)  
    status = models.CharField(max_length=20, choices=HOST_STATUS_CHOICES, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.purchase_date and self.expiry_date:
            if self.expiry_date < self.purchase_date:
                raise ValidationError("Expiry date cannot be before purchase date.")

        if self.server_cost is not None and self.server_cost < 0:
            raise ValidationError("Server cost cannot be negative.")

        if not self.server_name and not self.hosting_provider:
            raise ValidationError("Either server name or hosting provider must be provided.")

        if self.server_ip:
            if HostData.objects.exclude(pk=self.pk).filter(server_ip=self.server_ip).exists():
                raise ValidationError("This IP address is already in use.")



    def __str__(self):
        return f"{self.hosting_provider or 'No Provider'} - {self.server_ip}"


# -----------------------------
# Domain model
# -----------------------------
class Domain(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Bank Transfer', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('Cash', 'Cash'),
        ('Cheque', 'Cheque'),
        ('Other', 'Other'),
    ]

    PAYMENT_MODE_CHOICES = [
        ('Client', 'Client'),
        ('Company', 'Company'),
    ]

    AUTO_RENEWAL_CHOICES = [
        ('On','On'),
        ('Off','Off')
    ]
    project = models.ManyToManyField(Project, related_name='domains',blank=True)
    domain_name = models.CharField(max_length=255, blank=True, null=True)
    
    sub_domain1 = models.CharField(max_length=255, blank=True, null=True)
    sub_domain2 = models.CharField(max_length=255, blank=True, null=True)

    purchase_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    left_days = models.PositiveIntegerField(blank=True, null=True)
    auto_renewal = models.CharField(max_length=50, choices=AUTO_RENEWAL_CHOICES, blank=True, null=True)

    registrar = models.CharField(max_length=255, blank=True, null=True)
    renewal_status = models.CharField(max_length=50, blank=True, null=True)
    
    dns_configured = models.BooleanField(default=False)
    nameservers = models.TextField(blank=True, null=True)

    ssl_installed = models.BooleanField(default=False)
    ssl_expiry = models.DateField(blank=True, null=True)
    
    credentials_user = models.CharField(max_length=255, blank=True, null=True)
    credentials_pass = models.CharField(max_length=255, blank=True, null=True)
    
    linked_services = models.TextField(blank=True, null=True)
    
    # Payment-related
    domain_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Charge in INR")
    client_payment_status = models.CharField(
        max_length=20,
        choices=[("Received", "Received"), ("Pending", "Pending")],
        default="Pending"
    )
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default="Client")
    payment_details = models.JSONField(blank=True, null=True)

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

         # Validate payment details based on method
        if self.payment_method:
            details = self.payment_details or {}

            if self.payment_method == "Bank Transfer":
                required_fields = ["bank_name", "account_no", "ifsc_code"]
            elif self.payment_method == "UPI":
                required_fields = ["upi_id"]
            elif self.payment_method == "Cheque":
                required_fields = ["cheque_no", "cheque_name"]
            else:
                required_fields = []

            for field in required_fields:
                if field not in details or not details[field]:
                    errors["payment_details"] = f"'{field}' is required for {self.payment_method}."


        if errors:
            raise ValidationError(errors)

    def __str__(self):
        project_list = ", ".join([p.project_id for p in self.project.all()]) or "No Project"
        return f"{self.domain_name or 'No Domain'} ({project_list})"

# -----------------------------
# Quotation model
# -----------------------------

class Quotation(models.Model):
    # Company & Client Info
    company_name = models.CharField(max_length=255)
    company_address = models.TextField(blank=True)
    company_phone = models.CharField(max_length=50, blank=True)
    company_email = models.EmailField(blank=True)

    quotation_no = models.CharField(max_length=50, unique=True,blank=True)
    date = models.DateField()
    valid_until = models.DateField()
    prepared_by = models.ForeignKey(
        'User',               # reference your User model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations_prepared'
    )

    client_name = models.CharField(max_length=255)
    client_contact = models.CharField(max_length=255, blank=True)
    client_email = models.EmailField(blank=True)
    client_address = models.TextField(blank=True)

    #service charge
    SERVICE_CATEGORY_CHOICES = [
    ('web', 'Web Development'),
    ('mobile', 'Mobile Development'),
    ('cloud', 'Cloud Services'),
    ('ai_ml', 'AI/ML Algorithms'),
    ]

    # category = models.CharField(max_length=100, choices=SERVICE_CATEGORY_CHOICES)
    web_services = models.JSONField(blank=True, null=True)
    mobile_services = models.JSONField(blank=True, null=True)
    cloud_services = models.JSONField(blank=True, null=True)
    ai_ml_services = models.JSONField(blank=True, null=True)
    total_service_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Server and domain charge (JSON fields)
    domain_registration = models.JSONField(blank=True, null=True)
    server_hosting = models.JSONField(blank=True, null=True)
    ssl_certificate = models.JSONField(blank=True, null=True)
    email_hosting = models.JSONField(blank=True, null=True)
    total_server_domain_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Summary fields
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_type = models.CharField(max_length=10, choices=[('none', 'None'),('flat','Flat'),('percent','Percent')], default='none')
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    after_discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    #other
    payment_terms = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)
    lead_source = models.CharField(max_length=50, blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    signatory_name = models.CharField(max_length=255, blank=True)
    signatory_designation = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_next_quotation_no(cls):
        year = timezone.now().year
        last_qtn = cls.objects.filter(
            quotation_no__startswith=f"QTN-{year}-"
        ).aggregate(Max('quotation_no'))['quotation_no__max']

        if last_qtn:
            try:
                last_seq = int(last_qtn.split('-')[-1])
            except (IndexError, ValueError):
                last_seq = 0
            new_seq = last_seq + 1
        else:
            new_seq = 1
        return f"QTN-{year}-{str(new_seq).zfill(3)}"
    # def clean(self):
    #     if not self.company_name:
    #         raise ValidationError('Company name is required.')
    #     if not self.date:
    #         raise ValidationError('Quotation date is required.')
    #     if not self.valid_until:
    #         raise ValidationError('Valid until date is required.')
    #     if not self.client_name:
    #         raise ValidationError('Client name is required.')

        
    def save(self, *args, **kwargs):
        #quatation_no generation
        if not self.quotation_no:
            year = timezone.now().year
            last_qtn = Quotation.objects.filter(quotation_no__startswith=f"QTN-{year}-") \
                                        .aggregate(Max('quotation_no'))['quotation_no__max']
            if last_qtn:
                # Extract last sequence number and increment
                try:
                    last_seq = int(last_qtn.split('-')[-1])
                except (IndexError, ValueError):
                    last_seq = 0
                new_seq = last_seq + 1
            else:
                # Table is empty or no quotations for this year -> start from 1
                new_seq = 1
            self.quotation_no = f"QTN-{year}-{str(new_seq).zfill(3)}"

        contact = self.client_contact.strip() if self.client_contact else ""

        # Regex patterns
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        phone_pattern = r"^\+?\d{7,15}$"  # simple phone validation

        if re.match(email_pattern, contact):
            self.client_email = contact
            self.client_contact = ""  # leave phone blank
        elif re.match(phone_pattern, contact):
            self.client_contact = contact
            self.client_email = ""  # leave email blank
        else:
            # Optional: raise error if neither valid
            self.client_contact = "" 
            self.client_email = "" 
            # raise ValidationError("Client Contact must be a valid phone number or email.")

        # Validate dates
        today = timezone.now().date()
        if self.date < today:
            raise ValidationError("Quotation date cannot be in the past.")

        if self.valid_until < self.date:
            raise ValidationError("Valid Until date cannot be before quotation date.")
        
         # Calculate total service charge
        def calc_service_list(service_list):
            if service_list and isinstance(service_list, list):
                for s in service_list:
                    qty = int(s.get('quantity', 1) or 1)
                    unit_price = Decimal(s.get('unit_price', 0) or 0)
                    s['total'] = float(unit_price * qty)
            return service_list

        def safe_total(service_list):
            if service_list and isinstance(service_list, list):
                return sum(Decimal(str(s.get('total', 0))) for s in service_list)
            return Decimal(0)

        self.web_services = calc_service_list(self.web_services)
        self.mobile_services = calc_service_list(self.mobile_services)
        self.cloud_services = calc_service_list(self.cloud_services)
        self.ai_ml_services = calc_service_list(self.ai_ml_services)

        self.total_service_charge = (
            safe_total(self.web_services) +
            safe_total(self.mobile_services) +
            safe_total(self.cloud_services) +
            safe_total(self.ai_ml_services)
        )
        # calculate sub total which is addition of all above services (web,mobile,cloud, ai/ml)
        subtotal = self.total_service_charge
        
        # Calculate total server and domain charges
        def calc_total_list(field_list):
            if field_list and isinstance(field_list, list):
                for f in field_list:
                    included = f.get('included', False)
                    qty = int(f.get('quantity', 1) or 1)  # default 1
                    unit_price = Decimal(f.get('unit_price', 0) or 0)
                    # ALWAYS overwrite total
                    f['total'] = float(unit_price * qty) if included else 0.0
            return field_list

        # --- Recalculate for each category ---
        self.domain_registration = calc_total_list(self.domain_registration)
        self.server_hosting = calc_total_list(self.server_hosting)
        self.ssl_certificate = calc_total_list(self.ssl_certificate)
        self.email_hosting = calc_total_list(self.email_hosting)

        # --- Helper to sum totals ---
        def safe_total_list(field_list):
            if field_list and isinstance(field_list, list):
                return sum(
                    Decimal(str(f.get('total', 0))) for f in field_list
                )
            return Decimal(0)

        # --- Final grand total across all 4 categories ---
        self.total_server_domain_charge = (
            safe_total_list(self.domain_registration) +
            safe_total_list(self.server_hosting) +
            safe_total_list(self.ssl_certificate) +
            safe_total_list(self.email_hosting)
        )
        

        # Calculate tax
        if self.tax_rate > 0:
            self.tax_amount = subtotal * (self.tax_rate / 100)
        else:
            self.tax_amount = subtotal
        
        # Calculate discount value
        if self.discount_type == 'flat':
            self.after_discount_total = self.discount_value
        elif self.discount_type == "percent":
            self.after_discount_total = self.tax_amount * (self.discount_value / 100)
        else:  # 'none'
            self.after_discount_total = Decimal(0)

        # Calculate grand total
        self.grand_total = self.tax_amount - self.after_discount_total + safe_total_list(self.domain_registration) + safe_total_list(self.server_hosting) 

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quotation_no} - {self.client_name} ({self.date})"
    
# -----------------------------
# client model
# -----------------------------
class Client(models.Model):
    # Basic details
    name = models.CharField(max_length=255, help_text="Full name of the client or company")
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Address
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=15, blank=True, null=True)

    # Extra info
    company_name = models.CharField(max_length=255, blank=True, null=True)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    website = models.URLField(blank=True, null=True, validators=[URLValidator()])

    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}

        # --- Name ---
        if self.name and len(self.name.strip()) < 2:
            errors["name"] = "Name must be at least 2 characters long."

        # --- Phone ---
        if self.phone:
            if not re.match(r'^\+?\d{7,15}$', self.phone):
                errors["phone"] = "Enter a valid phone number (7–15 digits, optional +)."

        # --- Pincode ---
        if self.pincode:
            if not re.match(r'^\d{4,10}$', self.pincode):
                errors["pincode"] = "Enter a valid pincode (4–10 digits)."

        # --- GST ---
        if self.gst_number:
            if not re.match(r'^[0-9A-Z]{15}$', self.gst_number):
                errors["gst_number"] = "GST must be 15 uppercase alphanumeric characters."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.company_name if self.company_name else self.name

# -----------------------------
# FileDocs model    
# -----------------------------
class Folder(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="folders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        project_name = self.project.project_name if self.project else "No Project"
        return f"{self.name} ({project_name})"


class FileDoc(models.Model):
    name = models.CharField(max_length=255)
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name="files"
    )
    file = models.FileField(upload_to="files/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name