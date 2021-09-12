import graphene
import graphql_jwt
from graphene import Date
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.db.models import Prefetch

from shelf.budget.models import *

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'monthly_income',
            'created',
            'modified'
        )

class TransactionType(DjangoObjectType):
    class Meta:
        model = Transaction
        fields = (
            'id',
            'created',
            'modified',
            'amount',
            'source',
            'date',
            'recurring',
            'description',
            'category'
        )

class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = (
            'id',
            'label',
            'monthly_amount',
            'user',
            'created',
            'modified',
            'transactions'
        )

    spent = graphene.Float()

    def resolve_spent(instance, info):
        return instance.spent()

class MonthlyBudgetType(DjangoObjectType):
    class Meta:
        model = MonthlyBudget
        fields = (
            'id',
            'income'
        )

    month = graphene.String()
    year = graphene.String()
    net = graphene.Int()

    def resolve_month(instance, info):
        return instance.date.strftime('%B')

    def resolve_year(instance, info):
        return instance.date.strftime('%Y')

    def resolve_net(instance, info):
        return 100

class CreateCategory(graphene.Mutation):
    class Arguments:
        label = graphene.String()
        monthly_amount = graphene.Int()

    category = graphene.Field(CategoryType)

    def mutate(root, info, label, monthly_amount):
        category = Category(
            label=label,
            monthly_amount=monthly_amount,
            user=info.context.user
        )
        category.save()

        return CreateCategory(category=category)

class CreateTransaction(graphene.Mutation):
    class Arguments:
        amount = graphene.Float()
        source = graphene.String()
        day = graphene.Int()
        description = graphene.String()
        category_id = graphene.ID()
        recurring = graphene.Boolean()

    transaction = graphene.Field(TransactionType)

    def mutate(root, info, amount, source, day, description, category_id, recurring):
        category = Category.objects.get(user=info.context.user, id=category_id)
        transaction = category.transactions.create(
            amount=amount,
            source=source,
            date=day,
            description=description,
            recurring=recurring
        )

        return CreateTransaction(transaction=transaction)

class DeleteCategory(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    category = graphene.Field(CategoryType)

    def mutate(root, info, id):
        category = Category.objects.get(
            id=id,
            user=info.context.user
        )
        category.delete()

        return DeleteCategory(category=category)


class Query(graphene.ObjectType):
    all_categories = graphene.List(CategoryType)
    monthly_budgets = graphene.List(MonthlyBudgetType, year=graphene.String())
    all_budget_years = graphene.List(graphene.String)
    category = graphene.Field(CategoryType, id=graphene.ID(required=True))

    @login_required
    def resolve_all_categories(self, info):
        return Category.objects.filter(user=info.context.user)

    @login_required
    def resolve_monthly_budgets(self, info, year):
        return MonthlyBudget.objects.filter(user=info.context.user, date__year=year)

    @login_required
    def resolve_all_budget_years(self, info):
        years = MonthlyBudget.objects.all().values_list('date__year').distinct().order_by('-date__year')
        return [year[0] for year in years]

    @login_required
    def resolve_category(self, info, id):
        # category also uses transactions when calculating 'spent'.
        # This avoids hitting the db twice when getting 'spent' as well as transaction fields
        prefetch = Prefetch('transactions', queryset=Transaction.objects.order_by('-date'))
        return Category.objects.prefetch_related(prefetch).get(id=id)

class Mutation(graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    create_category = CreateCategory.Field()
    create_transaction = CreateTransaction.Field()
    delete_category = DeleteCategory.Field()
    # verify_token = graphql_jwt.Verify.Field()
    # refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)