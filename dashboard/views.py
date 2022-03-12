from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
import requests
import datetime

# Create your views here.

def show(request):
    date = datetime.date.today()
    day = datetime.timedelta(days=1)
    daysBehind = 0
    context = {}

    url1 = 'https://api.data.gov.hk/v2/filter?q=%7B%22resource%22%3A%22http%3A%2F%2Fwww.chp.gov.hk%2Ffiles%2Fmisc%2Foccupancy_of_quarantine_centres_eng.csv%22%2C%22section%22%3A1%2C%22format%22%3A%22json%22%2C%22filters%22%3A%5B%5B1%2C%22eq%22%2C%5B%22{:02d}%2F{:02d}%2F{}%22%5D%5D%5D%7D'.format(date.day, date.month, date.year)
    response1 = requests.get(url1)
    url2 = 'https://api.data.gov.hk/v2/filter?q=%7B%22resource%22%3A%22http%3A%2F%2Fwww.chp.gov.hk%2Ffiles%2Fmisc%2Fno_of_confines_by_types_in_quarantine_centres_eng.csv%22%2C%22section%22%3A1%2C%22format%22%3A%22json%22%2C%22filters%22%3A%5B%5B1%2C%22eq%22%2C%5B%22{:02d}%2F{:02d}%2F{}%22%5D%5D%5D%7D'.format(date.day, date.month, date.year)
    response2 = requests.get(url2)

    if response1.status_code!=200 or response2.status_code!=200: #if server is down
        context = {'connected':False}
        return render(request, 'dashboard3.html', context=context)

    if len(response1.json()) == 0 or len(response2.json()) == 0: #if data is not available for the date
        while daysBehind < 7 and (len(response1.json()) == 0 or len(response2.json()) == 0): #keep going back until data is found within 7 days
            date = date - day
            daysBehind+=1
            url1 = 'https://api.data.gov.hk/v2/filter?q=%7B%22resource%22%3A%22http%3A%2F%2Fwww.chp.gov.hk%2Ffiles%2Fmisc%2Foccupancy_of_quarantine_centres_eng.csv%22%2C%22section%22%3A1%2C%22format%22%3A%22json%22%2C%22filters%22%3A%5B%5B1%2C%22eq%22%2C%5B%22{:02d}%2F{:02d}%2F{}%22%5D%5D%5D%7D'.format(date.day, date.month, date.year)
            url2 = 'https://api.data.gov.hk/v2/filter?q=%7B%22resource%22%3A%22http%3A%2F%2Fwww.chp.gov.hk%2Ffiles%2Fmisc%2Fno_of_confines_by_types_in_quarantine_centres_eng.csv%22%2C%22section%22%3A1%2C%22format%22%3A%22json%22%2C%22filters%22%3A%5B%5B1%2C%22eq%22%2C%5B%22{:02d}%2F{:02d}%2F{}%22%5D%5D%5D%7D'.format(date.day, date.month, date.year)
            response1 = requests.get(url1)
            response2 = requests.get(url2)
    if len(response1.json()) == 0 or len(response2.json()) == 0: #if no data found in past 7 days
        context = {'connected':True, 'has_data':False}
        return render(request, 'dashboard3.html', context=context)
    
    #data found
    response1 = response1.json() #deserialize
    response2 = response2.json()
    unitsOccupied, unitsAvailable, peopleQurantined = (0,0,0) #initialize variables

    for centre in response1: #sum required data
        unitsOccupied+=centre['Current unit in use']
        unitsAvailable+=centre['Ready to be used (unit)']
        peopleQurantined+=centre['Current person in use']

    response1 = sorted(response1, key = lambda x: x['Ready to be used (unit)'], reverse=True) #sort by number of units available

    peopleQurantinedValidation = response2[0]['Current number of close contacts of confirmed cases']+response2[0]['Current number of non-close contacts']
    nonCloseContacts = response2[0]['Current number of non-close contacts']

    context = {'connected':True, 'has_data':True, 
    'centres':[{'name':response1[0]['Quarantine centres'], 'units':response1[0]['Ready to be used (unit)']}, #top three centres by availability
    {'name':response1[1]['Quarantine centres'], 'units':response1[1]['Ready to be used (unit)']},
    {'name':response1[2]['Quarantine centres'], 'units':response1[2]['Ready to be used (unit)']}], 
    'data':{'date':date.strftime('%d/%m/%Y'),'units_in_use':unitsOccupied,'units_available':unitsAvailable, 
    'persons_quarantined':peopleQurantined, 'non_close_contacts':nonCloseContacts, 
    'count_consistent':peopleQurantined==peopleQurantinedValidation}}
    return render(request, 'dashboard3.html', context=context)
