from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate,login
#importing for auth
from django.contrib.auth.models import User
from django.contrib.auth import logout
#importing models 
from services.models import Auctionform,Auctiontransaction
#importing sendmail
from django.core.mail import send_mail
#for login required
from django.contrib.auth.decorators import login_required
#importing date and time 
from datetime import date,datetime
#importing for classification for upcoming auctions
from django.db.models import Q
#importing for backup of database and application
import os
import zipfile
from django.conf import settings
from django.core.management import call_command

def userregister(request):

    #saving data from registeration form to auth_user database
    if request.method == "POST":
        username=request.POST['username']
        useremail=request.POST['email']
        userpassword=request.POST['password']

        #checking if username already exist
        if User.objects.filter(username=username).exists():
            return render(request,"userregister.html",{'username_error': 'Username already exists'})

        User.objects.create_user(
            username=username,
            email=useremail,
            password=userpassword
        )

        #sending mail on the mail u have given
        send_mail(
            "Real Time Auction.com",
            f"Thank You {username} u have Successfully Registered on Real Time Auction.com",
            "aadityakalgaonkar@gmail.com",
            [useremail],
            fail_silently=False
        )

        return redirect('login') 
    return render(request, "userregister.html")


def homepage(request):
    return render(request,"homepage.html")

def userlogin(request):

    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('homepage')
        else:
            return render(request, "userlogin.html", {
                'loginerror': 'invalid username or password'
            })

    return render(request, "userlogin.html")

def userlogout(request):

    logout(request)

    return redirect('login')

#for loginrequired if user isnt logged in this wont let them create auction 
@login_required
def auctionformpage(request):
    if request.method == "POST":
        iname=request.POST['itemname']
        ipicture=request.FILES['itempicture']
        icatgory=request.POST['itemcat']
        ibaseprice=request.POST['itembaseprice']
        idate=request.POST['itemdatetoauction']
        itime=request.POST['itemtimetoauction']
        idescription=request.POST['itemdescription']

        Auctionform.objects.create(
            owner=request.user,
            itemname=iname,
            itempicture=ipicture,
            itemcat=icatgory,
            itembaseprice=ibaseprice,
            itemdatetoauction=idate,
            itemtimetoauction=itime,
            itemdescription=idescription
        )
        return redirect('homepage')
    return render(request,"auctionform.html")

def liveauctionpage(request):
    #initalizing current date and time to avariable for classification
    today=date.today()
    currenttime=datetime.now().time()

    #filtering live auctions from auctionform db which is equal to or less than current time
    live=Auctionform.objects.filter(
        itemdatetoauction=today,
        itemtimetoauction__lte=currenttime,
        isactive=True
    )

    #passing live variable in dict
    display={'live':live,}

    return render(request,"liveauction.html",display)

def upcomingauctionpage(request):
    #initalizing current date and time to avariable for classification
    today=date.today()
    currenttime=datetime.now().time()

    #filtering upcoming auctions from auctionform db which is not rqual or more than current time
    upcoming=Auctionform.objects.filter(isactive=True).filter(
        Q(itemdatetoauction__gt=today) |
        Q(itemdatetoauction=today , itemtimetoauction__gt=currenttime)

    )
    display={'upcoming':upcoming}
    return render(request,"upcomingauction.html",display)
'''
@login_required
def userprofile(request):

    profile, created = Profile.objects.get_or_create(
        userid=request.user
    )

    if request.method == "POST":

        profile.usermobileno = request.POST['usermobileno']
        profile.useraddress = request.POST['useraddress']
        profile.userdob = request.POST['userdob']

        profile.save()

        return redirect('homepage')

    return render(request, "userprofile.html", {
        "profile": profile
    })
'''
    
@login_required
def myauctionspage(request):

    auctionslisted=Auctionform.objects.filter(owner=request.user)
    print("my auction called")

    return render(request,"myauctions.html",{'auctions':auctionslisted})

@login_required
def auctionpage(request,id):
    #getting id of perticular auction and assigning it to a variable
    data=Auctionform.objects.get(id=id)
    display={'id':id,'data':data}

    return render(request,"auctionpage.html",display)

@login_required
def historypage(request):

    #sorting the page by datewise
    sort=request.GET.get('sort')

    #getting the auctions from auction transaction table by user id comparing with auth 
    history = Auctiontransaction.objects.filter(
        userid=request.user
    ).select_related('auctionid','auctionid__owner')

    #sorting by latest or oldest bid 
    if sort == "old":
        history = history.order_by('bidtime')
    else:
        history = history.order_by('-bidtime')

    #removing dublicate values 
    seen = set()

    unique_history = []

    for i in history:

        if i.auctionid.id not in seen:

            unique_history.append(i)

            seen.add(i.auctionid.id)

    return render(request, "history.html", {
        'history': unique_history
    })

def aboutus(request):
    return render(request,"aboutus.html")

@login_required
def backupdatabase(request):
    
    # create backup folder and paste the folder path 
    backup_folder = r"D:\backup database and application of real time auction system"

    #to make the directory 
    os.makedirs(backup_folder, exist_ok=True)

    # filename with time 
    filename = f"dbbackup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    #joining file path with file name 
    filepath = os.path.join(
        backup_folder,
        filename
    )

    # create json database backup
    with open(filepath, "w") as f:

        call_command(
            "dumpdata",
            stdout=f
        )

    return HttpResponse(f"Database backuped up at {filepath}")


@login_required
def backupapplication(request):

    # backup location
    backup_folder = r"D:\backup database and application of real time auction system"

    os.makedirs(backup_folder, exist_ok=True)

    # zip filename
    zipname = f"application_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

    zippath = os.path.join(
        backup_folder,
        zipname
    )

    # your project folder
    project_folder = r"D:\django projects\RealTimeAuction"

    # create zip
    with zipfile.ZipFile(
        zippath,
        'w',
        zipfile.ZIP_DEFLATED
    ) as zipf:

        for foldername, subfolders, filenames in os.walk(project_folder):

            # skip unnecessary folders
            if "__pycache__" in foldername or ".git" in foldername:
                continue

            for filename in filenames:

                filepath = os.path.join(
                    foldername,
                    filename
                )

                # relative path inside zip
                arcname = os.path.relpath(
                    filepath,
                    project_folder
                )

                zipf.write(
                    filepath,
                    arcname
                )

    return HttpResponse(
        f"Application Backup Created : {zippath}"
    )

@login_required
def allauctionspage(request):

    #getting all the data from auction form 
    allauctions=Auctionform.objects.all().order_by('-id')

    return render(request,"allauctions.html",{'allauctions':allauctions})