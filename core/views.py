import requests
from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.core.mail import send_mail
from django.http import HttpResponse

from .models import Setting
from .form import ControllerForm


TOKEN = settings.SMART_HOME_ACCESS_TOKEN
url = settings.SMART_HOME_API_URL
headers = {'Authorization': f'Bearer {TOKEN}'}




class ControllerView(FormView):
    form_class = ControllerForm
    template_name = 'core/control.html'
    success_url = reverse_lazy('form')

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        if (context.get('status')!= 'ok'):
            return HttpResponse('problems', status=502)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):

        context = super(ControllerView, self).get_context_data()
        try:
            r = requests.get(url, headers=headers)
            a = r.json()
            context['status'] = a['status']
            context['data'] = a['data']
        except:
            return HttpResponse('Some problems', status=502)

        return context

    def get_initial(self):

        initial = super(ControllerView, self).get_initial()

        initial['bedroom_target_temperature'] = 21
        initial['hot_water_target_temperature'] = 80

        return initial

    def form_valid(self, form):
        try:
            r = requests.get(
                url,
                headers=headers)
            if r.json()['status'] != 'ok':
                return HttpResponse('Some problems', status=502)
        except:
            return HttpResponse('Some problems', status=502)

        controller_data = r.json().get('data')
        try:
            a = Setting.objects.get(controller_name='bedroom_target_temperature')
            if (a.value!=form.cleaned_data['bedroom_target_temperature']):
                a.value = form.cleaned_data['bedroom_target_temperature']
                a.save()
        except Setting.DoesNotExist:
            Setting.objects.create(
                controller_name='bedroom_target_temperature',
                label='Bedroom target temperature',
                value= form.cleaned_data['bedroom_target_temperature']
            )

        try:
            b = Setting.objects.get(controller_name='hot_water_target_temperature')
            if(b.value!=form.cleaned_data['hot_water_target_temperature']):
                b.value = form.cleaned_data['hot_water_target_temperature']
                b.save()

        except Setting.DoesNotExist:
            Setting.objects.create(
                controller_name='hot_water_target_temperature',
                label='Hot water target temperature value',
                value= form.cleaned_data['hot_water_target_temperature']
            )

        if (controller_data):
            controller_bedroom_light = list(
                filter(lambda x: 'bedroom_light' in x.values(), controller_data)
            )[0]['value']
            controller_bathroom_light = list(
                filter(lambda x: 'bathroom_light' in x.values(), controller_data)
            )[0]['value']
            smoke_detector = list(
                filter(lambda x: 'smoke_detector' in x.values(),
                       controller_data)
            )[0]['value']
            ansv = {'controllers': []}

            if (form.cleaned_data['bedroom_light'] != controller_bedroom_light):
                if (smoke_detector):
                    ansv['controllers'].append(
                        {'name': 'bedroom_light', 'value': False})
                else:
                    ansv['controllers'].append(
                        {'name': 'bedroom_light', 'value': form.cleaned_data['bedroom_light']})
            if (form.cleaned_data['bathroom_light'] != controller_bathroom_light):
                if (smoke_detector):
                    ansv['controllers'].append(
                        {'name': 'bathroom_light', 'value': False})
                else:
                    ansv['controllers'].append(
                        {'name': 'bathroom_light', 'value': form.cleaned_data['bathroom_light']})
            if (form.cleaned_data['bedroom_light'] != controller_bedroom_light or form.cleaned_data['bathroom_light'] != controller_bathroom_light):
                r = requests.post(url, headers=headers, json=ansv)
                if r.json()['status'] != 'ok':
                    return HttpResponse('Some problems w API', status=502)


        return super(ControllerView, self).get(form)

