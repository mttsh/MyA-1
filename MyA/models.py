"""
Filename: models.py
Description: Model definitions
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Check the input of the telephone number - numbers and as a separator / or -
REGEX_PHONE = r'^[0-9 -\/]+$'
# Check the input of the 5 digit zip code and enter the city
REGEX_CODE_CITY = r'^\d{5} [a-zA-ZäöüÄÖÜ -ß]+$'


class Employee(models.Model):
    phoneRegex = RegexValidator(regex=REGEX_PHONE,
                                message="Telefonnummern: bitte Zahlen eingeben, Format: 123-456, 123/567")
    plzcityRegex = RegexValidator(regex=REGEX_CODE_CITY, message="5 stellige PLZ und Stadt")
    # this connects the employee to the django auth user model
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField('firstname', max_length=100)
    lastname = models.CharField('lastname', max_length=100)
    GENDER = (
        ('N', 'Keine Auswahl'),
        ('F', 'Frau'),
        ('M', 'Herr'),
    )
    gender = models.CharField('salutation', blank=True, default='N', max_length=1, choices=GENDER)
    title = models.CharField('title', blank=True, max_length=100)
    position = models.CharField('position', max_length=100)
    phone = models.CharField('phone', validators=[phoneRegex], blank=True, max_length=25)
    fax = models.CharField('fax', validators=[phoneRegex], blank=True, max_length=100)
    mobile = models.CharField('mobile', validators=[phoneRegex], blank=True, max_length=100)
    email = models.EmailField('email', blank=True, max_length=100)

    def get_fullname(self):
        """
        Returns the fullname depending on the given fields
        If both firstname and lastname are set, return following format: "F. Lastname"
        """
        if self.firstname and self.lastname:
            return self.firstname[0] + ". " + self.lastname
        elif self.firstname and not self.lastname:
            return self.firstname
        elif not self.firstname and self.lastname:
            return self.lastname
        else:
            return ""

    @receiver(post_save, sender=User)
    def create_employee_for_superuser(sender, instance, created, **kwargs):
        """This signal receiver guarantees a creation of an employee object when the superuser is created"""
        if created and instance.is_superuser:
            employee = Employee()
            # map some user fields to the employee
            employee.firstname = instance.username
            employee.email = instance.email
            employee.position = "Administrator"
            employee.user = instance
            employee.save()

    def __str__(self):
        return "{} {}".format(self.firstname, self.lastname)


class Customer(models.Model):
    phoneRegex = RegexValidator(regex=REGEX_PHONE,
                                message="Telefonnummern: bitte Zahlen eingeben, Format: 123-456, 123/567")
    plzcityRegex = RegexValidator(regex=REGEX_CODE_CITY, message="5 stellige PLZ und Stadt")
    company = models.CharField('company', max_length=100)
    street = models.CharField('street', blank=True, max_length=100)
    plzcity = models.CharField('plzcity', validators=[plzcityRegex], blank=True, max_length=100)
    phone = models.CharField('phone', validators=[phoneRegex], blank=True, max_length=100)
    fax = models.CharField('fax', validators=[phoneRegex], blank=True, max_length=100)
    website = models.CharField('website', blank=True, max_length=100)
    is_active = models.BooleanField('is_active', default=True)

    def __str__(self):
        return "{}".format(self.company)


class Contact(models.Model):
    phoneRegex = RegexValidator(regex=REGEX_PHONE,
                                message="Telefonnummern: bitte Zahlen eingeben, Format: 123-456, 123/567")
    customer = models.ForeignKey(Customer)
    firstname = models.CharField('firstname', max_length=100)
    lastname = models.CharField('lastname', max_length=100)
    GENDER = (
        ('N', 'Keine Auswahl'),
        ('F', 'Frau'),
        ('M', 'Herr'),
    )
    gender = models.CharField('gender', blank=True, default='N', max_length=1, choices=GENDER)
    title = models.CharField('title', blank=True, max_length=100)
    position = models.CharField('position', max_length=100)
    phone = models.CharField('phone', validators=[phoneRegex], blank=True, max_length=25)
    fax = models.CharField('fax', validators=[phoneRegex], blank=True, max_length=100)
    mobile = models.CharField('mobile', validators=[phoneRegex], blank=True, max_length=100)
    email = models.EmailField('email', blank=True, max_length=100)
    is_active = models.BooleanField('is_active', default=True)

    def get_fullname(self):
        """
        Returns the fullname depending on the given fields
        If both firstname and lastname are set, return following format: "F. Lastname"
        """
        if self.firstname and self.lastname:
            return self.firstname[0] + ". " + self.lastname
        elif self.firstname and not self.lastname:
            return self.firstname
        elif not self.firstname and self.lastname:
            return self.lastname
        else:
            return ""

    def __str__(self):
        return "{} - {} {} ".format(self.customer, self.firstname, self.lastname)


class Event(models.Model):
    employee = models.ManyToManyField(Employee, through='MemberInt')  # many to many Field
    contact = models.ManyToManyField(Contact, through='MemberExt')  # many to many Field
    date = models.DateTimeField('date', default=timezone.now().__format__('%d.%m.%Y'))
    starttime = models.TimeField('starttime')
    endtime = models.TimeField('endtime')
    title = models.CharField('title', max_length=100)
    location = models.CharField('location', max_length=100)

    def __str__(self):
        return "{} {} {} {}".format(self.date, self.starttime, self.endtime, self.title)


class MemberExt(models.Model):
    contact = models.ForeignKey(Contact)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    status = models.IntegerField('status', default=0)


class MemberInt(models.Model):
    employee = models.ForeignKey(Employee)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    leader = models.BooleanField('leader', default=False)
    status = models.IntegerField('status', default=0)


class Note(models.Model):
    contact = models.ForeignKey(Contact)
    employee = models.ForeignKey(Employee)
    notetext = models.CharField('notetext', max_length=1000)
    date = models.DateTimeField('date', default=timezone.now())

    def __str__(self):
        return "{}".format(self.notetext)
