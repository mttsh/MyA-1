"""
Fielname: view.py
Description: All view definition and their logical
"""
from calendar import *
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.core.urlresolvers import reverse
from MyA.forms import *
from django.contrib.admin.views.decorators import user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, SetPasswordForm
from MyA.admin import EmployeeResource, CustomerResource, ContactResource, NoteResource


# Index - View
def homesite(request):
    employee = Employee.objects.get(user=request.user.id)
    employee_name = employee.firstname + " " + employee.lastname
    try:
        my_notes = Note.objects.filter(employee=employee)
    except ObjectDoesNotExist:
        my_notes = []

    today = datetime.today()
    try:
        my_events = Event.objects.filter(memberint__employee_id=employee.id).exclude(date__lt=today)
    except ObjectDoesNotExist:
        my_events = []

    return render(request, 'dashboard.html', {'page_title': 'Startseite',
                                          'employee_name': employee_name,
                                          'my_notes': my_notes,
                                          'my_events': my_events})


# ======================================================== #
# Employee - View
# ======================================================== #
# only the superuser is allowed for this view
@user_passes_test(lambda u: u.is_superuser)
def get_employee(request):
    employees = Employee.objects.all()
    return render(request, 'list_employee.html', {'page_title': 'Mitarbeiter', 'employees': employees})


# create a new employee or edit a employee
def details_employee(request, pk=None, is_profile=False):
    is_edit = False
    if pk == None:
        # a new user is will be created
        user = User()
        employee = Employee()
        page_title = "Mitarbeiter anlegen"
    else:
        # an existing user will be edited
        is_edit = True
        employee = get_object_or_404(Employee, id=pk)
        user = employee.user
        # check if the current user has permission to edit this employee/user
        if not (request.user.is_superuser or user == request.user):
            raise PermissionDenied
        # set page title
        if is_profile:
            page_title = "Profil bearbeiten"
        else:
            page_title = "Mitarbeiter ändern"
    if request.method == 'POST':
        # the form for a new user and an existing user differs (password field)
        if is_edit:
            user_form = UserEditForm(request.POST, instance=user)
        else:
            user_form = UserCreationForm(request.POST, instance=user)

        employee_form = EmployeeForm(request.POST, instance=employee)
        if employee_form.is_valid() and user_form.is_valid():
            user = user_form.save()
            # we need to set the relationsship between the user and the employee manually
            employee = employee_form.save(commit=False)
            employee.user = user
            employee.save()

            if is_profile:
                messages.success(request, u'Profil gespeichert')
                return HttpResponseRedirect(reverse('profil'))
            else:
                messages.success(request, u'Mitarbeiter gespeichert')
                return HttpResponseRedirect(reverse('mitarbeiterListe'))
        else:
            messages.error(request, u'Daten konnten nicht gespeichert werden')
            pass
    else:
        employee_form = EmployeeForm(instance=employee)
        # the form for a new user and an existing user differs (password field)
        if is_edit:
            user_form = UserEditForm(instance=user)
        else:
            user_form = UserCreationForm(instance=user)

    return render(request, 'detail.html', {'page_title': page_title, 'forms': [user_form, employee_form]})


def export_employees(request):
    dataset = EmployeeResource().export()
    filename = 'employees.xls'

    # set the response as a downloadable excel file
    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    # set the file name
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

    return response


# ======================================================== #
# Profile - View
# ======================================================== #
# edit Profile - View
def edit_profile(request, pk=None):
    # get the current employee from the current user id
    employee = Employee.objects.get(user=request.user.id)

    # use the view for creating and editing employees but for the current user id
    return details_employee(request, pk=employee.id, is_profile=True)


# ======================================================== #
# Superuser - View
# ======================================================== #
# only the superuser is allowed for this view
@user_passes_test(lambda u: u.is_superuser)
def set_password(request, pk):
    user = get_object_or_404(User, id=pk)
    page_title = "Passwort für User " + user.username + " ändern"
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Das Passwort wurde geändert')
        else:
            messages.error(request, 'Fehler')
    else:
        form = SetPasswordForm(user)
    return render(request, 'detail.html', {'page_title': page_title, 'forms': [form]})


