from generator.models import TimetableEntry
from django.db.models import Count

def delete_duplicates(queryset, unique_fields):
    duplicates = (
        queryset.values(*unique_fields)
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )
    
    deleted_count = 0
    for duplicate in duplicates:
        filters = {field: duplicate[field] for field in unique_fields}
        # Get all entries matching these unique fields
        entries = list(queryset.filter(**filters).order_by('-id'))
        # Keep the first one (latest ID), delete the rest
        for entry in entries[1:]:
            print(f"Deleting duplicate entry {entry.id} for {filters}")
            entry.delete()
            deleted_count += 1
    return deleted_count

# 1. Division constraint
print("Cleaning duplicates for Division + Timeslot + Day...")
c1 = delete_duplicates(TimetableEntry.objects.all(), ['division', 'timeslot', 'day'])
print(f"Removed {c1} entries.")

# 2. Faculty constraint (exclude null faculty)
print("Cleaning duplicates for Faculty + Timeslot + Day...")
c2 = delete_duplicates(TimetableEntry.objects.filter(faculty__isnull=False), ['faculty', 'timeslot', 'day'])
print(f"Removed {c2} entries.")

# 3. Room constraint (exclude null room)
print("Cleaning duplicates for Room + Timeslot + Day...")
c3 = delete_duplicates(TimetableEntry.objects.filter(room__isnull=False), ['room', 'timeslot', 'day'])
print(f"Removed {c3} entries.")

print("Cleanup complete.")
