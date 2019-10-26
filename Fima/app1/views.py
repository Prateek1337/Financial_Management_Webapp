from django.shortcuts import render
from app1.forms import UserForm,UserProfileInfoForm,UpdateProfileForm
from django.contrib.auth import authenticate,login,logout
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from app1.models import CurrentTransaction,Friends,UserProfileInfo,OldNotification,NewNotification
from django.contrib.auth.models import User

from app1.forms import TransactionForm
from django.utils import timezone
from django.contrib.auth.hashers import check_password
import copy
# Create your views here.

is_check_notification=False

def index(request):
	return render(request,'app1/index.html')

@login_required
def special(request):
	return HttpResponse("You Are logged in !")

@login_required
def user_logout(request):
	global is_check_notofication
	print("is_check_notification=",is_check_notification)
	if(is_check_notification is True):
		move_notification(request.user)
	logout(request)
	return HttpResponseRedirect(reverse('index'))

def register(request):
	registered=False
	if(request.method=='POST'):
		user_form=UserForm(data=request.POST)
		profile_form=UserProfileInfoForm(data=request.POST)

		if(user_form.is_valid() and profile_form.is_valid()):
			user=user_form.save(commit=False)
			user.set_password(user.password)
			user.username=user.email
			user.save()
			profile=profile_form.save(commit=False)
			profile.user=user
			profile.save()
			regitered=True

		else:
			print(user_form.errors,profile_form.errors)
	else:
		user_form = UserForm()
		profile_form = UserProfileInfoForm()
	return render(request,'app1/registration.html',
						  {'user_form':user_form,
						   'profile_form':profile_form,
						   'registered':registered})

def user_login(request):
	global is_check_notofication
	is_check_notofication=False
	if(request.method=="POST"):
		username=request.POST.get('username')
		password=request.POST.get('password')
		user=authenticate(username=username,password=password)
		if(user):
			if(user.is_active):
				login(request,user)
				return HttpResponseRedirect(reverse('index'))
			else:
				return HttpResponse("Your account was inactive.")

		else:
			print("Someone tried to login and failed.")
			print("They used username: {} and password: {}".format(username,password))
			return HttpResponse("Invalid login details given")
	else:
		return render(request, 'app1/login.html', {})

add_friend=None
@login_required
def user_search(request):
	global add_friend
	if(request.method=='POST'):
		print("I am in if 1")
		query=request.POST.get('q')
		# print(query)
		cur_user=request.user
		# print(request.POST.get('add'),add_friend)
		if(request.POST.get('add') and add_friend):
			f1=Friends()
			f1.user_id1=User.objects.get(id=request.user.id)
			f1.user_id2=User.objects.get(id=add_friend.id)
			f1.save()
			f2=Friends()
			f2.user_id2=User.objects.get(id=request.user.id)
			f2.user_id1=User.objects.get(id=add_friend.id)
			f2.save()
			message=request.user.email+" has added you as a friend"
			add_notification(add_friend,message)
			return HttpResponse('Friend Has been Added Succesfully')
		elif(query is not None):
			is_exist=False
			result=User.objects.filter(email=query)
			if(result.exists() and result[0].username!=request.user.username):
				# print(request.user.username)
				is_friend=False;
				is_friend_query=Friends.objects.filter(user_id1=request.user.id,
					user_id2=result[0].id)
				if(is_friend_query.exists()):
					is_friend=True
				else:
					add_friend=result[0]
				return render(request,'app1/search.html',{'result':result[0],'is_friend':is_friend})
			else:
				return render(request,'app1/search.html')

		else:
			return render(request,'app1/search.html')
	else:
		print("I am in else 1")
		return render(request,'app1/search.html')





