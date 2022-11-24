from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
import json


def getData(request):
    # get ajax dict
    ajax_response_dict = json.loads(request.POST['data'])
    print(ajax_response_dict)

    return render(request, 'index.html')
