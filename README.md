<div class="flex flex-wrap -mx-2 overflow-hidden xl:-mx-2">
  <div class="my-1 px-2 w-full overflow-hidden xl:my-1 xl:px-2 xl:w-1/2">
    <img
      src="https://res.cloudinary.com/dnd2qugjk/image/upload/v1633247494/cover_photos/django-admin-import-cover.png"
      alt="Django import banner"
    />
  </div>
</div>

>### You can also read the whole article on [my blog](https://rishabh-tech-blog.vercel.app/blog/how-to-import-large-csv-file-in-django-admin)

## Overview

In this tutorial, we will look at an alternative approach to import csv files in django-admin. This tutorial is intended for intermediate to advanced level developers. All the code related to the tutorial is available in the repo.

## Introduction

If you have worked on django, then there's a high probability that you have already used the popular `django-import-export` library which works smoothly in django-admin and gives developers lots of freedom to import/export all sorts of files. (If you haven't seen it do check it out `here` because we'll be using it 😉).

Although it's good for importing model-specific files as it gives the specific headers for that particular model. But what if you want to import data that leads to different tables in your database and you want to perform some custom logic and data validation. Also, suppose you want to import very large files (say 20k rows), it will be computation heavy and will run a lot of queries. I came across the same requirement while I was working on a project and using default django-import-export is not the way to do it. We have to CUSTOMIZE it!

## Setup the project

1. Setup a virtual environment

2. Install Django and create a new project

3. Install django-import-export

```
pip install django-import-export
```

4. Add `django-import-export` to your INSTALLED_APPS

```python:settings.py
INSTALLED_APPS = [
    ...
    'import_export',
]
```

5. Define your models. I've used [StarWars API](https://swapi.dev/) so accordingly, I've created the following model

```python
#models.py
from django.db import models

# Create your models here.
class Characters(models.Model):
    name = models.CharField(max_length=255,null=True,blank=True)
    height = models.FloatField(null=True, blank=True)
    mass = models.FloatField(null=True, blank=True)
    hair_color = models.CharField(max_length=25,null=True, blank=True)
    skin_color = models.CharField(max_length=25,null=True, blank=True)
    eye_color = models.CharField(max_length=25,null=True, blank=True)
    birth_year = models.CharField(max_length=25,null=True, blank=True)
    gender = models.CharField(max_length=25,null=True, blank=True)

    class Meta:
        verbose_name = "Characters"

    def __str__(self):
        return str(self.name)
```

6. Apply `ImportExportModelAdmin` in your admin

```python
#admin.py
# your imports
from import_export.admin import ImportExportModelAdmin

@admin.register(models.Characters)
class CharactersAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    # your admin logic for the model
    ...
```

If you have done the setup correctly then you should be
able to see the **import/export** buttons in the django admin
`attach-image`.

## Create a template

In this step, we'll be overriding the default `import` view of
django and provide our custom template. This template will be
essential in sending and receiving requests to and from the
Django-admin. For this, we have to first override the default import
method of `ImportExportModelAdmin`.

```python
#admin.py
# your imports
from django.shortcuts import render
from django import forms

# create a form field which can input a file
class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

@admin.register(models.Characters)
class CharactersAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ("name","birth_year","gender")

    def import_action(self,request):
        form = CsvImportForm()
        context = {"form": form, "form_title": "Upload StarWars characters csv file.",
                    "description": "The file should have following headers: "
                                    "[NAME,HEIGHT,MASS,HAIR COLOR,EYE COLOR,SKIN COLOR,BIRTH YEAR,GENDER]."
                                    " The Following rows should contain information for the same.",
                                    "endpoint": "/admin/starwars/characters/import/"}
        return render(
            request, "admin/import_starwars_characters.html", context
        )

```

Now create a new html template called `import_starwars_characters.html`
inside the `templates/admin` folder in your app. You can find the template `here` in my git repo.

Once you're done then you'll be able to see your custom template
when you click the import button.

<div class="flex flex-wrap -mx-2 overflow-hidden xl:-mx-2">
  <div class="my-1 px-2 w-full overflow-hidden xl:my-1 xl:px-2 xl:w-1/2">
    <img
      src="https://res.cloudinary.com/dnd2qugjk/image/upload/v1632679694/cover_photos/import_characters_template_wpaoo2.png"
      alt="Custom template to import csv files"
    />
  </div>
</div>

## Add Jquery and AJAX

