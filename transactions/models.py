from django.db import models
from django.utils.translation import gettext_lazy as _


class BookTransaction(models.Model):
    class TransactionType(models.TextChoices):
        WAREHOUSE_TO_SCHOOL = 'WAREHOUSE_TO_SCHOOL', _('Warehouse to School')
        LIBRARIAN_TO_TEACHER = 'LIBRARIAN_TO_TEACHER', _('Librarian to Teacher')
        TEACHER_TO_STUDENT = 'TEACHER_TO_STUDENT', _('Teacher to Student')
        STUDENT_RETURN = 'STUDENT_RETURN', _('Student Return')
        TEACHER_RETURN = 'TEACHER_RETURN', _('Teacher Return')
        LOST = 'LOST', _('Lost')
        DAMAGED = 'DAMAGED', _('Damaged')
        WRITTEN_OFF = 'WRITTEN_OFF', _('Written Off')

    book_copy = models.ForeignKey('library.BookCopy', on_delete=models.CASCADE, related_name='transactions')
    from_user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_transactions')
    to_user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_transactions')
    from_location = models.CharField(max_length=300, blank=True)
    to_location = models.CharField(max_length=300, blank=True)
    transaction_type = models.CharField(max_length=30, choices=TransactionType.choices)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Book Transaction'
        verbose_name_plural = 'Book Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.book_copy.inventory_number} - {self.get_transaction_type_display()}'