def change_password(request):
    user = request.user
    page_title = "Eigenes Passwort ändern"
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            # we need to update the session after a password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Das Passwort wurde geändert')
        else:
            messages.error(request, 'Fehler')
    else:
        form = PasswordChangeForm(user=user)
    return render(request, 'detail.html', {'page_title': page_title, 'forms': [form]})


# only the superuser is allowed for this view
@user_passes_test(lambda u: u.is_superuser)
def toggle_employee_active(request, pk=None):
    if pk == None:
        messages.error(request, u'Mitarbeiter konnten nicht aktiviert/deaktiviert werden')
    else:
        employee = get_object_or_404(Employee, id=pk)
        user = employee.user
        if user.is_active:
            user.is_active = False
            user.save()
            messages.success(request, u'Mitarbeiter erfolgreich deaktiviert')
        else:
            user.is_active = True
            user.save()
            messages.success(request, u'Mitarbeiter erfolgreich aktiviert')
    return HttpResponseRedirect(reverse('mitarbeiterListe'))


# ======================================================== #
# Customer - View
# ======================================================== #
def get_customer(request):
    customers = Customer.objects.all
    return render(request, 'list_customer.html', {'page_title': 'Kunden', 'customers': customers})


# create a new customer or edit a customer
def details_customer(request, pk=None):
    if pk == None:
        customer = Customer()
        page_title = "Kunden anlegen"
    else:
        customer = get_object_or_404(Customer, id=pk)
        page_title = "Kunden ändern"

    if request.method == 'POST':

        # form sent off
        form = CustomerForm(request.POST, instance=customer)
        # Validity check
        if form.is_valid():
            form.save()
            messages.success(request, u'Daten erfolgreich geändert')
            return HttpResponseRedirect(reverse('kundenliste'))
        else:
            # error message
            messages.error(request, u'Daten konnten nicht gespeichert werden')
            pass
    else:
        # form first call
        form = CustomerForm(instance=customer)
    return render(request, 'detail.html', {'page_title': page_title, 'forms': [form]})


# delete a customer
def delete_customer(request, pk=None, status=None):
    if pk == None:
        messages.error(request, u'Daten konnten nicht gelöscht werden')
    else:
        if status == '2':

            customer = get_object_or_404(Customer, id=pk)
            # check if customer has no contacts
            nocontact = 0
            for c in Contact.objects.raw('SELECT * FROM mya_contact where customer_id='+pk):
                nocontact = 1
            if nocontact == 0:
                customer.delete()
                messages.success(request, u'Daten erfolgreich gelöscht')
            else:
                if customer.status == 0:
                    # Customer has contact so he can only be disabled
                    customer.status = 1
                    Contact.objects.select_related().filter(customer=customer.id).update(status=1)
                    customer.save()
                    messages.success(request, u'Daten erfolgreich de-/aktiviert')
                else:
                    messages.error(request, u'Daten konnten nicht gelöscht werden')
        else:
            customer = get_object_or_404(Customer, id=pk)

            if customer.status == 0:
                customer.status = 1
                Contact.objects.select_related().filter(customer=customer.id).update(status=1)
            elif customer.status == 1:
                customer.status = 0
                Contact.objects.select_related().filter(customer=customer.id).update(status=0)
            customer.save()
            messages.success(request, u'Daten erfolgreich de-/aktiviert')
    return HttpResponseRedirect(reverse('kundenliste'))


def export_customers(request):
    dataset = CustomerResource().export()
    filename = 'customers.xls'

    # set the response as a downloadable excel file
    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    # set the file name
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

    return response


# ======================================================== #
# Contact - View
# ======================================================== #
# all contacts of the selected customer (fk)
def get_contact(request, fk=None):
    contacts = Contact.objects.all().filter(customer_id=fk)
    # show the company in the title - select from customer
    customers = Customer.objects.filter(id=fk)
    for c in customers:
        customername = " - " + c.company
    page_title = "Ansprechpartner" + customername

    # paraameter selcted customer for the list_contact.html using by call view new contact
    return render(request, 'list_contact.html', {'page_title': page_title, 'contacts': contacts, 'selected_customer_id': fk})


