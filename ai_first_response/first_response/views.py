import os
import json
import time
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from .models import EmergencyCategory, ReceivedMessage
from .responders import classify_message
from .disaster_feeds import recent_quakes, gdacs_events
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncDay, TruncHour
from datetime import datetime, timedelta

def dashboard(request):
    """Render the emergency chat dashboard"""
    # Get active emergency categories ordered by display order
    categories = EmergencyCategory.objects.filter(is_active=True).order_by('order', 'title')
    context = {
        'emergency_categories': categories
    }
    return render(request, 'dashboard.html', context)

@csrf_exempt
def first_response(request):
    """Handle emergency classification API endpoint"""
    if request.method != 'POST':
        return HttpResponseBadRequest(json.dumps({"error": "POST required"}), content_type="application/json")

    # Check Content-Type (optional but helpful for debugging)
    content_type = request.META.get('CONTENT_TYPE', '')
    print(f"Content-Type: {content_type}")  # Debug log

    start_time = time.time()
    received_message = None
    
    try:
        # Check if request body is empty
        if not request.body:
            return HttpResponseBadRequest(json.dumps({"error": "Empty request body"}), content_type="application/json")
        
        # Decode the request body
        body_str = request.body.decode('utf-8')
        print(f"Raw request body: {body_str}")  # Debug log
        
        if not body_str.strip():
            return HttpResponseBadRequest(json.dumps({"error": "Empty JSON payload"}), content_type="application/json")
        
        payload = json.loads(body_str)
        print(f"Parsed payload: {payload}")  # Debug log
        
        msg = payload.get('message')
        lat = payload.get('lat')
        lon = payload.get('lon')
        
        # Validate required fields
        if not msg:
            return HttpResponseBadRequest(json.dumps({"error": "Missing 'message' field"}), content_type="application/json")
        if lat is None:
            return HttpResponseBadRequest(json.dumps({"error": "Missing 'lat' field"}), content_type="application/json")
        if lon is None:
            return HttpResponseBadRequest(json.dumps({"error": "Missing 'lon' field"}), content_type="application/json")
        
        # Convert to float
        lat = float(lat)
        lon = float(lon)
        
        # Create ReceivedMessage instance
        received_message = ReceivedMessage.objects.create(
            user_message=msg,
            user_latitude=lat,
            user_longitude=lon,
            user_ip=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_key=request.session.session_key or '',
        )
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON format: {str(e)}"
        print(f"JSON decode error: {error_msg}")  # Debug log
        if received_message:
            received_message.has_error = True
            received_message.error_message = error_msg
            received_message.save()
        return HttpResponseBadRequest(json.dumps({"error": error_msg}), content_type="application/json")
    except ValueError as e:
        error_msg = f"Invalid coordinate values: {str(e)}"
        print(f"Value error: {error_msg}")  # Debug log
        if received_message:
            received_message.has_error = True
            received_message.error_message = error_msg
            received_message.save()
        return HttpResponseBadRequest(json.dumps({"error": error_msg}), content_type="application/json")
    except Exception as e:
        error_msg = f"Input validation error: {str(e)}"
        print(f"General error: {error_msg}")  # Debug log
        if received_message:
            received_message.has_error = True
            received_message.error_message = error_msg
            received_message.save()
        return HttpResponseBadRequest(json.dumps({"error": error_msg}), content_type="application/json")

    try:
        # Optionally fetch external feed based on initial message classification
        feed_snippet = ''
        # classify raw message first
        print(msg)
        classification = classify_message(msg, lat, lon)
        print(classification)
        category = classification.get('category', '').upper()

        # if natural disaster, append feed snippet
        if category in ['EARTHQUAKE', 'FLOOD', 'VOLCANO']:
            try:
                quakes = recent_quakes(lat, lon)
                if quakes:
                    latest = quakes[0]['properties']
                    feed_snippet = f"M{latest['mag']} earthquake {latest['place']} at {latest['time']} UTC"
                else:
                    gd = gdacs_events(lat, lon)
                    # Safely handle GDACS data
                    if gd and len(gd) > 0:
                        # Convert to string representation instead of JSON
                        feed_snippet = str(gd[0]) if gd[0] else ''
                    else:
                        feed_snippet = ''
                # re-classify with feed context
                classification = classify_message(msg, lat, lon, feed_snippet)
                print(f"Re-classified with feed: {classification}")
            except Exception as feed_error:
                print(f"Error fetching external feeds: {feed_error}")
                feed_snippet = ''
                # Continue with original classification

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Safely extract and validate data
        category = classification.get('category', 'Unknown')
        severity = classification.get('severity', 'INFO') 
        instructions = classification.get('instructions', [])
        
        # Ensure instructions is a list
        if not isinstance(instructions, list):
            if isinstance(instructions, str):
                instructions = [instructions]
            else:
                instructions = []
        
        print(f"Final classification - Category: {category}, Severity: {severity}, Instructions: {instructions}")
        
        # Update ReceivedMessage with results
        try:
            received_message.ai_category = category
            received_message.ai_severity = severity
            received_message.ai_instructions = instructions
            received_message.external_feed = feed_snippet
            received_message.response_time_ms = processing_time_ms
            received_message.processed_at = timezone.now()
            received_message.save()
            print("ReceivedMessage saved successfully")
        except Exception as save_error:
            print(f"Error saving ReceivedMessage: {save_error}")
            # Continue with response even if save fails

        # Prepare response data with safe defaults
        response_data = {
            "category": category,
            "severity": severity,
            "instructions": instructions,
            "feed": feed_snippet
        }
        
        print(f"Sending response: {response_data}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        # Log error to ReceivedMessage
        if received_message:
            received_message.has_error = True
            received_message.error_message = str(e)
            received_message.processed_at = timezone.now()
            received_message.save()
        
        return JsonResponse({
            "error": f"Processing error: {str(e)}"
        }, status=500)

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with statistics and charts"""
    # Get date range for filtering (last 30 days by default)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Basic statistics
    total_messages = ReceivedMessage.objects.count()
    messages_last_30_days = ReceivedMessage.objects.filter(
        received_at__gte=start_date
    ).count()
    
    critical_messages = ReceivedMessage.objects.filter(
        ai_severity__in=['CRIT', 'HIGH']
    ).count()
    
    avg_response_time = ReceivedMessage.objects.filter(
        response_time_ms__isnull=False
    ).aggregate(avg_time=Avg('response_time_ms'))['avg_time']
    
    # Messages by severity
    severity_stats = ReceivedMessage.objects.values('ai_severity').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Messages by category
    category_stats = ReceivedMessage.objects.values('ai_category').annotate(
        count=Count('id')
    ).order_by('-count')[:10]  # Top 10 categories
    
    # Messages by day (last 30 days)
    daily_stats = ReceivedMessage.objects.filter(
        received_at__gte=start_date
    ).annotate(
        day=TruncDay('received_at')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Messages by hour (last 24 hours)
    hourly_stats = ReceivedMessage.objects.filter(
        received_at__gte=end_date - timedelta(hours=24)
    ).annotate(
        hour=TruncHour('received_at')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Recent critical messages
    recent_critical = ReceivedMessage.objects.filter(
        ai_severity__in=['CRIT', 'HIGH']
    ).order_by('-received_at')[:10]
    
    # Error rate
    total_processed = ReceivedMessage.objects.filter(processed_at__isnull=False).count()
    error_count = ReceivedMessage.objects.filter(has_error=True).count()
    error_rate = (error_count / total_processed * 100) if total_processed > 0 else 0
    
    context = {
        'total_messages': total_messages,
        'messages_last_30_days': messages_last_30_days,
        'critical_messages': critical_messages,
        'avg_response_time': avg_response_time,
        'error_rate': error_rate,
        'severity_stats': severity_stats,
        'category_stats': category_stats,
        'daily_stats': daily_stats,
        'hourly_stats': hourly_stats,
        'recent_critical': recent_critical,
    }
    
    return render(request, 'admin/dashboard.html', context)

def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
