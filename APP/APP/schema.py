import graphene
from login.schema import Query as usersQuery
from login.schema import Mutation as userMutation


class Query(usersQuery, graphene.ObjectType):
    pass


class Mutation(userMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