# create a new contact or edit a contact
# parameters for create and edit selected customer (foreign key)
#            for edit primary key of the contact
def details_contact(request, pk=None, fk=None):
    # show the company in the title - select from customer
    customers = Customer.objects.filter(id=fk)
    for c in customers:
        customername = " - " + c.company
    # set page-title for a nwe contact or for edit contact
    if pk == None:
        # new contact
        contact = Contact()
        page_title = "Ansprechpartner anlegen" + customername
    else:
        # edit contact
        contact = get_object_or_404(Contact, id=pk)
        page_title = "Ansprechpartner ändern" + customername

    if request.method == 'POST':

        # form sent off
        # parameter of the form selcted customer (fk) per initial
        form = ContactForm(request.POST, instance=contact, initial={'customer': fk})

        # Validity check
        if form.is_valid():
            form = form.save(commit=False)
            # set customer-id
            form.customer_id = fk
            form.save()
            messages.success(request, u'Daten erfolgreich geändert')
            # parameter to filter to the selected customer (fk) per args
            return HttpResponseRedirect(reverse('ansprechpartnerliste', args=[fk]))

        else:
            # error message
            messages.error(request, u'Daten konnten nicht gespeichert werden')
            pass
    else:
        # form first call
        # parameter of the form selcted customer (fk) per initial
        form = ContactForm(instance=contact,  initial={'customer': fk})
    return render(request, 'detail.html', {'page_title': page_title, 'forms': [form]})


# delete a contact
# parameters primary key of the contact and selected customer (foreign key)
def delete_contact(request, pk=None, fk=None, status=None):

    if pk == None:
        messages.error(request, u'Daten konnten nicht gelöscht werden')
    else:
        if status == '2':
            contact = get_object_or_404(Contact, id=pk)
            # check if contact has no notes and no events / memberext
            no_notes_and_events = 0
            for n in Note.objects.raw('SELECT * FROM mya_note where contact_id=' + pk):
                no_notes_and_events = 1
            for e in MemberExt.objects.raw('SELECT * FROM mya_memberext where contact_id=' + pk):
                no_notes_and_events = 1
            if no_notes_and_events == 0:
                contact.delete()
                messages.success(request, u'Daten erfolgreich gelöscht')
            else:
                # check if customer active
                customer = Customer.objects.filter(id=contact.customer_id).first()
                if customer.status == 0 and contact.status == 0:
                    # contact has relaticns to a child-table so it can only be disabled
                    contact.status = 1
                    contact.save()
                    messages.success(request, u'Daten erfolgreich de-/aktiviert')
                else:
                    messages.error(request, u'Daten konnten nicht gelöscht werden')
        else:
            contact = get_object_or_404(Contact, id=pk)
            # check if customer active
            customer = Customer.objects.filter(id=contact.customer_id).first()
            if customer.status == 0:
                if contact.status == 0:
                    contact.status = 1
                elif contact.status == 1:
                    contact.status = 0
                contact.save()
                messages.success(request, u'Daten erfolgreich de-/aktiviert')
            else:
                messages.error(request,
                               u'Anspechpartner konnten nicht de-/aktiviert werden, da der Kunde deaktiviert ist! ')
    # paramter to filter to the selected customer (fk) per args
    return HttpResponseRedirect(reverse('ansprechpartnerliste', args=[fk]))


def export_contacts(request):
    dataset = ContactResource().export()
    filename = 'contacts.xls'

    # set the response as a downloadable excel file
    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    # set the file name
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

    return response