This is the main step of this recipe. Here we will be doing the paginated AJAX calls
to our python logic inside django itself!

Let's do it step by step.

#### Step1:- Create a promise to read the csv

Yes, you heard it right! We will utilize Javascript's Promises
to read the csv file contents. Here is the code with some useful comments.

```js
//import_starwars_characters.html

// this is the secure way to get some hidden data into javascript from python
// to learn about it more find the resources at the end
{{endpoint|json_script:"endpoint"}}
<script>
  // all the javascript goes here .....
</script>
```

```js
//import_starwars_characters.html

let headers = []; // to store csv file headers
let allData = []; // to store all the rows except headers
let file_name = "";
let totalentries = 0;
// get the endpoint we want our AJAX call to hit
// reading it from json_script
let endpoint = JSON.parse($("#endpoint").text());

// <!--  pagination variables-->
let pageSize = 10;
let pages = 0;
// it will store limit-offset objects
let pageObjs = [];

// <!--  promise to read csv so that submit button gets enabled-->
// <!--  only after file has been read-->

function readCSVPromise(lines) {
  return new Promise((resolve, reject) => {
    // store headers and rows
    headers = lines.slice(0, lines.indexOf("\n")).split(",");
    let data = lines.slice(lines.indexOf("\n") + 1).split("\n");
    data.forEach((row) => {
      let x = row.split(",");
      if (x.length > 1) {
        allData.push(x);
      }
    });
    if (data.length > 0) {
      resolve(true);
    } else {
      reject(false);
    }
  });
}
```

A brief explanation of the above code is that we resolve our promise
if we have the data with length > 0 otherwise we reject the promise.

#### Step2:- Add event listener to read the input file

Let's add an event listener to our file input button that will run when
we upload the file through it. We will then run our promise and wait till it
gets finished. Once it's done, we then start paginating the data using **limit-offset**
method.

```js
//import_starwars_characters.html

//<!--  read csv file and perform pagination of rows-->

$("#csvfile").change((e) => {
  // regex to validate file name and extension
  var regex = /^([^\s]+[a-zA-Z0-9\s_\\.\-:()\[\]])+(.csv)$/;
  if (regex.test($("#csvfile").val().toLowerCase())) {
    // initialize javascript's FileReader
    // Read more here https://developer.mozilla.org/en-US/docs/Web/API/FileReader
    var reader = new FileReader();
    reader.onload = function (e) {
      var lines = e.target.result;
      // start storing all the data
      readCSVPromise(lines)
        .then((result) => {
          // when done start paginating the data
          pages = Math.ceil(allData.length / pageSize);
          for (let pageNo = 1; pageNo <= pages; pageNo++) {
            let limit = pageNo * pageSize;
            let offset = pageNo * pageSize - pageSize;
            if (limit >= allData.length) {
              limit = allData.length;
            }
            pageObjs.push({ limit: limit, offset: offset });
          }
          // enable submit button
          $("#submit").prop("disabled", false);
        })
        .catch((result) => {
          $("#submit").prop("disabled", true);
        });
    };
    file_name = e.target.files.item(0).name;
    reader.readAsText(e.target.files.item(0));
  } else {
    alert("Please select a csv file!!");
  }
});
```

#### Step3:- Send AJAX requests to Django

Now that we have read the csv file and its contents, we are good to
call the AJAX requests to Django. Since we want to do the paginated requests,
there can be **n** number of calls, so we will call them sequentially. Here's
how we do it.

```js
//import_starwars_characters.html

//<!--  Perform multiple sequential AJAX Calls on submit click event  -->

let looper = $.Deferred().resolve();
$("#submit").click((e) => {
  e.preventDefault();
  // $.when.apply is the way to call multiple AJAX calls
  // apply functions accepts two arguments => (this,array of requests)
  // for array of requests we are using map function to loop over pageObjs
  // that returns AJAX request
  $.when
    .apply(
      $,
      $.map(pageObjs, (pageObj, i) => {
        looper = looper.then(() => {
          return callImportRequest(pageObj);
        });
        return looper;
      })
    )
    .then((res) => {
      // once all requests are finished then enable download report button
      console.log("Upload Finished!!");
      $("#downloadReport").show();
    })
    .catch((err) => {
      console.log(err);
    });
});
```

And now to call the actual AJAX request we will do like the following

