import graphene


class CreatePersonInput(graphene.InputObjectType):
    """
    Inputs for the mutation of above
    """
    email = graphene.String(required=True)
    password = graphene.String(required=True)


class ActivateAccountInput(graphene.InputObjectType):
    """
    Input token and email to activate account
    """
    email = graphene.String(required=True)
    token = graphene.String(required=True)


class LoginInput(CreatePersonInput):
    """
    Login Input
    """
    pass


class RestorePasswordInput(graphene.InputObjectType):
    """
    Inputs to change password
    """
    uidb64 = graphene.String(required=True)
    password1 = graphene.String(required=True)
    password2 = graphene.String(required=True)