# ======================================================== #
# Note - View
# ======================================================== #
def get_notes(request):
    filtertext=''
    if request.method == 'POST':
        selemployee = request.POST.get('selemployee')
        selcustomer = request.POST.get ('selcustomer')
        selcontact = request.POST.get('selcontact')

        if selemployee == '' and selcustomer == '' and selcontact == '':
            #No filter
            notes = Note.objects.all()
        elif  selcustomer != ''and selcontact == '':
            # filter by customer - no contact
            if selemployee == '':
                notes = Note.objects.raw (
                'SELECT * FROM mya_note WHERE contact_id IN (SELECT id FROM mya_contact WHERE customer_id=' + selcustomer + ')')

            elif selemployee != '':
                # filter employee and customer
                notes = Note.objects.raw ('SELECT * FROM mya_note WHERE employee_id = ' + selemployee + \
                                          ' AND contact_id IN (SELECT id FROM mya_contact WHERE customer_id=' + selcustomer + ')')
                # show employee in filtertext
                for e in Employee.objects.filter (id=int(selemployee)):
                    if filtertext == '':
                        filtertext = 'Filter nach: ' + e.firstname + ' ' + e.lastname
                    else:
                        filtertext += ', ' + e.firstname + ' ' + e.lastname
            # show customer in filtertext
            for c in Customer.objects.filter (id=int(selcustomer)):
                if filtertext == '':
                    filtertext = 'Filter nach: ' + c.company
                else:
                    filtertext += ', ' + c.company
        else:

            if selemployee != '' and selcontact != '':
                # filter employee and contact
                notes = Note.objects.filter (employee_id=int(selemployee), contact_id=int(selcontact))
                # show employee in filtertext
                for e in Employee.objects.filter (id=int(selemployee)):
                    if filtertext == '':
                        filtertext = 'Filter nach: ' + e.firstname + ' ' + e.lastname
                    else:
                        filtertext += ', ' + e.firstname + ' ' + e.lastname
                # show contact in filtertext
                for co in Contact.objects.filter (id=int (selcontact)):
                    if filtertext == '':
                        filtertext = 'Filter nach: ' + co.firstname + ' ' + co.lastname
                    else:
                        filtertext += ', ' + + co.firstname + ' ' + co.lastname
            elif selemployee != '' and selcontact == '':
                # filter employee
                notes = Note.objects.filter (employee_id=int(selemployee))
                # show employee in filtertext
                for e in Employee.objects.filter (id=int(selemployee)):
                    if filtertext == '':
                        filtertext = 'Filter nach: ' + e.firstname + ' ' + e.lastname
                    else:
                        filtertext += ', ' + e.firstname + ' ' + e.lastname
            elif selemployee == '' and selcontact != '':
                # filter contact
                notes = Note.objects.filter ( contact_id=int(selcontact))
                # show contact in filtertext
                for co in Contact.objects.filter (id=int (selcontact)):
                    if filtertext == '':
                        filtertext = 'Filter nach: ' + co.firstname + ' ' + co.lastname
                    else:
                        filtertext += ', ' + + co.firstname + ' ' + co.lastname
    else:
        # first call
        notes = Note.objects.all()

    form = FilterNoteForm ()
    # Contact list for use in javascript for the dynamic list
    mylist = Contact.objects.all ()
    return render(request, 'list_note.html', {'page_title': 'Notizen', 'notes': notes, 'forms': [form], 'mylist': mylist, 'page_filtertext':filtertext})


# create a new note or edit a note
def details_note(request, pk=None):
    if pk == None:
        note = Note()
        page_title = "Notiz anlegen"
    else:
        note = get_object_or_404(Note, id=pk)
        page_title = "Notiz ändern"

    if request.method == 'POST':

        # form sent off
        form = NoteForm(request.POST, instance=note)
        # Validity check
        if form.is_valid():
            form = form.save(commit=False)
            # set contact from the Select-Contact-Field - value form the request
            form.contact_id = request.POST.get('selcontact')
            form.save()
            messages.success(request, u'Daten erfolgreich geändert')
            return HttpResponseRedirect(reverse('notizliste'))
        else:
            # error message
            messages.error(request, u'Daten konnten nicht gespeichert werden')
            pass

    else:

        if pk == None:
            # form first call - to insert a new note
            form = NoteForm(instance=note)
        else:
            # form first call with a pk - to edit a note
            # transfer the customer_id and the contact_id for the unbound selection fields
            form = NoteForm(instance=note,  mycustomer=note.contact.customer_id, mycontact=note.contact_id)

    # Contact list for use in javascript for the dynamic list
    mylist = Contact.objects.all()
    return render(request, 'detail_note.html', {'page_title': page_title, 'forms': [form], 'mylist': mylist})