```js
//import_starwars_characters.html

//<!--  Paginated AJAX call to initiate file upload  -->

function callImportRequest(pageObj) {
  let deferred = $.Deferred();
  let offset = pageObj.offset;
  let limit = pageObj.limit;
  // contains paginated data
  let rows = allData.slice(offset, limit);
  $.ajax({
    type: "POST",
    dataType: "json",
    url: endpoint,
    data: {
      file_name: JSON.stringify(file_name),
      csv_headers: JSON.stringify(headers),
      rows: JSON.stringify(rows),
      page_no: JSON.stringify(offset),
      csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
      action: "post",
    },
    beforeSend: () => {
      $("#spinner").show();
    },
    success: function (data) {
      // here we will update our DOM to show the object status
      $("#file_name").text(data.file);
      totalentries += data.entries;
      $("#entries").text(totalentries);
      $("table").append(
        `<tr class="parent" onclick="handlecollapse($(this))"><td class="checkpoint">Entries: ${offset} to ${limit}</td><td></td><td></td></tr>`
      );
      data.results.forEach((obj) => {
        $("table").append(
          `<tr class="child"><td>${obj.character}</td><td>${obj.status}</td><td>${obj.msg}</td></tr>`
        );
      });
      deferred.resolve(data);
    },
    complete: () => {
      $("#spinner").hide();
    },
  });
  return deferred.promise();
}
```

## Custom import logic

We have made it this far! Now the last step is to Custom import logic to
create the objects in our database. Here we write our custom logic of import
and try to save some queries using `bulk_create`.

```python
#admin.py

# your imports
from starwars.utils import ImportUtils
from django.contrib import admin
from starwars import models
from import_export.admin import ImportExportModelAdmin
from django.shortcuts import render
from django import forms
from django.http import HttpResponse
import json

def import_action(self, request):
    import_object_status = []
    create_new_characters = []
    if request.method == "POST":
        # clear the list for every new request
        create_new_characters = []
        # capture payload from request
        csv_file = json.loads(request.POST.get("file_name"))
        reader = json.loads(request.POST.get("rows"))
        column_headers = json.loads(request.POST.get("csv_headers"))
        # helper class for validation and other stuff
        # look into git repo
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
        # bulk create objects
        models.Characters.objects.bulk_create(create_new_characters)
        # return the response to the AJAX call
        context = {
            "file": csv_file,
            "entries": len(import_object_status),
            "results": import_object_status
        }
        return HttpResponse(json.dumps(context), content_type="application/json")
    # below code just displays the template once in the django-admin
    form = CsvImportForm()
    context = {"form": form, "form_title": "Upload users csv file.",
                "description": "The file should have following headers: "
                "[NAME,HEIGHT,MASS,HAIR COLOR,EYE COLOR,SKIN COLOR,BIRTH YEAR,GENDER]."
                " The Following rows should contain information for the same.",
                "endpoint": "/admin/starwars/characters/import/"}
    return render(
        request, "admin/import_user_from_csv.html", context
    )
```

In brief, the above code just listens to every AJAX request and captures the payload.
Then with that payload, it creates new entries in the `Characters` model and returns
the response back to the call.

## Points to remember

Although the above implementation works pretty well and can handle large csv files, there are
some points to remember while considering this approach.

1. Clicking `Cancel` does not cancel the whole operation. This means that if you close the
   browser window or close the tab or click on cancel, then the operations which have already run can not be reverted.

2. It does not provide you a preview of your data. This is implemented in `django-import-export` pretty well, but sadly not here.
   I will try to include this feature also in the next iteration.

3. You have to do your own data validation either before uploading the file or inside your import logic in Python.

## Conclusion

**Django-import-export** is great and works pretty well for most cases, but when it comes to adding customize business logic
then you have to look for some other alternatives. In this article, I tried to convince you that it is possible to customize the
default `django-import-export` features and you can import large **csv** files. I hope this article has given you some new information
and approach to customizing django-admin. I hope you have learned something new from here and if so then please appreciate the efforts by
liking the post and share it with your peers.

## Resources

1. Official Django docs explaining about [json_script](https://docs.djangoproject.com/en/3.0/ref/templates/builtins/#json-script).
2. Here is an article for [further reading on json_script](https://adamj.eu/tech/2020/02/18/safely-including-data-for-javascript-in-a-django-template/).
3. A great article that explains how to use [deffered objects](http://michaelsoriano.com/working-with-jquerys-ajax-promises-and-deferred-objects/).
