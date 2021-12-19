import json

from django.http import HttpResponse
from django.contrib import admin
from django import forms
from django.shortcuts import render

from import_export.admin import ImportExportModelAdmin

from starwars.utils import ImportUtils
from starwars import models

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

    # global variables to improve performance
    export_qs = None
    total_count = 0
    characters = []

    def export_action(self, request):
        if request.method == 'POST':
            offset = json.loads(request.POST.get('offset'))
            limit = json.loads(request.POST.get('limit'))
            self.characters = []
            if not self.export_qs:
                self.export_qs = models.Characters.objects.all().values_list("name", "height", "mass", "birth_year", "gender")

            for obj in self.export_qs[offset:limit]:
                self.characters.append({
                    "name": obj[0],
                    "height": obj[1],
                    "mass": obj[2],
                    "birth_year": obj[3],
                    "gender": obj[4]
                })

            context = {
                "results": self.characters
            }
            return HttpResponse(json.dumps(context), content_type="application/json")

        # define the queryset you want to export and get the count of rows
        self.total_count = models.Characters.objects.all().count()
        context = {"total_count": self.total_count, "form_title": "Export Characters to csv file",
                   "description": "",
                   "headers": ["Name", "Height", "Mass", "Birth Year", "Gender"],
                   "endpoint": "/admin/starwars/characters/export/",
                   "fileName": "starwars_characters"}
        return render(
            request, "admin/export_starwars_characters.html", context
        )
