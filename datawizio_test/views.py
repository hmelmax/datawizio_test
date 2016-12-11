import datetime
import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

from analyzer import Analyzer

@csrf_exempt
def main_page(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            analyzer = request.session.get("analyzer")
            main_table = analyzer.get_main_table()
            return render(request, "main_page.html", context={"main_table": main_table})
    if request.method == "POST":
        analyzer = request.session.get("analyzer")
        if analyzer.update(request.POST.get("name"),
                        datetime.datetime.strptime(request.POST.get("value"), "%Y-%m-%d")):
            request.session["analyzer"] = analyzer
            return HttpResponse("")
        else:
            return HttpResponse("Wrong date")

    return HttpResponseRedirect("login")


@csrf_exempt
def my_login(request):
    if request.method == "GET":
        return render(request, "login.html")
    if request.method == "POST":
        user_login = request.POST.get("login")
        user_password = request.POST.get("password")
        request.session["analyzer"] = Analyzer(login=user_login, password=user_password)
        if request.session.get("analyzer") is not None:
            print("Analyzer created")
            user = authenticate(username=user_login, password=user_password)
            if user is not None:
                print("autentification OK")
                login(request, user)
                return HttpResponseRedirect('/')
    return render(request, "login.html")

@csrf_exempt
def get_page(request, page):
    if request.method == "GET":
        if request.user.is_authenticated:
            analyzer = request.session.get("analyzer")
            other = analyzer.get_other_tables(int(page))
            return HttpResponse(json.dumps(other))
    return HttpResponseRedirect("login")

@csrf_exempt
def my_logout(request):
    logout(request)
    return HttpResponseRedirect("login")

@csrf_exempt
def user_information(request):
    if request.user.is_authenticated:
        analyzer = request.session.get("analyzer")
        result = analyzer.get_client_info()
        return render(request, "user_info.html", context={"result": result})
    else:
        return HttpResponseRedirect("login")

@csrf_exempt
def get_main_table(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            analyzer = request.session.get("analyzer")
            main_table = analyzer.get_main_table()
            return HttpResponse(json.dumps(main_table))
    return HttpResponseRedirect("login")

@csrf_exempt
def get_pages_count(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            analyzer = request.session.get("analyzer")
            pages_count = analyzer.get_pages_count()
            return HttpResponse(json.dumps(pages_count))
    return HttpResponseRedirect("login")
