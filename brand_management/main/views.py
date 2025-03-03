import os, json, qrcode, base64, uuid, hashlib, time, re, random
from django.utils.timezone import now
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
import pdfkit
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import localtime
from django.db.models import Q
from django.http import JsonResponse, StreamingHttpResponse, Http404, HttpResponse
from .models import Brand, Campaign, Newsletter, Subscriber, Coupon, TrackingLink
from .forms import BrandForm, SubscriberForm
from xml.etree import ElementTree as ET
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from datetime import datetime, timedelta
from io import BytesIO
from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from django.views.decorators.csrf import ensure_csrf_cookie
from weasyprint import HTML
from django.core.cache import cache
import json
import asyncio
from asgiref.sync import sync_to_async
from django.template import Template, Context
import tempfile
import zipfile

def home(request):
    return render(request, 'base.html')

def brands(request):
    return render(request, 'brands.html')

def get_brands(request):
    query = request.GET.get('query', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    brands = Brand.objects.all()

    if query:
        brands = brands.filter(Q(name__icontains=query) | Q(brand_id__icontains=query))

    if start_date and end_date:
        brands = brands.filter(created_at__date__range=[start_date, end_date])

    data = []
    
    for brand in brands:
        data.append({
            "id": brand.brand_id,
            "brand_id": brand.brand_id,
            "name": brand.name,
            "email": brand.email,
            "phone": brand.phone,
            "address": brand.address,
            "subscription": settings.SUBSCRIPTION_LINK,
            "created_at": localtime(brand.created_at).strftime("%d-%m-%Y %H:%M:%S")
        })

    return JsonResponse(data, safe=False)

def create_brand(request):
    if request.method == "POST":
        form = BrandForm(request.POST)
        if form.is_valid():
            brand = form.save(commit=False)
            brand.subscription_link = settings.SUBSCRIPTION_LINK
            brand.save()
            return JsonResponse({
                "name": brand.name,
                "brand_id": brand.brand_id,
                "email": brand.email,
                "phone": brand.phone,
                "address": brand.address,
                "subscription_link": brand.subscription_link,
                "created_at": localtime(brand.created_at).strftime("%d-%m-%Y %H:%M:%S")
            })
        else:
            return JsonResponse({"error": "Invalid form data", "details": form.errors}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

def brand_detail(request, brand_id):
    brand = get_object_or_404(Brand, brand_id=brand_id)
    campaigns = Campaign.objects.filter(brand=brand)
    newsletters = Newsletter.objects.all()
    subscribers = Subscriber.objects.all()

    context = {
        "brand": brand,
        "campaigns": campaigns,
        "newsletters": newsletters,
        "subscribers": subscribers,
        "subscription_link": settings.SUBSCRIPTION_LINK,
    }
    return render(request, "brand_detail.html", context)

def subscribe(request):
    form = SubscriberForm()

    if request.method == "POST":
        form = SubscriberForm(request.POST)
        if form.is_valid():
            subscriber = form.save()
            return redirect('subscription_success')

    return render(request, 'subscribe.html', {'form': form})

def subscription_success(request):
    return render(request, 'subscription_success.html')

def newsletter_list(request):
    newsletters = Newsletter.objects.all()
    campaigns = Campaign.objects.all()
    return render(request, "newsletters.html", {"newsletters": newsletters, "campaigns": campaigns})

   
def search_campaigns(request):
    query = request.GET.get("query", "").strip()

    campaigns = Campaign.objects.filter(campaign_id__icontains=query)[:10]

    return JsonResponse({
        "campaigns": [{"campaign_id": c.campaign_id, "name": c.name} for c in campaigns]
    })


def create_campaign(request, brand_id):
    if request.method == "POST":
        brand = get_object_or_404(Brand, brand_id=brand_id)
        name = request.POST.get("name")
        campaign_id = request.POST.get("campaign_id")

        if Campaign.objects.filter(campaign_id=campaign_id).exists():
            return JsonResponse({"error": "Campaign ID already exists"}, status=400)

        campaign = Campaign.objects.create(
            brand=brand,
            name=name,
            campaign_id=campaign_id,
        )

        return JsonResponse({
            "name": campaign.name,
            "campaign_id": campaign.campaign_id,
            "created_at": localtime(campaign.created_at).strftime("%d-%m-%Y"),
        })

    return JsonResponse({"error": "Invalid request"}, status=400)


def get_subscribers(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('query', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        subscribers = Subscriber.objects.all()

        if query:
            subscribers = subscribers.filter(
                Q(name__icontains=query) | 
                Q(email__icontains=query) | 
                Q(phone__icontains=query) | 
                Q(subscriber_id__icontains=query)
            )

        if start_date and end_date:
            subscribers = subscribers.filter(subscribed_at__date__range=[start_date, end_date])

        data = [
            {
                "subscriber_id": sub.subscriber_id,
                "name": sub.name,
                "email": sub.email,
                "phone": sub.phone,
                "subscribed_at": sub.subscribed_at.strftime("%d-%m-%Y"),
                "group": sub.group
            }
            for sub in subscribers
        ]

        return JsonResponse(data, safe=False)

    subscribers = Subscriber.objects.all()
    return render(request, "subscribers.html", {"subscribers": subscribers})


@csrf_exempt
def update_subscriber_group(request):
    if request.method == "POST":
        subscriber_id = request.POST.get("subscriber_id")
        group = request.POST.get("group")

        subscriber = Subscriber.objects.filter(subscriber_id=subscriber_id).first()
        if subscriber:
            subscriber.group = group
            subscriber.save()
            return JsonResponse({"message": "Group updated successfully"})
        else:
            return JsonResponse({"error": "Subscriber not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)

def get_campaigns(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('query', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        brand_id = request.GET.get('brand_id', '')

        campaigns = Campaign.objects.all().select_related('brand').prefetch_related('coupons')

        if brand_id:
            campaigns = campaigns.filter(brand__brand_id=brand_id)

        if query:
            campaigns = campaigns.filter(
                Q(name__icontains=query) | Q(campaign_id__icontains=query)
            )

        if start_date and end_date:
            campaigns = campaigns.filter(created_at__date__range=[start_date, end_date])

        data = [
            {
                "campaign_id": campaign.campaign_id,
                "name": campaign.name,
                "created_at": localtime(campaign.created_at).strftime("%d-%m-%Y"),
                "coupon_id": campaign.coupons.first().coupon_id if campaign.coupons.exists() else None,
                "brand": campaign.brand.name if campaign.brand else "N/A",
                "brand_id": campaign.brand.id if campaign.brand else None,
            }
            for campaign in campaigns
        ]

        return JsonResponse(data, safe=False)

    return JsonResponse({"error": "Invalid request."}, status=400)


def campaigns(request):
    query = request.GET.get("query", "").strip()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    brand_id = request.GET.get("brand_id")

    campaigns_data = Campaign.objects.select_related("brand").prefetch_related("coupons").all()

    if query:
        campaigns_data = campaigns_data.filter(
            Q(name__icontains=query) | Q(campaign_id__icontains=query)
        )

    if start_date and end_date:
        campaigns_data = campaigns_data.filter(created_at__date__range=[start_date, end_date])

    if brand_id:
        campaigns_data = campaigns_data.filter(brand__id=brand_id)

    campaigns_list = []
    for campaign in campaigns_data:
        coupon = campaign.coupons.first()
        newsletter = Newsletter.objects.filter(placeholders__icontains=campaign.campaign_id).first()

        campaigns_list.append({
            "campaign_id": campaign.campaign_id,
            "name": campaign.name,
            "created_at": campaign.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "brand_id": campaign.brand.brand_id,
            "brand_name": campaign.brand.name,
            "coupon_id": coupon.coupon_id if coupon else "N/A",
            "newsletter_id": newsletter.newsletter_id if newsletter else "N/A",
        })

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(campaigns_list, safe=False)

    return render(request, "campaigns.html", {"campaigns": campaigns_list})
    

def get_subscriber_base(campaign):
    newsletter = Newsletter.objects.filter(campaign=campaign).first()
    return newsletter.subscriber_base if newsletter else ""


def get_newsletters(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('query', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        brand_id = request.GET.get('brand_id', '')

        newsletters = Newsletter.objects.all()

        if query:
            newsletters = newsletters.filter(
                Q(name__icontains=query) | Q(newsletter_id__icontains=query)
            )

        if start_date and end_date:
            newsletters = newsletters.filter(created_at__date__range=[start_date, end_date])

        if brand_id:
            newsletters = newsletters.filter(brand__id=brand_id)

        data = [
            {
                "newsletter_id": newsletter.newsletter_id,
                "name": newsletter.name,
                "created_at": localtime(newsletter.created_at).strftime("%d-%m-%Y"),
                "brand": newsletter.brand.name if newsletter.brand else "N/A",
                "thumbnail": newsletter.thumbnail.url if newsletter.thumbnail else None,
                "subscriber_base": newsletter.subscriber_base,
                "campaign_ids": newsletter.get_placeholders(),
            }
            for newsletter in newsletters
        ]

        return JsonResponse(data, safe=False)

    brands = Brand.objects.all()
    newsletters = Newsletter.objects.all()
    return render(request, "newsletters.html", {"newsletters": newsletters, "brands": brands})

def newsletter_detail(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, newsletter_id=newsletter_id)
    
    campaign_ids = newsletter.get_placeholders()
    
    campaigns = Campaign.objects.filter(
        campaign_id__in=campaign_ids
    ).select_related('brand').order_by('created_at')
    
    campaign_data = []
    for campaign in campaigns:
        campaign_data.append({
            'campaign_id': campaign.campaign_id,
            'campaign_name': campaign.name,
            'brand_name': campaign.brand.name,
            'brand_id': campaign.brand.brand_id,
            'created_at': campaign.created_at,
        })
    
    context = {
        'newsletter': newsletter,
        'campaigns': campaign_data,
    }
    
    return render(request, 'newsletter_detail.html', context)

def get_coupons(request, newsletter_id):
    """Fetch and filter coupons dynamically via AJAX request."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('query', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        coupons = Coupon.objects.filter(newsletter__newsletter_id=newsletter_id)

        if query:
            coupons = coupons.filter(
                Q(coupon_id__icontains=query) | 
                Q(coupon_type__icontains=query) |
                Q(channel__icontains=query) |
                Q(bill_count__icontains=query)
            )

        if start_date and end_date:
            coupons = coupons.filter(created_at__date__range=[start_date, end_date])

        data = [
            {
                "coupon_id": coupon.coupon_id,
                "created_at": localtime(coupon.created_at).strftime("%d-%m-%Y"),
                "coupon_type": coupon.coupon_type,
                "bill_count": coupon.bill_count,
                "channel": coupon.channel,
                "newsletter_id": coupon.newsletter.newsletter_id if coupon.newsletter else "N/A",
            }
            for coupon in coupons
        ]

        return JsonResponse(data, safe=False)
    
def coupons(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('query', '').strip()
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        coupons = Coupon.objects.select_related("campaign__brand").all()

        if query:
            coupons = coupons.filter(
                Q(coupon_id__icontains=query) |
                Q(campaign__campaign_id__icontains=query) | 
                Q(campaign__brand__name__icontains=query) | 
                Q(coupon_type__icontains=query)
            )

        if start_date:
            coupons = coupons.filter(created_at__date__gte=start_date)
        if end_date:
            coupons = coupons.filter(created_at__date__lte=end_date)

        data = []
        for coupon in coupons:
            data.append({
                "coupon_id": coupon.coupon_id,
                "created_at": coupon.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "coupon_type": coupon.coupon_type,
                "bill_count": coupon.bill_count,
                "expiration_date": coupon.expiration_date.strftime("%Y-%m-%d") if coupon.expiration_date else None,
                "campaign_id": coupon.campaign.campaign_id if coupon.campaign else None,
                "brand_name": coupon.campaign.brand.name if coupon.campaign and coupon.campaign.brand else None
            })

        return JsonResponse(data, safe=False)

    coupons = Coupon.objects.select_related("campaign__brand").all()
    return render(request, "coupons.html", {"coupons": coupons})

def coupon_detail(request, coupon_id):
    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
    tracking_links = TrackingLink.objects.filter(coupon=coupon).select_related('subscriber')

    return render(request, "coupon_detail.html", {
        "coupon": coupon,
        "tracking_links": tracking_links
    })


def create_coupon(request, campaign_id):
    print(f"Campaign ID received: {campaign_id}")
    print(f"Request body: {request.body}")
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            coupon_id = data.get("coupon_id")
            coupon_type = data.get("coupon_type")
            discount_value = data.get("discount_value")
            bill_count = data.get("bill_count", 0)
            coupon_days = data.get("coupon_days", "All Days")
            expiration_date = data.get("expiration_date")
            buy_x = data.get("buy_x")
            get_y = data.get("get_y")

            if not coupon_id:
                return JsonResponse({"error": "Coupon ID is required"}, status=400)

            if coupon_type == "Percentage Discount" and discount_value is not None:
                try:
                    discount_value = float(discount_value)
                    if not (0 <= discount_value <= 100):
                        return JsonResponse({"error": "Percentage discount must be between 0 and 100"}, status=400)
                except ValueError:
                    return JsonResponse({"error": "Invalid discount value"}, status=400)
            
            campaign = get_object_or_404(Campaign, campaign_id=campaign_id) 

            if expiration_date:
                try:
                    expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d").date()
                except ValueError:
                    return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

            flat_discount = None
            percentage_discount = None

            if coupon_type == "Flat Discount" and discount_value is not None:
                flat_discount = discount_value
            elif coupon_type == "Percentage Discount" and discount_value is not None:
                percentage_discount = discount_value

            if coupon_type == "Buy X Get Y":
                buy_x = buy_x if buy_x is not None else None
                get_y = get_y if get_y is not None else None

            coupon = Coupon.objects.create(
                coupon_id=coupon_id,
                coupon_type=coupon_type,
                flat_discount=flat_discount,
                percentage_discount=percentage_discount,
                bill_count=bill_count,
                campaign=campaign,
                coupon_days=", ".join(coupon_days) if isinstance(coupon_days, list) else coupon_days,
                expiration_date=expiration_date,
                buy_x=buy_x,
                get_y=get_y,
            )

            return JsonResponse({"message": "Coupon created successfully!", "coupon_id": coupon.coupon_id}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)




def newsletter_list(request):
    newsletters = Newsletter.objects.all().order_by('-created_at')
    return render(request, 'newsletters.html', {'newsletters': newsletters})

@csrf_exempt
def create_newsletter(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        newsletter = Newsletter.objects.create(
            name=data['name'],
            newsletter_id=data['newsletter_id'],
        )
        
        return JsonResponse({
            'status': 'success',
            'newsletter_id': newsletter.newsletter_id
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)



@csrf_exempt
def process_template(request):
    if request.method == 'POST' and request.FILES.get('template'):
        try:
            template_file = request.FILES['template']
            template_content = template_file.read().decode('utf-8')
            
            return JsonResponse({
                'status': 'success',
                'template_content': template_content,
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@csrf_exempt
def generate_preview(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template_content = data['template_content']
            campaign_ids = data['campaign_ids']
            newsletter_id = data['newsletter_id']

            # Get the newsletter
            newsletter = get_object_or_404(Newsletter, newsletter_id=newsletter_id)

            # Process template for each campaign
            template = Template(template_content)
            context = {}

            for index, campaign_id in enumerate(campaign_ids, 1):
                campaign = get_object_or_404(Campaign, campaign_id=campaign_id)
                brand = campaign.brand
                coupon = Coupon.objects.filter(campaign=campaign).first()

                if coupon:
                    # Determine offer display text based on coupon type
                    offer_text = ""
                    coupon_category = "Special Offer"  # Default category

                    if coupon.coupon_type == "Buy X Get Y":
                        offer_text = f"Buy {coupon.buy_x} Get {coupon.get_y}"
                    elif coupon.coupon_type == "Percentage Discount":
                        offer_text = f"{coupon.percentage_discount}% OFF"
                        coupon_category = "Discount"
                    elif coupon.coupon_type == "Flat Discount":
                        offer_text = f"₹{coupon.flat_discount} OFF"
                        coupon_category = "Discount"
                    else:
                        # Handle Bundle Offer and Custom types
                        offer_text = coupon.custom_coupon_type if coupon.custom_coupon_type else coupon.coupon_type

                    # Format min purchase requirement
                    min_purchase = f"Min. Bill: ₹{coupon.bill_count}" if coupon.bill_count > 0 else "No minimum purchase required"

                    # Format applicable days
                    applicable_days = "Valid: " + (coupon.coupon_days if coupon.coupon_days != "All Days" 
                                                 else "Valid all days")

                    context.update({
                        f'campaign_id_{index}': campaign_id,
                        f'brand_name_{index}': brand.name,
                        f'coupon_type_{index}': coupon_category,
                        f'offer_{index}': offer_text,
                        f'min_purchase_{index}': min_purchase,
                        f'applicable_days_{index}': applicable_days,
                        f'expiry_date_{index}': coupon.expiration_date.strftime('%B %d, %Y') if coupon.expiration_date else 'No expiry date'
                    })

            # Add common fields
            context['subscriber_name'] = 'Preview User'
            context['unique_id'] = 'PREVIEW-ID'

            # Render template with all contexts
            rendered_html = template.render(Context(context))

            # Convert to PDF using pdfkit
            pdf = pdfkit.from_string(rendered_html, False)
            
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{newsletter_id}_preview.pdf"'
            return response

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def generate_unique_tracking_id(subscriber_id, campaign_id, coupon_id):
    """Generate a 12-digit unique tracking ID"""
    # Mix parts of each ID and add random characters
    base = f"{subscriber_id[:2]}{campaign_id[:2]}{coupon_id[:2]}"
    random_part = uuid.uuid4().hex[:6].upper()
    return f"{base}{random_part}"

@csrf_exempt
def generate_subscriber_pdfs(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template_content = data['template_content']
            campaign_ids = data['campaign_ids']
            newsletter_id = data['newsletter_id']
            subscriber_groups = data['subscriber_groups']

            newsletter = get_object_or_404(Newsletter, newsletter_id=newsletter_id)
            
            # Get all subscribers from selected groups
            subscribers = Subscriber.objects.filter(group__in=subscriber_groups)
            
            # Create PDF directory if it doesn't exist
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'newsletters', newsletter_id)
            os.makedirs(pdf_dir, exist_ok=True)

            generated_count = 0
            template = Template(template_content)

            for subscriber in subscribers:
                context = {}
                
                # Add subscriber-specific information
                context['subscriber_name'] = subscriber.name
                
                # Process each campaign
                for index, campaign_id in enumerate(campaign_ids, 1):
                    campaign = Campaign.objects.get(campaign_id=campaign_id)
                    brand = campaign.brand
                    coupon = campaign.coupons.first()

                    if coupon:
                        # Generate unique tracking ID and link
                        tracking_id = generate_unique_tracking_id(
                            subscriber.subscriber_id,
                            campaign_id,
                            coupon.coupon_id
                        )
                        
                        # Create tracking link
                        tracking_link = TrackingLink.objects.create(
                            coupon=coupon,
                            subscriber=subscriber,
                            unique_id=tracking_id,
                            tracking_link=f"{settings.REDEEM_LINK}/{tracking_id}"
                        )

                        # Add campaign-specific context
                        offer_text = ""
                        coupon_category = "Special Offer"

                        if coupon.coupon_type == "Buy X Get Y":
                            offer_text = f"Buy {coupon.buy_x} Get {coupon.get_y}"
                        elif coupon.coupon_type == "Percentage Discount":
                            offer_text = f"{coupon.percentage_discount}% OFF"
                            coupon_category = "Discount"
                        elif coupon.coupon_type == "Flat Discount":
                            offer_text = f"₹{coupon.flat_discount} OFF"
                            coupon_category = "Discount"
                        else:
                            offer_text = coupon.custom_coupon_type or coupon.coupon_type

                        context.update({
                            f'campaign_id_{index}': campaign_id,
                            f'brand_name_{index}': brand.name,
                            f'coupon_type_{index}': coupon_category,
                            f'offer_{index}': offer_text,
                            f'min_purchase_{index}': f"Min. Bill: ₹{coupon.bill_count}" if coupon.bill_count > 0 else "No minimum purchase required",
                            f'applicable_days_{index}': "Valid: " + coupon.coupon_days,
                            f'expiry_date_{index}': coupon.expiration_date.strftime('%B %d, %Y') if coupon.expiration_date else 'No expiry date',
                            f'tracking_link_{index}': tracking_link.tracking_link,
                            f'unique_id_{index}': tracking_id
                        })

                # Generate PDF for subscriber
                rendered_html = template.render(Context(context))
                pdf_filename = f"{subscriber.subscriber_id}_{newsletter_id}.pdf"
                pdf_path = os.path.join(pdf_dir, pdf_filename)
                
                pdf = pdfkit.from_string(rendered_html, pdf_path)
                generated_count += 1

            # Update newsletter status
            newsletter.is_frozen = True
            newsletter.placeholders = ','.join(campaign_ids)
            newsletter.save()

            return JsonResponse({
                'status': 'success',
                'generated_count': generated_count,
                'message': f'Successfully generated {generated_count} PDFs'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })


def redeem_coupon(request, tracking_id):
    # Get tracking link or return 404
    tracking_link = get_object_or_404(TrackingLink, unique_id=tracking_id)
    
    # Update clicked status if not already clicked
    if not tracking_link.clicked:
        tracking_link.clicked = True
        # tracking_link.clicked_at = timezone.now()
        tracking_link.save()

    # Get related objects
    subscriber = tracking_link.subscriber
    coupon = tracking_link.coupon

    # Generate QR code containing the tracking ID
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(tracking_id)
    qr.make(fit=True)

    # Create QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Convert QR code to base64 for embedding in HTML
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'subscriber': subscriber,
        'coupon': coupon,
        'qr_base64': qr_base64,
        'tracking_id': tracking_id
    }
    
    return render(request, 'redeem_coupon.html', context)

############################################## Brand Login

def generate_otp():
    return str(random.randint(100000, 999999))

# Option 1: Email OTP (Completely Free)
def send_email_otp(email, otp):
    try:
        subject = 'Your Login OTP'
        message = f'Your OTP for login is: {otp}'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        
        send_mail(subject, message, from_email, recipient_list)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    

def brand_login(request):
    if request.method == 'POST':
        brand_id = request.POST.get('brand_id')
        try:
            brand = Brand.objects.get(brand_id=brand_id)
            otp = generate_otp()
            cache.set(f'brand_otp_{brand_id}', otp, 300)
            
            if send_email_otp(brand.email, otp):
                request.session['brand_id'] = brand_id
                messages.success(request, 'OTP has been sent to your registered email.')
                return redirect('verify_otp')
            
            else:
                messages.error(request, 'Failed to send OTP. Please try again.')
        except Brand.DoesNotExist:
            messages.error(request, 'Invalid Brand ID.')
    
    return render(request, 'brands/brand_login.html')

def verify_otp(request):
    brand_id = request.session.get('brand_id')
    if not brand_id:
        return redirect('brand_login')
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = cache.get(f'brand_otp_{brand_id}')
        
        if stored_otp and entered_otp == stored_otp:
            cache.delete(f'brand_otp_{brand_id}')
            del request.session['brand_id']
            return redirect(f'/brand/dashboard/{brand_id}')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    return render(request, 'brands/verify_otp.html')


def brand_dashboard(request, brand_id):
    # Get the brand or return 404
    brand = get_object_or_404(Brand, brand_id=brand_id)
    
    context = {
        'brand': brand,
        # Add any additional context data you want to display
    }
    return render(request, 'brands/brand_dashboard.html', context)


###################### Coupon Validation

def validate_coupon(request, brand_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            scanned_qr_content = data.get("qr_content")  # Unique tracking ID
            bill_amount = data.get("bill_amount")  # Bill amount from the form

            tracking = get_object_or_404(TrackingLink, unique_id=scanned_qr_content)
            coupon = tracking.coupon
            subscriber = tracking.subscriber

            expected_brand_id = str(coupon.campaign.brand.brand_id).strip()
            actual_brand_id = str(brand_id).strip()

            if expected_brand_id != actual_brand_id:
                return JsonResponse({
                    "status": "error", 
                    "message": f"Unauthorized brand access. Expected {expected_brand_id}, got {actual_brand_id}"
                }, status=403)

            if coupon.is_expired():
                return JsonResponse({"status": "error", "message": "Coupon has expired."}, status=400)

            if not coupon.is_valid_today():
                return JsonResponse({"status": "error", "message": "Coupon is not valid today."}, status=400)

            if tracking.redeemed:
                return JsonResponse({"status": "error", "message": "Coupon already redeemed."}, status=400)

            # Check if bill amount is provided and valid
            if bill_amount is None or bill_amount == "":
                return JsonResponse({"status": "error", "message": "Bill amount is required."}, status=400)
            
            try:
                # Convert bill_amount to a float for comparison
                bill_amount_val = float(bill_amount)
            except ValueError:
                return JsonResponse({"status": "error", "message": "Invalid bill amount."}, status=400)

            # Compare bill amount with coupon.bill_count (assumed as minimum required amount)
            if bill_amount_val < coupon.bill_count:
                return JsonResponse({
                    "status": "error",
                    "message": f"Bill amount {bill_amount_val} is less than the required minimum of {coupon.bill_count}."
                }, status=400)

            # Save the bill amount if valid
            tracking.bill_amount = bill_amount_val
            tracking.redeemed = True
            tracking.redeemed_at = now()
            tracking.save()

            return JsonResponse({
                "status": "success",
                "message": f"Coupon successfully redeemed for {subscriber.name}.",
                "subscriber_id": subscriber.subscriber_id,
                "redeemed_at": tracking.redeemed_at.strftime("%Y-%m-%d %H:%M:%S"),
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


################# Analytics

def brand_analytics(request, brand_id):
    # Get the brand; ensure the user is logged in (or use a decorator if necessary)
    brand = get_object_or_404(Brand, brand_id=brand_id)
    
    # Get redeemed tracking links for the brand
    redemptions = TrackingLink.objects.filter(
        coupon__campaign__brand=brand, redeemed=True
    ).select_related('coupon', 'subscriber').order_by('-redeemed_at')
    
    # Prepare chart data: count redemptions per day
    redemptions_by_date = {}
    for redemption in redemptions:
        # Format the date (e.g., "2023-01-01")
        date_str = redemption.redeemed_at.strftime("%Y-%m-%d")
        redemptions_by_date[date_str] = redemptions_by_date.get(date_str, 0) + 1

    # Sort the dates chronologically and prepare labels and data arrays
    labels = sorted(redemptions_by_date.keys())
    data = [redemptions_by_date[label] for label in labels]
    redemptions_data = json.dumps({"labels": labels, "data": data})
    
    context = {
        'brand': brand,
        'redemptions': redemptions,
        'redemptions_data': redemptions_data,
    }
    return render(request, 'brands/analytics.html', context)

