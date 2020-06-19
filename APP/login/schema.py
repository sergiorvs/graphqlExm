import random
import graphene
import graphql_jwt

from graphql_jwt.decorators import login_required

from django.contrib.auth import login, get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import logout as do_logout

from APP.celery import debug_task
import login.task as celery

from graphene_django.types import DjangoObjectType
from django.core.mail import EmailMessage

from .models import (
    CustomUser,
    TokenAux,
)
from login.tokens import (
    account_activation_token,
    change_password_token,
)
from login.inputs import (
    ActivateAccountInput,
    CreatePersonInput,
    LoginInput,
    RestorePasswordInput,
)


User = get_user_model()


def get_domain(request: WSGIRequest) -> str:
    """
    Get domain from request
    :param request:
    :return:
    """
    return request.META.get('HTTP_ORIGIN', '') + '/'


class UserType(DjangoObjectType):
    """
    User Type
    """
    class Meta:
        model = CustomUser
        exclude = ['password']


class CreateUser(graphene.Mutation):
    """
    Create User Mutation
    """
    class Arguments:
        create_data = CreatePersonInput(required=True)

    # The class attributes define the response of the mutation
    # user = graphene.Field(UserType)
    Output = UserType

    @staticmethod
    def mutate(self, info, create_data=None):
        _email = create_data.email
        _password = create_data.password

        domain = get_domain(info.context)
        _user = CustomUser(email=_email, password=_password)
        _user.is_active = False
        _user.save()

        num = random.randint(1, 101)
        token_seed = TokenAux(user=_user, counter=num)
        token_seed.save()

        mail_subject = 'Activate your blog account.'
        message = render_to_string('Mail/acc_active_email.html', {
            'user': _user,
            'domain': domain,
            'uid': urlsafe_base64_encode(force_bytes(_user.pk)),
            'token': account_activation_token.make_token(_user),
        })

        celery.send_email.delay(email=_email, subject=mail_subject, message=message)

        # Notice we return an instance of this mutation
        return UserType(
            email=_user.email,
            is_active=_user.is_active)


class ActivateUser(graphene.Mutation):
    """
    Activate Account with email confirmation
    """
    class Arguments:
        activate_data = ActivateAccountInput(required=True)

    Output = UserType

    @staticmethod
    def mutate(self, info, activate_data=None):
        _email = activate_data.email
        _token = activate_data.token
        _user = CustomUser.objects.get(email=_email)
        if account_activation_token.check_token(_user, _token):
            _user.is_active = True
        _user.save()

        return UserType(
            email=_user.email,
            is_active=_user.is_active
        )


class LoginUser(graphene.Mutation):
    """
    Login Mutation
    """
    class Arguments:
        login_data = LoginInput(required=True)

    Output = UserType

    @staticmethod
    def mutate(self, info, login_data):
        _email = login_data.email
        _password = login_data.password

        user = CustomUser.objects.get(email=_email)

        if not user.is_active:
            raise Exception('This account is not activate')
        if not user.check_password(_password):
            raise Exception('email user or password is incorrect!')

        login(info.context, user, backend='django.contrib.auth.backends.ModelBackend')

        return UserType(
            email=user.email,
            is_active=user.is_active
        )


class RestorePasswordRequest(graphene.Mutation):
    """
    Send email with a token to restore password
    """
    class Arguments:
        email = graphene.String()

    Output = UserType

    @staticmethod
    def mutate(self, info, email):
        _email = email

        try:
            user = CustomUser.objects.get(email=_email)
        except CustomUser.DoesNotExist:
            raise Exception("User is not Registered!")

        cont = random.randint(1, 101)
        tk = TokenAux.objects.get(user=user)
        tk.counter = cont
        tk.save()

        domain = get_domain(info.context)
        mail_subject = 'Restore Password'
        message = render_to_string('Mail/acc_restore_password.html', {
            'user': user,
            'domain': domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': change_password_token.make_token(user),
        })

        celery.send_email.delay(email=_email, subject=mail_subject, message=message)

        return UserType(
            email=user.email,
            is_active=user.is_active
        )


class RestorePassword(graphene.Mutation):
    """
    Change to a new password
    """
    class Arguments:
        restore_password_data = RestorePasswordInput(required=True)

    Output = UserType

    @staticmethod
    def mutate(self, info, restore_password_data):
        uidb64 = restore_password_data.uidb64
        uid = force_text(urlsafe_base64_decode(uidb64))
        password1 = restore_password_data.password1
        password2 = restore_password_data.password2

        try:
            user = CustomUser.objects.get(pk=uid)
        except CustomUser.DoesNotExist:
            raise Exception('User is not registered!')
        if password1 != password2:
            raise Exception('The passwords does not match')

        user.set_password(password1)
        user.save()

        return UserType(
            email=user.email,
            is_active=user.is_active
        )


class Query(graphene.ObjectType):
    """
    Graphql Queries
    """
    all_users = graphene.List(UserType)
    user = graphene.Field(
        UserType,
        email=graphene.String()
    )
    is_logged = graphene.Field(
        UserType,
        email=graphene.String()
    )

    @staticmethod
    @login_required
    def resolve_all_users(self, info, **kwargs):
        debug_task.delay()

        return CustomUser.objects.all()

    @staticmethod
    def resolve_user(self, info, **kwargs):
        email = kwargs.get('email')

        return CustomUser.objects.get(email=email)

    @staticmethod
    def resolve_is_logged(self, info, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')

        do_logout(info.context)
        return user


class Mutation(graphene.ObjectType):
    """
    All mutations methods
    """
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

    new_user = CreateUser.Field()
    activate_account = ActivateUser.Field()
    login_user = LoginUser.Field()
    restore_password_request = RestorePasswordRequest.Field()
    restore_password = RestorePassword.Field()