# delete a note
def delete_note(request, pk=None):
    if pk == None:
        messages.error(request, u'Daten konnten nicht gelöscht werden')
    else:
        note = get_object_or_404(Note, id=pk)
        note.delete()

    return HttpResponseRedirect(reverse('notizliste'))


def export_notes(request):
    dataset = NoteResource().export()
    filename = 'notes.xls'

    # set the response as a downloadable excel file
    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    # set the file name
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

    return response


# ======================================================== #
# Calendar - View
# ======================================================== #
def named_day(day_number):
    # show the name of the day
    return datetime(1900, 1, day_number).strftime("%A")


def named_month(month_number):
    # show the name of the month
    return datetime(1900, month_number, 1).strftime("%B")


def get_calendar(request, year=None, month=None):

    if year!=None and month!=None:
        act_year = int(year)
        act_month = int(month)
    else:
        act_year = datetime.now().year
        act_month = datetime.now().month

    # all events of model Event
    all_events = Event.objects.all()

    # all days of month, output: eg. for month March (3, 31)
    all_month_day = monthcalendar(act_year, act_month)

    # Calculate values for the calender controls. (Januar = 1)
    previous_year = act_year
    previous_month = act_month - 1
    if previous_month == 0:
        previous_year = act_year - 1
        previous_month = 12
    next_year = act_year
    next_month = act_month + 1
    if next_month == 13:
        next_year = act_year + 1
        next_month = 1
    year_after_this = act_year + 1
    year_befor_this = act_year - 1

    return render(request, 'calendar.html',
                  {'page_title': 'Terminkalender',
                   'calendar': all_month_day,
                   'month': act_month,
                   'month_name': named_month(act_month),
                   'year': act_year,
                   'previous_month': previous_month,
                   'previous_month_name': named_month(previous_month),
                   'previous_year': previous_year,
                   'next_month': next_month,
                   'next_month_name': named_month(next_month),
                   'next_year': next_year,
                   'year_before_this': year_befor_this,
                   'year_after_this': year_after_this,
                   'all_events': all_events
                   # 'event_today': event_today
                   })


# create a new event
def details_calendar(request, pk=None, year=None, month=None, day=None):
    act_year = int(year)
    act_month = int(month)
    act_day = int(day)

    act_date = datetime(act_year, act_month, act_day).__format__('%d.%m.%Y')
    if pk == None:
        events = Event()
        page_title = "Neuen Termin anlegen"
    else:

        events = get_object_or_404(Event, id=pk)
        page_title = "Termin ändern"

    if request.method == 'POST':

        # form sent off
        form = EventForm(request.POST, instance=events)

        # Validity check
        if form.is_valid():
            form.save()
            messages.success(request, u'Daten erfolgreich geändert')
            return HttpResponseRedirect(reverse('terminkalender'))
        else:
            # error message
            messages.error(request, u'Daten konnten nicht gespeichert werden')
            pass
    else:
        # form first call
        form = EventForm(instance=events, initial={'date': act_date})
    return render(request, 'detail.html', {'page_title': page_title, 'forms': [form]})


# delete an event in calendar View
def delete_event(request, pk=None):

    if pk == None:
        messages.error(request, u'Daten konnten nicht gelöscht werden')
    else:
        delevent = get_object_or_404(Event, id=pk)
        delevent.delete()

    return HttpResponseRedirect(reverse('terminkalender'))


