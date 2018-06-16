from django.shortcuts import render
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from webauction.models import *
from .forms import *

def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']
            next = request.POST['next']
            print('Valore next: ' + next)

            error_event = False
            error_string = ''
            already_exist_user = None
            try:
                already_exist_user = User.objects.get(username = username)
            except User.DoesNotExist:
                already_exist_user = None
            if already_exist_user != None:
                error_string += 'Username already exist '
                error_event = True
            if password != confirm_password:
                error_string += 'Password unmatch '
                error_event = True
            if error_event:
                return render(request, 'sign_up.html',
                        {'form':form, 'error_message':error_string})

            q = User.objects.create_user(username = username, password = password, email = email)
            q.save()

            return HttpResponseRedirect(next)
        else:
            form = SignUpForm()
            return render(request, 'sign_up.html',
                    {'form':form, 'error_message':'Form compilation error'})
    if request.method == 'GET':
        # caso in cui sia un GET
        form = SignUpForm()
        return render(request, 'sign_up.html', {'form':form})

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/webauction')
    
