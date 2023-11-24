from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import User, Listing, Bid, Comment, Category, WatchList
from django import forms

class CreateListingForm(forms.Form):

    title = forms.CharField(required=True, label="Title", widget=forms.TextInput())
    description = forms.CharField(required=True, widget=forms.Textarea())
    price = forms.CharField(required=True, widget=forms.NumberInput(attrs={'step':'0.01', 'min':'0'}))
    img_url = forms.CharField(required=False, widget=forms.URLInput())

def index(request):

    return render(request, "auctions/index.html", 
    {"listings": Listing.objects.filter(sold=False)
    })

def login_view(request):

    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):

    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):

    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required
def create_listing(request):

    if request.method == "POST":
        form = CreateListingForm(request.POST)
        if form.is_valid():
            user = request.user
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            price = form.cleaned_data["price"]
            if form.cleaned_data["img_url"] == "":
                img_url = "https://globalauctioneers.co.uk/wp-content/uploads/2020/09/logo.png"
            else:
                img_url = form.cleaned_data["img_url"]
            category = Category.objects.get(id=request.POST["categories"])
            Listing.objects.create(user=user, title=title, description=description, price=price, img_url=img_url, category=category)
        
        return HttpResponseRedirect(reverse('index'))
    
    else:
        return render(request, "auctions/create_listing.html", {
            "form": CreateListingForm(),
            "categories": Category.objects.all().order_by('category')
        })

@login_required
def listing_details(request, listing_id):

    listing = Listing.objects.get(id=listing_id)
    user = request.user
    landlord = True if listing.user == user else False
    category = Category.objects.get(category=listing.category)
    comments = Comment.objects.filter(listing=listing.id)
    watching = WatchList.objects.filter(user = user, listing = listing)
    if watching:
        watching = WatchList.objects.get(user = user, listing = listing)

    return listing, user, landlord, category, comments, watching

@login_required
def listing(request, listing_id):

    listing = listing_details(request, listing_id)
    listing, user, landlord, category = listing[0], listing[1], listing[2], listing[3]
    
    if request.method == "POST":
        comment = request.POST["comment"]
        if comment != "":
            Comment.objects.create(user = user, listing = listing, comment = comment)

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "category": category,
        "comments":Comment.objects.filter(listing=listing.id), 
        "watching": WatchList.objects.filter(user = user, listing = listing).values('watching'), 
        "landlord": landlord
    })

@login_required
def watchlist(request, user_id):

    listing_ids = WatchList.objects.filter(user = request.user, watching=True).values('listing')
    listing = Listing.objects.filter(id__in = listing_ids)
    return render(request, "auctions/watchlist.html", {
        "listings": listing
    })

@login_required
def add_watchlist(request, listing_id):

    listing = listing_details(request, listing_id)
    listing, user, landlord, category, comments = listing[0], listing[1], listing[2], listing[3], listing[4]
    watch = WatchList.objects.filter(user = user, listing = listing)
    if watch:
        watch = WatchList.objects.get(user = user, listing = listing)
        watch.watching = True
        watch.save()
    else:
        WatchList.objects.create(user = user, listing = listing, watching = True)

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "category": category,
        "comments": comments, 
        "watching": WatchList.objects.get(user = user, listing = listing).watching, 
        "landlord": landlord
    })

@login_required
def remove_watchlist(request, listing_id):

    listing = listing_details(request, listing_id)
    listing, user, landlord, category, comments, watch = listing[0], listing[1], listing[2], listing[3], listing[4], listing[5]
    watch.watching = False
    watch.save()

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "category": category,
        "comments": comments, 
        "watching": WatchList.objects.get(user = user, listing = listing).watching, 
        "landlord": landlord
    })

@login_required
def bidding(request, listing_id):

    listing = listing_details(request, listing_id)
    listing, user, landlord, category, comments, watch = listing[0], listing[1], listing[2], listing[3], listing[4], listing[5]
    if request.method == "POST":
        bid = request.POST["bid"]
        listing.price = float(bid)
        listing.save()
        Bid.objects.create(user = user, price = bid, listing = listing)

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "category": category,
        "comments": comments, 
        "watching": watch, 
        "landlord": landlord
    })

@login_required
def close_bidding(request, listing_id):

    listing = listing_details(request, listing_id)
    listing, user, landlord, category, comments, watch = listing[0], listing[1], listing[2], listing[3], listing[4], listing[5]
    listing.sold = True
    listing.save()
    winner = Bid.objects.get(price = listing.price, listing = listing).user
    print(user.id, winner.id)
    is_winner = user.id == winner.id

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "category": category,
        "comments": comments, 
        "watching": watch, 
        "landlord": landlord,
        "is_winner": is_winner
    })

def category(request):

    listings = None
    category = None
    if request.method == "POST":
        category = request.POST["categories"]
        listings = Listing.objects.filter(category=category).filter(sold=False)
    return render(request, "auctions/categories.html", {
        "categories": Category.objects.all().order_by('category'),
        "category": Category.objects.get(id=category).category if category is not None else "",
        "listings": listings
    })

def page_not_found_view(request, exception):

    return render(request, "auctions/404.html", status=404)

def server_error_view(request, *args, **argv):

    return render(request, "auctions/500.html", status=500)