import csv
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, TemplateView, UpdateView

from ndh.utils import query_sum

from .forms import ReservationForm, UserForm
from .models import Reservation


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class ReservationListView(StaffRequiredMixin, ListView):
    model = Reservation

    def get_context_data(self, **kwargs):
        return super().get_context_data(total=query_sum(self.model.objects.all(), 'emplacements'), **kwargs)


class ReservationModerateView(StaffRequiredMixin, UpdateView):
    model = Reservation
    fields = []

    def get(self, request, accepte, *args, **kwargs):
        reservation = self.get_object()
        reservation.accepte = accepte == 1
        reservation.save()
        return HttpResponseRedirect(reverse('videgrenier:reservation-list'))


class ReservationUserMixin(LoginRequiredMixin):
    def get_object(self, queryset=None):
        return get_object_or_404(Reservation, user=self.request.user)


class ReservationDeleteView(ReservationUserMixin, DeleteView):
    success_url = reverse_lazy('videgrenier:home')


class ReservationDetailView(ReservationUserMixin, DetailView):
    def get_context_data(self, **kwargs):
        def get_infos(obj, field):
            return obj._meta.get_field(field).verbose_name, obj.__dict__[field]

        infos = [
            get_infos(self.object.user, f) for f in ['last_name', 'first_name']
        ] + [
            get_infos(self.object, f) for f in ['birthdate', 'birthplace', 'id_num', 'id_date', 'id_org', 'plaque',
                                                'phone_number', 'address']
        ]
        return super().get_context_data(infos=infos, **kwargs)


@login_required
def reservation(request):
    ok = True
    try:
        reserv = request.user.reservation
    except Exception as e:
        reserv = None
        if not (settings.DATES_VIDE_GRENIER['open'] <= date.today() <= settings.DATES_VIDE_GRENIER['close']):
            return redirect('videgrenier:fini')
    forms = [UserForm(request.POST or None, instance=request.user),
             ReservationForm(request.POST or None, instance=reserv)]
    if request.method == 'POST':
        for form in forms:
            if form.is_valid():
                form.instance.user = request.user
                form.save()
            else:
                ok = False
        if ok:
            messages.success(request, 'Ces informations ont bien été enregistrées')
            return redirect('videgrenier:reservation-detail')
        else:
            messages.error(request, 'Certains champs présentent des erreurs')
    return render(request, 'videgrenier/reservation_form.html', {'forms': forms})


@staff_member_required
def csview(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="videgrenier.csv"'

    writer = csv.writer(response)
    writer.writerow(['Personne', 'email', 'Naissance', 'Adresse', 'Téléphone', 'Pièce d’identité', 'Immatriculation',
                     'Emplacements', 'Nature', 'Accepté'])
    for reservation in Reservation.objects.all():
        writer.writerow(['%s %s' % (reservation.user.first_name, reservation.user.last_name),
                         reservation.user.email,
                         '%s à %s' % (reservation.birthdate, reservation.birthplace),
                         reservation.address, reservation.phone_number,
                         'n°%s delivrée le %s par %s' % (reservation.id_num, reservation.id_date, reservation.id_org),
                         reservation.plaque,
                         reservation.emplacements,
                         reservation.nature,
                         'Oui' if reservation.accepte else 'Non'])
    return response


class FiniView(TemplateView):
    def get_template_name(self):
        return ['videgrenier/%s.html' % ('apres' if date.today() >= settings.DATES_VIDE_GRENIER['close'] else 'avant')]
