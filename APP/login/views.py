"""
Login Views
"""
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import (
    urlsafe_base64_encode,
    urlsafe_base64_decode,
)
from django.views import View
from login.forms import *

from django.core.mail import EmailMessage

from login.tokens import (
    account_activation_token,
    change_password_token,
)

from .models import *
import random

from APP.schema import schema


class Register(View):
    template_name = "Views/register.html"
    context = {}

    @staticmethod
    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            _email = form['email'].value()
            _password = form['password1'].value()

            domain = get_current_site(request).domain
            result = schema.execute(
                '''
                mutation newUser($email:String!, $password:String!){
                    newUser(email:$email, password:$password){
                        user {
                            email
                            isActive
                        }
                    }
                }
                ''',
                variable_values={'email': _email, 'password': _password},
                # context={'domain': domain}
            )

            print(result)

            return HttpResponse('Please confirm your email address to complete the registration')

        return redirect('register')

    def get(self, request):
        form = SignUpForm()

        return render(request, self.template_name, {'form': form})


class Login(View):
    template_name = 'Views/login.html'

    def post(self, request):
        if "_login" in request.POST:
            _email = request.POST.get('email')
            _password = request.POST.get('password')

            user = CustomUser.objects.get(email=_email)
            print(user)
            print(_password)

            if user.check_password(_password):
                login(request, user)

                return HttpResponse("You now are logged!")

            return HttpResponse("Incorrect!")

        # elif "_forgot" in request.POST:
        #     return redirect('restore_email')

        return render(request, self.template_name)

    def get(self, request):
        return render(request, self.template_name)


class RestoreWithEmail(View):
    template_name = 'Views/restore_password.html'

    def post(self, request):
        _email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=_email)
            cont = random.randint(1, 101)
            tk = TokenAux.objects.get(user=user)
            tk.counter = cont
            tk.save()

            mail_subject = 'Restore Password'
            current_site = get_current_site(request)
            message = render_to_string('Mail/acc_restore_password.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': change_password_token.make_token(user),
            })

            email = EmailMessage(
                mail_subject, message, to=[_email]
            )
            email.send()

            return HttpResponse('We have send a link to your email to restore Password')

        except User.DoesNotExist:

            return HttpResponse("This email is not registered!")

    def get(self, request):
        return render(request, self.template_name)


def activate(request, uidb64, token):
    """
    This function is a view that allows users to activate its accounts
    :param request:
    :param uidb64:
    :param token: to check if the current url is active
    :return: http response
    """
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')

        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')

    return HttpResponse('Activation link is invalid!')


class RestorePassword(View):
    template_name = "Views/change_password.html"

    def post(self, request):
        user = request.user
        _password1 = request.POST.get('password1')
        _password2 = request.POST.get('password2')
        if _password1 == _password2:
            user.set_password(_password1)
            user.save()
            return HttpResponse('Your passwod has benn changed succesfully!')

        return HttpResponse('Try Again')

    def get(self, request):

        return render(request, self.template_name)


def restore_password(request, uidb64, token):
    try:
        print("UIDB64: ", uidb64)
        uid = force_text(urlsafe_base64_decode(uidb64))
        print("UID: ", uid)

        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        login(request, user)
        return redirect('newPassword')

    return HttpResponse('The link is invalid!')


