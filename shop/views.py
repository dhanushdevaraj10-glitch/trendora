import json

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect,render
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


def _get_guest_cart(request):
    guest_cart = request.session.get('guest_cart', {})
    if not isinstance(guest_cart, dict):
        guest_cart = {}
        request.session['guest_cart'] = guest_cart

    product_ids = [key for key in guest_cart if str(key).isdigit()]
    products = Product.objects.filter(
        id__in=product_ids,
        status=False,
        category__status=False,
    )
    items = []
    for product in products:
        try:
            quantity = int(guest_cart.get(str(product.id), guest_cart.get(product.id, 0)))
        except (TypeError, ValueError):
            continue
        if quantity < 1:
            continue
        items.append({
            'id': product.id,
            'Products': product,
            'Product_qty': quantity,
            'total_cost': product.Selling_price * quantity,
        })
    return items


def _get_guest_favorites(request):
    guest_favorites = request.session.get('guest_favorites', [])
    if not isinstance(guest_favorites, list):
        guest_favorites = []
        request.session['guest_favorites'] = guest_favorites

    product_ids = [product_id for product_id in guest_favorites if str(product_id).isdigit()]
    products = Product.objects.filter(
        id__in=product_ids,
        status=False,
        category__status=False,
    )
    return [{'id': product.id, 'Product': product} for product in products]


def _merge_guest_items(request, user):
    for item in _get_guest_cart(request):
        product = item['Products']
        quantity = min(item['Product_qty'], product.Quantity)
        cart_item = Cart.objects.filter(User=user, Products=product).first()
        if cart_item:
            cart_item.Product_qty = min(cart_item.Product_qty + quantity, product.Quantity)
            cart_item.save(update_fields=['Product_qty'])
        elif quantity > 0:
            Cart.objects.create(User=user, Products=product, Product_qty=quantity)

    existing_favorites = set(
        Favourite.objects.filter(User=user).values_list('Product_id', flat=True)
    )
    favorite_ids = {item['Product'].id for item in _get_guest_favorites(request)}
    for product_id in favorite_ids - existing_favorites:
        Favourite.objects.create(User=user, Product_id=product_id)

    request.session.pop('guest_cart', None)
    request.session.pop('guest_favorites', None)


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
    else:
        fav = _get_guest_favorites(request)
    return render(
        request,
        "shop/fav.html",
        {"fav": fav, "is_guest": not request.user.is_authenticated},
    )

def add_to_cart(request):
    if request.headers.get('x-requested-with')=='XMLHttpRequest':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'status': 'Invalid data'}, status=400)

        product_id = data.get('pid') or data.get('product_id')
        product_qty = data.get('product_qty') or data.get('qty')

        if not product_id or not product_qty:
            return JsonResponse({'status': 'Missing product id or quantity'}, status=400)

        try:
            product = Product.objects.get(
                id=product_id,
                status=False,
                category__status=False,
            )
        except (Product.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'status': 'Product not found'}, status=404)

        try:
            quantity = int(product_qty)
        except (TypeError, ValueError):
            return JsonResponse({'status': 'Invalid quantity'}, status=400)
        if quantity < 1:
            return JsonResponse({'status': 'Invalid quantity'}, status=400)

        if request.user.is_authenticated:
            cart_item = Cart.objects.filter(User=request.user, Products=product).first()
            if cart_item:
                return JsonResponse({'status': 'Already in Cart'}, status=200)
            if quantity <= product.Quantity:
                Cart.objects.create(User=request.user, Products=product, Product_qty=quantity)
                return JsonResponse({'status': 'Product Added to Cart'}, status=200)
        else:
            guest_cart = request.session.get('guest_cart', {})
            if not isinstance(guest_cart, dict):
                guest_cart = {}
            product_key = str(product.id)
            if product_key in guest_cart:
                return JsonResponse({'status': 'Already in Cart'}, status=200)
            if quantity <= product.Quantity:
                guest_cart[product_key] = quantity
                request.session['guest_cart'] = guest_cart
                return JsonResponse({'status': 'Product Added to Cart'}, status=200)

        return JsonResponse({'status': 'Requested quantity not available'}, status=200)
        
    else:
        return JsonResponse({'status':'Invalid Access'},status=400)

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
                _merge_guest_items(request, user)
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
        cart = Cart.objects.filter(User=request.user)
    else:
        cart = _get_guest_cart(request)
    return render(
        request,
        'shop/cart.html',
        {'cart': cart, 'is_guest': not request.user.is_authenticated},
    )
    

def remove_cart(request,cid):
    if request.user.is_authenticated:
        cart_item = Cart.objects.filter(id=cid, User=request.user).first()
        if cart_item:
            cart_item.delete()
            return redirect('cart')
    else:
        guest_cart = request.session.get('guest_cart', {})
        if isinstance(guest_cart, dict) and str(cid) in guest_cart:
            del guest_cart[str(cid)]
            request.session['guest_cart'] = guest_cart
            return redirect('cart')
    messages.warning(request, "Cart item not found")
    return redirect('cart')

def fav_page(request):
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return JsonResponse({'status': 'Invalid Access'}, status=400)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'status': 'Invalid data'}, status=400)

    product_id = data.get('pid') or data.get('product_id')
    if not product_id:
        return JsonResponse({'status': 'Missing product id'}, status=400)

    try:
        product = Product.objects.get(
            id=product_id,
            status=False,
            category__status=False,
        )
    except (Product.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'status': 'Product not found'}, status=404)

    if request.user.is_authenticated:
        if Favourite.objects.filter(User=request.user, Product=product).exists():
            return JsonResponse({'status': 'Product already in Favourite'}, status=200)
        Favourite.objects.create(User=request.user, Product=product)
    else:
        guest_favorites = request.session.get('guest_favorites', [])
        if not isinstance(guest_favorites, list):
            guest_favorites = []
        if product.id in guest_favorites:
            return JsonResponse({'status': 'Product already in Favourite'}, status=200)
        guest_favorites.append(product.id)
        request.session['guest_favorites'] = guest_favorites
    return JsonResponse({'status': 'Product Added to Favourite'}, status=200)


def remove_fav(request, fid):
    if request.user.is_authenticated:
        fav_item = Favourite.objects.filter(id=fid, User=request.user).first()
        if fav_item:
            fav_item.delete()
            return redirect('favViewPage')
    else:
        guest_favorites = request.session.get('guest_favorites', [])
        if isinstance(guest_favorites, list) and fid in guest_favorites:
            guest_favorites.remove(fid)
            request.session['guest_favorites'] = guest_favorites
            return redirect('favViewPage')
    messages.warning(request, "Favourite item not found")
    return redirect('favViewPage')
