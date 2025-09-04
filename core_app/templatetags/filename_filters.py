from django import template
import os

register = template.Library()

@register.filter
def smart_truncate(filename, length=25):
    """Truncate a filename (string) keeping start and end with extension"""
    if not filename:
        return ""   # 🔹 return empty if blank or None
    if not isinstance(filename, str):
        filename = str(filename)

    name, ext = os.path.splitext(filename)
    if len(filename) <= length:
        return filename
    return f"{name[:10]}...{name[-5:]}{ext}"
