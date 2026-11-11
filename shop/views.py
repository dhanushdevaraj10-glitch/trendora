import json

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect,render
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from shop.form import CoustomUserForm
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout


def _get_safe_next_url(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return '/'


def home(request):
    products = Product.objects.filter(
        status=False,
        category__status=False,
    ).order_by('?')
    return render(request, 'shop/index.html', {'products': products})


def search_products(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query)
            | Q(vendor__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query),
            status=False,
            category__status=False,
        ).order_by('name')
    return render(
        request,
        'shop/search.html',
        {'query': query, 'products': products},
    )


def favViewPage(request):
    if request.user.is_authenticated:
        fav = Favourite.objects.filter(User=request.user)
        return render(request, "shop/fav.html", {"fav": fav})
    else:
        return redirect_to_login(request.get_full_path(), reverse('login'))

def add_to_cart(request):
    if request.headers.get('x-requested-with')=='XMLHttpRequest':
        if request.user.is_authenticated:
            try:
                data = json.loads(request.body)
            except Exception:
                return JsonResponse({'status': 'Invalid data'}, status=400)

            product_id = data.get('pid') or data.get('product_id')
            product_qty = data.get('product_qty') or data.get('qty')

            if not product_id or not product_qty:
                return JsonResponse({'status': 'Missing product id or quantity'}, status=400)

            try:
                product_status = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'status': 'Product not found'}, status=404)

            # check if already in cart (model fields use capitalized names)
            if Cart.objects.filter(User=request.user, Products_id=product_id).exists():
                return JsonResponse({'status': 'Already in Cart'}, status=200)

            try:
                available_qty = product_status.Quantity
                req_qty = int(product_qty)
            except Exception:
                return JsonResponse({'status': 'Invalid quantity'}, status=400)

            if available_qty >= req_qty and req_qty > 0:
                Cart.objects.create(User=request.user, Products_id=product_id, Product_qty=req_qty)
                return JsonResponse({'status': 'Product Added to Cart'}, status=200)

            return JsonResponse({'status': 'Requested quantity not available'}, status=200)
        else:
            return JsonResponse({'status':'login to Add Cart'}, status=200)
        
    else:
        return JsonResponse({'status':'Inavalid Access'},status=200)

def login_page(request):
    if request.user.is_authenticated:
        return redirect(_get_safe_next_url(request))
    else:
        if request.method == 'POST':
            name = (request.POST.get('username') or '').strip()
            pwd = request.POST.get('password')

            user = authenticate(request, username=name, **{'password': pwd})
            if user is not None:
                login(request, user)
                messages.success(request, "Logged in Successfully")
                return redirect(_get_safe_next_url(request))
            else:
                messages.error(request, "Invalid Username or Password")
                return redirect('login')
    return render(request, 'shop/login.html', {'next': request.GET.get('next', '')})

def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Logged out Successfully")
    return redirect('/')

def register(request):
    form = CoustomUserForm()
    if request.method == 'POST':
        form = CoustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registered Successfully")
            return redirect('/login')
    return render(request, 'shop/register.html', {'form': form})

def collections(request):
    categories = Category.objects.filter(status=0)
    return render(request, 'shop/collections.html', {'categories': categories})


def collectionview(request, name):
    category = Category.objects.filter(name=name, status=False).first()
    if not category:
        messages.warning(request, "No such category found")
        return redirect('collections')

    products = Product.objects.filter(category=category, status=False)
    return render(request, 'shop/products/index.html', {'products': products, "category_name": category.name})
    
def product_details(request, pid):
    product = Product.objects.filter(
        id=pid,
        category__status=False,
        status=False,
    ).first()
    if not product:
        messages.warning(request, "No such product found")
        return redirect('collections')

    return render(request, 'shop/products/product_details.html', {'products': product})

def cart_page(request):
    if request.user.is_authenticated:
        cart=Cart.objects.filter(User=request.user)
        return render(request, 'shop/cart.html', {'cart': cart})
    else:
       return redirect_to_login(request.get_full_path(), reverse('login'))
    

def remove_cart(request,cid):
     cartitem=Cart.objects.filter(id=cid, User=request.user).first()
     if not cartitem:
         messages.warning(request, "Cart item not found")
         return redirect('cart')
     cartitem.delete()
     return redirect('cart')

def fav_page(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            try:
                data = json.loads(request.body)
            except Exception:
                return JsonResponse({'status': 'Invalid data'}, status=400)

            Product_id = data.get('pid') or data.get('product_id')
            if not Product_id:
                return JsonResponse({'status': 'Missing product id'}, status=400)

            try:
                product_status = Product.objects.get(id=Product_id)
            except Product.DoesNotExist:
                return JsonResponse({'status': 'Product not found'}, status=404)

            if Favourite.objects.filter(User=request.user, Product_id=Product_id).exists():
                return JsonResponse({'status': 'Product already in Favourite'}, status=200)

            Favourite.objects.create(User=request.user, Product_id=Product_id)
            return JsonResponse({'status': 'Product Added to Favourite'}, status=200)
        else:
            return JsonResponse({'status': 'Login to Add Favourite'}, status=200)
    else:
        return JsonResponse({'status': 'Invalid Access'}, status=200)


def remove_fav(request, fid):
    fav_item = Favourite.objects.filter(id=fid, User=request.user).first()
    if not fav_item:
        messages.warning(request, "Favourite item not found")
        return redirect('favViewPage')
    fav_item.delete()
    return redirect('favViewPage')
