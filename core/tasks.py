from __future__ import absolute_import, unicode_literals
from celery import task
from django.core.mail import send_mail
from django.conf import settings
import requests



from coursera_house.core.models import Setting
from django.http import HttpResponse
from django.core.mail import EmailMessage


TOKEN = settings.SMART_HOME_ACCESS_TOKEN
url = settings.SMART_HOME_API_URL
headers = {'Authorization': f'Bearer {TOKEN}'}



@task()
def smart_home_manager():
    ansv = {'controllers': []}
    try:
        r = requests.get(
            url,
            headers=headers)
        if r.json()['status'] != 'ok':
            return HttpResponse('Some problems', status=502)
    except:
        return HttpResponse('Some problems', status=502)
    a = r.json()


    a = a['data']
    data = {x['name']: x for x in a}

    if (data['leak_detector']['value'] == True):
        if (data['cold_water']['value'] == True):
            ansv['controllers'].append({'name': 'cold_water', 'value': False})
        if (data['hot_water']['value']==True):
            ansv['controllers'].append({'name': 'hot_water', 'value': False})

        email = EmailMessage(
            'leak detector',
            'text',
            settings.EMAIL_HOST,
            [settings.EMAIL_RECEPIENT],
        )
        email.send(fail_silently=False)
    



    if (data['cold_water']['value'] == False or data['leak_detector']['value'] == True) :
        if (data['boiler']['value']==True):
            ansv['controllers'].append({'name': 'boiler', 'value': False})
        if (data['washing_machine']['value'] in ('on', 'broken')):
            ansv['controllers'].append({'name': 'washing_machine', 'value': "off"})



    boiler_temperature = data['boiler_temperature']['value']

    hot_water_target_temperature = Setting.objects.get(
        controller_name='hot_water_target_temperature').value
    a = ((data['cold_water']['value']) and
         (not data['leak_detector']['value']) and (
             not data['smoke_detector']['value']) and (
             not data['boiler']))
    if(boiler_temperature):
        if ((boiler_temperature < hot_water_target_temperature * 0.9) and (a)):
            if (data['boiler']['value'] != True):
                ansv['controllers'].append({'name': 'boiler', 'value': True})

        if boiler_temperature > hot_water_target_temperature * 1.1:
            if (data['boiler']['value'] != False):
                ansv['controllers'].append({'name': 'boiler', 'value': False})


    if (data['curtains']['value'] != 'slightly_open'):
        outdoor_light = data['outdoor_light']['value']
        bedroom_light = data['bedroom_light']['value']
        if (outdoor_light < 50 and bedroom_light == False):
            if(data['curtains']['value']!='open'):
                ansv['controllers'].append({'name': 'curtains', 'value': 'open'})
        elif (outdoor_light > 50 or bedroom_light == True):
            if (data['curtains']['value'] != 'close'):
                ansv['controllers'].append({'name': 'curtains', 'value': 'close'})



    if (data['smoke_detector']['value'] == True):

        if (data['air_conditioner']['value']):
            ansv['controllers'].append(
                {'name': 'air_conditioner', 'value': False}
            )

        if (data['bedroom_light']['value']):
            ansv['controllers'].append(
                {'name': 'bedroom_light', 'value': False}
            )

        if (data['bathroom_light']['value']):
            ansv['controllers'].append(
                {'name': 'bathroom_light', 'value': False}
            )

        if (data['boiler']['value']):
            ansv['controllers'].append({'name': 'boiler', 'value': False})
        if (data['washing_machine']['value'] in ('on', 'broken')):
            ansv['controllers'].append(
                {'name': 'washing_machine', 'value': 'off'}
            )




    bedroom_temperature = data['bedroom_temperature']['value']
    bedroom_target_temperature = Setting.objects.get(controller_name='bedroom_target_temperature').value
    b = not data['smoke_detector']['value']

    if (bedroom_temperature > bedroom_target_temperature * 1.1 and b):
        if(data['air_conditioner']['value']!=True):
            ansv['controllers'].append({'name': 'air_conditioner', 'value': True})

    if ((bedroom_temperature < bedroom_target_temperature * 0.9)):
        if(data['air_conditioner']['value']!=False):
            ansv['controllers'].append({'name': 'air_conditioner', 'value': False})





    if ansv['controllers']:
        unique = []
        for item in ansv['controllers']:
            if item not in unique:
                unique.append(item)
        ansv['controllers'] = unique
    if(ansv['controllers']!=[]):

        r = requests.post(url, headers=headers, json=ansv)
        if r.json()['status'] != 'ok':
            return HttpResponse('Some problems w API', status=502)