# create  edit an event
def details_with_Members_calendar(request, pk=None, year=None, month=None, day=None):
    if pk == None:
        # error back to calendar
        return HttpResponseRedirect (reverse ('terminkalender'))
    act_year = int(year)
    act_month = int(month)
    act_day = int(day)

    act_date = datetime(act_year, act_month, act_day).__format__('%d.%m.%Y')

    events = get_object_or_404 (Event, id=pk)

    if request.method == 'POST':
        if request.POST.get ('submit') == 'addEvent':
            # form sent off
            form = EventForm(request.POST, instance=events)

            # Validity check
            if form.is_valid():
                form.save()
                messages.success(request, u'Daten erfolgreich geändert')
                #return HttpResponseRedirect(reverse('terminkalender'))

            else:
                # error message
                messages.error(request, u'Daten konnten nicht gespeichert werden')
                pass
        elif request.POST.get ('submit') == 'addInt':
            selemployee = request.POST.get ('selemployee')
            if pk==None:
                # error message
                messages.error (request, u'Event muss gespeichert werden')
                pass
            elif selemployee=='':
                # error message
                messages.error (request, u'Mitarbeiter muss ausgewählt werden')
                pass
            else:
                if request.POST.get ('leader')=='on':
                    leader = True
                else:
                    leader=False
                memberint=MemberInt(employee_id=int(selemployee),leader= leader,event_id=pk)
                memberint.save()


        elif request.POST.get ('submit') == 'addExt':
            selcontact = request.POST.get ('selcontact')
            if pk==None:
                # error message
                messages.error (request, u'Event muss gespeichert werden')
                pass
            elif selcontact=='':
                # error message
                messages.error (request, u'Ansprechpartner muss ausgewählt werden')
                pass
            else:
                memberext=MemberExt(contact_id=int(selcontact),event_id=pk)
                memberext.save()

    page_title = "Termin ändern"
    form = EventForm (instance=events, initial={'date': act_date})
    memberints = MemberInt.objects.all().filter(event_id=pk)
    memberexts = MemberExt.objects.all().filter(event_id=pk)
    formInt = EventAddMembersInt()
    formExt = EventAddMembersExt()
    return render(request, 'detail_event.html', {'page_title': page_title, 'forms': form,
                                               'memberints': memberints,
                                               'memberexts': memberexts,
                                               'formsL': formInt, 'formsR': formExt})

def delete_MemberInt(request, pk=None):
    if pk == None:
        return HttpResponseRedirect (reverse ('terminkalender'))

    memberInt = get_object_or_404(MemberInt, id=pk)
    eventId=memberInt.event_id
    memberInt.delete()
    # use for select act_date
    event = Event.objects.all ().filter (id=eventId)
    act_date = event[0].date.strftime ('%d.%m.%Y')
    # use for from
    events = get_object_or_404 (Event, id=eventId)

    page_title = "Termin ändern"
    form = EventForm (instance=events, initial={'date': act_date})
    memberints = MemberInt.objects.all().filter(event_id=pk)
    memberexts = MemberExt.objects.all().filter(event_id=pk)
    formInt = EventAddMembersInt()
    formExt = EventAddMembersExt()
    return render(request, 'detail_event.html', {'page_title': page_title, 'forms': form,
                                               'memberints': memberints,
                                               'memberexts': memberexts,
                                               'formsL': formInt, 'formsR': formExt})


def delete_MemberExt(request, pk=None):
    if pk == None:
        return HttpResponseRedirect (reverse ('terminkalender'))

    memberExt = get_object_or_404 (MemberExt, id=pk)
    eventId = memberExt.event_id
    memberExt.delete()
    #use for select act_date
    event= Event.objects.all().filter(id=eventId)
    act_date = event[0].date.strftime ('%d.%m.%Y')
    # use for from
    events = get_object_or_404 (Event, id=eventId)

    page_title = "Termin ändern"
    form = EventForm (instance=events, initial={'date': act_date})
    memberints = MemberInt.objects.all().filter(event_id=pk)
    memberexts = MemberExt.objects.all().filter(event_id=pk)
    formInt = EventAddMembersInt ()
    formExt = EventAddMembersExt ()
    return render (request, 'detail_event.html', {'page_title': page_title, 'forms': form,
                                                'memberints': memberints,
                                                'memberexts': memberexts,
                                                'formsL': formInt, 'formsR': formExt})
