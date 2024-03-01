from django.http import HttpResponse
import csv
import django.http


def download_csv(modeladmin, request, queryset):
    try:
        if not request.user.is_staff:
            raise PermissionDenied
    except PermissionDenied as err:
            messages.add_message(
                request,
                messages.WARNING,
                f"Be marked as staff in django to run this!",
            )
            return HttpResponseRedirect(reverse("certs:index"))

    opts = queryset.model._meta
    model = queryset.model
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment;filename*="certiffy-export.csv"'
    writer = csv.writer(response)
    field_names = [field.name for field in opts.fields[1:]]
    writer.writerow(field_names)
    # Write data rows
    # for obj in queryset:
    #    writer.writerow([getattr(obj, field) for field in field_names[1:]])
    # Was that easy, but we have issues with contacts which has commas in
    # and is stored as a list too
    for obj in queryset:
        row = []
        for field in field_names:
            if field == "contacts":
                contacts = getattr(obj, field_names[3])
                contacts_str = ",".join(contacts)
                row.append(contacts_str)
            else:
                row.append(getattr(obj, field))
        try:
            writer.writerow(row)
        except Exception as e:
            print("exception")
            print(e.args)
    return response
