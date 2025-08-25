from django.contrib import admin
from .models import *
from django.utils.html import format_html




@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "project_id", "project_name", "status",
        "approval_amount", "colored_total_paid", "colored_remaining_payment"
    )
    list_filter = ("status", "payment_status")
    search_fields = ("project_id", "project_name")

    # Show total paid with green color
    def colored_total_paid(self, obj):
        return format_html(
            '<span style="color:green; font-weight:bold;">{}</span>', obj.total_paid
        )
    colored_total_paid.short_description = "Total Paid"

    # Show remaining with red if negative
    def colored_remaining_payment(self, obj):
        if obj.remaining_payment is None:
            return "N/A"
        color = "red" if obj.remaining_payment < 0 else "skyblue"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>', color, obj.remaining_payment
        )
    colored_remaining_payment.short_description = "Remaining Payment"


@admin.register(ProjectPayment)
class ProjectPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "project", "milestone_name", "colored_amount", "payment_date", "payment_method"
    )
    list_filter = ("payment_method", "payment_date")
    search_fields = ("project__project_name", "milestone_name")

    # Colorize payment amount
    def colored_amount(self, obj):
        color = "green" if obj.amount > 0 else "red"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>', color, obj.amount
        )
    colored_amount.short_description = "Amount"

admin.site.register(HostData)
admin.site.register(Domain)
admin.site.register(User)
admin.site.register(Quotation)
admin.site.register(Client)
admin.site.register(Folder)
admin.site.register(FileDoc)