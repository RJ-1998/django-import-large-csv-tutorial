from starwars.utils import ImportUtils
from django.contrib import admin
from starwars import models
from import_export.admin import ImportExportModelAdmin
from django.shortcuts import render
from django import forms
from django.http import HttpResponse
import json

# Register your models here.


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(models.Characters)
class CharactersAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("name", "birth_year", "gender")

    def import_action(self, request):
        import_object_status = []
        create_new_characters = []
        if request.method == "POST":
            create_new_characters = []
            # capture payload from request
            csv_file = json.loads(request.POST.get("file_name"))
            reader = json.loads(request.POST.get("rows"))
            column_headers = json.loads(request.POST.get("csv_headers"))
            util_obj = ImportUtils(column_headers)

            for row in reader:
                name = row[util_obj.get_column("NAME")]
                height = util_obj.validate_data(row[util_obj.get_column("HEIGHT")])
                mass = util_obj.validate_data(row[util_obj.get_column("MASS")])
                hair_color = row[util_obj.get_column("HAIR COLOR")]
                eye_color = row[util_obj.get_column("EYE COLOR")]
                skin_color = row[util_obj.get_column("SKIN COLOR")]
                birth_year = row[util_obj.get_column("BIRTH YEAR")]
                gender = row[util_obj.get_column("GENDER")]
                create_new_characters.append(
                    models.Characters(
                        name=name, height=height, mass=mass, hair_color=hair_color, eye_color=eye_color,
                        skin_color=skin_color, birth_year=birth_year, gender=gender))
                import_object_status.append({"character": name, "status": "FINISHED",
                                            "msg": "Character created successfully!"})

            models.Characters.objects.bulk_create(create_new_characters)

            context = {
                "file": csv_file,
                "entries": len(import_object_status),
                "results": import_object_status
            }
            return HttpResponse(json.dumps(context), content_type="application/json")
        form = CsvImportForm()
        context = {"form": form, "form_title": "Upload users csv file.",
                   "description": "The file should have following headers: "
                   "[NAME,HEIGHT,MASS,HAIR COLOR,EYE COLOR,SKIN COLOR,BIRTH YEAR,GENDER]."
                   " The Following rows should contain information for the same.",
                   "endpoint": "/admin/starwars/characters/import/"}
        return render(
            request, "admin/import_starwars_characters.html", context
        )
