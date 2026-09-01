from django.db.models import OuterRef, Subquery


def copies_currently_held_by(base_qs, user, status, tx_type, holder_field):
    """Restrict a BookCopy queryset to copies whose most recent hand-off
    transaction of the given type has `holder_field` equal to user.

    Filtering on status plus any historical transaction match is not enough:
    a copy keeps matching an old holder even after it has since been
    reassigned to someone else. So for each copy we look up its latest
    matching transaction and keep only the ones that match — in a single
    query instead of one query per copy.
    """
    from transactions.models import BookTransaction

    latest_holder = BookTransaction.objects.filter(
        book_copy=OuterRef('pk'), transaction_type=tx_type
    ).order_by('-created_at').values(holder_field)[:1]

    return base_qs.filter(status=status).annotate(
        _latest_holder=Subquery(latest_holder)
    ).filter(_latest_holder=user.pk)