@login_required
def make_transaction(request):
	if(request.method=='POST'):
		form=TransactionForm(request.POST)
		is_click=True;
		if(form.is_valid()):
			email=form.cleaned_data['Email']
			action=form.cleaned_data['Action']
			amount=form.cleaned_data['Amount']
			desc=form.cleaned_data['Desc']
			to_user=User.objects.filter(email=email)
			if(to_user.exists()):
				to_friend=Friends.objects.filter(user_id1=request.user.id,
						user_id2=to_user[0].id)
				if(to_friend.exists()):
					new_transaction=CurrentTransaction()
					print(UserProfileInfo.objects.filter(user_id=
							to_friend[0].user_id2.id))
					if(action=='Lent'):
						new_transaction.user_id1=request.user
						new_transaction.user_id2=User.objects.get(id=to_friend[0].user_id2.id)
						new_transaction.lent=UserProfileInfo.objects.filter(user=
							request.user)[0].name
						new_transaction.borrowed=UserProfileInfo.objects.filter(user=
							to_friend[0].user_id2)[0].name
						
						message="You Have Borrowed "+str(amount)+"Rs from"+request.user.email
						add_notification(to_friend[0].user_id2,message)	
						
					else:
						new_transaction.user_id2=request.user
						new_transaction.user_id1=User.objects.get(id=to_friend[0].user_id2.id)
						new_transaction.borrowed=UserProfileInfo.objects.filter(user=
							request.user)[0].name
						new_transaction.lent=UserProfileInfo.objects.filter(user=
							to_friend[0].user_id2)[0].name

						message="You Have Lent "+str(amount)+"Rs to"+request.user.email
						add_notification(to_friend[0].user_id2,message)

					new_transaction.amount=amount
					new_transaction.desc=desc
					new_transaction.tdate=timezone.now()
					new_transaction.save();
					return render(request,'app1/transaction.html',{'to_friend':to_friend,'form':form})

				else:
					return render(request,'app1/transaction.html',{'to_user':to_user,'form':form}) 

			else:
				return render(request,'app1/transaction.html',{'is_click':is_click,'form':form})

		else:
			ValidationError(_('Invalid value'), code='invalid')

	else:
		form=TransactionForm()
		return render(request,'app1/transaction.html',{'form':form})








@login_required
def user_profile_view(request):
	user_info=UserProfileInfo.objects.filter(user=request.user)[0]
	return render(request,"app1/show_profile.html",{"user":request.user,"user_info":user_info})







@login_required
def user_profile(request):
	if(request.method=='POST'):

		form=UpdateProfileForm(request.POST)
		is_clicked=True
		if(form.is_valid()):
			print("form is valid")
			new_name=form.cleaned_data['name']
			old_password=form.cleaned_data['old_password']
		
			if(check_password(old_password,request.user.password)):
				print("Check Password Success")
				new_password=form.cleaned_data['new_password']
				conf_password=form.cleaned_data['conf_password']
				is_update=False
				if(new_password==conf_password):
					is_update=True
					new_user=request.user
					new_user_profile=UserProfileInfo.objects.filter(user=request.user)[0]
					new_user.set_password(new_password)
					new_user_profile.name=new_name
					new_user.save()
					new_user_profile.save()
				print(is_update)
				return render(request,'app1/profile.html',{'is_update':is_update,'form':form})

			return render(request,'app1/profile.html',{'is_clicked':is_clicked,'form':form})
		
		else:
			ValidationError(_('Invalid value'), code='invalid')
	else:
		form=UpdateProfileForm()
		return render(request,'app1/profile.html',{'form':form})




@login_required
def show_notification(request):
	global is_check_notification
	is_check_notification=True
	old_not=copy.deepcopy(OldNotification.objects.filter(user_id=request.user))
	new_not=copy.deepcopy(NewNotification.objects.filter(user_id=request.user))
	return render(request,'app1/notification.html',{'old_not':old_not,'new_not':new_not})




def add_notification(user,message):
	new_notification=NewNotification()
	new_notification.user_id=user
	new_notification.desc=message
	new_notification.save()

def move_notification(user):
	all_obj=NewNotification.objects.filter(user_id=user)
	for obj in all_obj:
		old_obj=OldNotification()
		old_obj.user_id=obj.user_id	
		old_obj.desc=obj.desc
		old_obj.date=obj.date
		old_obj.save()
	NewNotification.objects.filter(user_id=user).delete()



