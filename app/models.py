import uuid

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models, connection


class MyManager(models.Manager):
    def raw_as_qs(self, raw_query, params=()):
        """Execute a raw query and return a QuerySet.  The first column in the
        result set must be the id field for the model.
        :type raw_query: str | unicode
        :type params: tuple[T] | dict[str | unicode, T]
        :rtype: django.db.models.query.QuerySet
        """
        cursor = connection.cursor()
        try:
            cursor.execute(raw_query, params)
            return self.filter(id__in=(x[0] for x in cursor))
        finally:
            cursor.close()


class BasicModels(models.Model):
    modified_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AccountManager(BaseUserManager):
    def create_user(self, username, password=None, **kwargs):
        if not username:
            raise ValueError("Users must have a valid username!")

        account = self.model(
            username=username,
            firstname=kwargs.get('firstname', None),
            middle_initial=kwargs.get('middle_initial', None),
            lastname=kwargs.get('lastname', None),
            gender=kwargs.get('gender', None),
            position=kwargs.get('position', None),
            is_staff=kwargs.get('is_staff', True),
        )
        account.set_password(password)
        account.save()

        return account

    def create_superuser(self, username, password=None, **kwargs):
        account = self.create_user(username, password, **kwargs)
        account.is_admin = True
        account.save()
        return account


class UserAccount(AbstractBaseUser):
    username = models.CharField(unique=True, max_length=50)

    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    can_encode = models.BooleanField(default=False)

    firstname = models.CharField(max_length=200, blank=True, null=True)
    middle_initial = models.CharField(max_length=2, blank=True, null=True)
    lastname = models.CharField(max_length=200, blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    position = models.CharField(max_length=200, blank=True, null=True)

    objects = AccountManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['firstname', 'lastname']

    def get_full_name(self):
        return f"{self.firstname} {self.lastname}"

    def get_short_name(self):
        return self.username

    @property
    def is_superuser(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    def __unicode__(self):
        return self.username


class Category(BasicModels):
    name = models.CharField(max_length=100, null=True, blank=True, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = "Categories"


class Item(BasicModels):
    objects = MyManager()
    name = models.CharField(max_length=100, null=True, blank=True, unique=True)
    selling_price = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=15)
    original_price = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=15)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'items'
        verbose_name = 'Item'
        verbose_name_plural = "Items"
        ordering = ['name']


class Supplier(BasicModels):
    name = models.CharField(max_length=100, null=True, blank=True, unique=True)
    address = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'suppliers'
        verbose_name = 'Supplier'
        verbose_name_plural = "Suppliers"


class Transfer(BasicModels):
    To = models.ForeignKey(Supplier, related_name="to+", on_delete=models.DO_NOTHING)
    items = models.ManyToManyField(Item, through="ItemTransfer")
    user = models.ForeignKey(UserAccount, on_delete=models.DO_NOTHING)
    delivered_by = models.CharField(max_length=255, default='')


class ItemTransfer(BasicModels):
    quantity = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=15)
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING)
    transfer = models.ForeignKey(Transfer, null=True, blank=True, on_delete=models.DO_NOTHING)

    @property
    def calculate_total(self):
        return self.item.original_price * self.quantity


class Arrival(BasicModels):
    types = (
        ('cash', 'cash'),
        ('payable', 'payable'),
    )
    type = models.CharField(max_length=10, choices=types, default='cash')
    items = models.ManyToManyField(Item, through='ItemArrival')
    supplier = models.ForeignKey(Supplier, on_delete=models.DO_NOTHING)
    receipt_no = models.IntegerField()
    user = models.ForeignKey(UserAccount, on_delete=models.DO_NOTHING)

    def __unicode__(self):
        return self.id

    def items_list(self):
        return [a.item for a in self.items.all()]

    @staticmethod
    def apply_filter(start, end, supplier):
        items = Arrival.objects.filter(supplier=supplier).filter(created_date__gt=start, created_date__lt=end)
        return items

    @property
    def get_grand_total(self):
        grand_total = 0
        items_set = self.items.all()
        for item in items_set:
            grand_total = grand_total + item.calculate_total
        return grand_total

    class Meta:
        db_table = 'arrivals'
        verbose_name = 'Arrival'
        verbose_name_plural = "Arrivals"


class ItemArrival(BasicModels):
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING)
    arrival = models.ForeignKey(Arrival, on_delete=models.DO_NOTHING)
    quantity = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=15, default=0)
    price = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=15, default=0)

    def __unicode__(self):
        return f"{self.item.name} {self.quantity}"

    @property
    def calculate_total(self):
        return self.item.original_price * self.quantity

    class Meta:
        db_table = 'item_arrivals'
        verbose_name = 'Item Arrival'
        verbose_name_plural = "Item Arrivals"


class Permission(BasicModels):
    user = models.ForeignKey(UserAccount, on_delete=models.DO_NOTHING)
    message = models.TextField()
    requested_report = models.BooleanField(default=False)
    requested_arrival = models.BooleanField(default=False)


class Event(BasicModels):
    correlation_id = models.UUIDField(default=uuid.uuid4(), unique=True)
    event_action = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    payload = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    auth_user = models.ForeignKey(UserAccount, on_delete=models.DO_NOTHING)
    status = models.SmallIntegerField(default=0)

    class Meta:
        db_table = 'events'
        verbose_name = 'Event Log'
        verbose_name_plural = "Event Logs"
