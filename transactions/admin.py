from django.contrib import admin
from .models import BookTransaction


@admin.register(BookTransaction)
class BookTransactionAdmin(admin.ModelAdmin):
    list_display = ['book_copy', 'transaction_type', 'from_user', 'to_user', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['book_copy__inventory_number', 'note']
