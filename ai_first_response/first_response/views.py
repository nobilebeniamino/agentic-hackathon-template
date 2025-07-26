import os
import json
import time
import tempfile
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from django.utils.translation import get_language
from django.core.files.storage import default_storage
from .models import EmergencyCategory, ReceivedMessage
from .responders import classify_message
from .disaster_feeds import recent_quakes, gdacs_events, get_cache_stats, cleanup_expired_cache, clear_cache
from .audio_utils import speech_to_text, text_to_speech, convert_audio_format, cleanup_audio_file
from .agentic_system import AgenticEmergencySystem
from .metrics import agentic_metrics
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncDay, TruncHour
from datetime import datetime, timedelta
import math

def dashboard(request):
    """Render the emergency chat dashboard"""
    # Get current language
    current_language = get_language()
    
    # Filter categories based on language
    # English categories have order 1-99, Italian categories have order 100+
    if current_language == 'it':
        categories = EmergencyCategory.objects.filter(is_active=True, order__gte=100).order_by('order', 'title')
    else:
        categories = EmergencyCategory.objects.filter(is_active=True, order__lt=100).order_by('order', 'title')
    
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
        frontend_lang = payload.get('language')  # Language from frontend
        
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
        
        # Detect user's preferred language from multiple sources
        user_lang = None
        
        # Priority 1: Language from frontend (most reliable)
        if frontend_lang:
            user_lang = frontend_lang
            print(f"Using frontend language: {user_lang}")
        
        # Priority 2: Try to get language from Django session
        elif hasattr(request, 'session') and 'django_language' in request.session:
            user_lang = request.session['django_language']
            print(f"Using session language: {user_lang}")
        
        # Priority 3: Fallback to checking cookies
        elif 'django_language' in request.COOKIES:
            user_lang = request.COOKIES['django_language']
            print(f"Using cookie language: {user_lang}")
        
        # Priority 4: Fallback to Accept-Language header
        else:
            accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            if 'it' in accept_lang.lower():
                user_lang = 'it'
            else:
                user_lang = 'en'
            print(f"Using Accept-Language header: {user_lang}")
        
        print(f"Final detected user language: {user_lang}")
        
        # **AGENTIC SYSTEM INTEGRATION**
        # Initialize the agentic emergency response system
        agentic_system = AgenticEmergencySystem()
        
        # Process emergency with full agentic architecture
        print(f"Processing with agentic system: {msg}")
        agentic_response = agentic_system.process_emergency(
            message=msg,
            latitude=lat,
            longitude=lon,
            user_language=user_lang
        )
        print(f"Agentic response: {agentic_response}")
        
        # Extract data for backward compatibility with existing frontend
        category = agentic_response.get('category', 'Unknown')
        severity = agentic_response.get('severity', 'INFO')
        instructions = agentic_response.get('enhanced_instructions', 
                                          agentic_response.get('instructions', []))
        
        # Get feed snippet from agentic context
        feed_snippet = ''
        if 'contextual_awareness' in agentic_response:
            if agentic_response['contextual_awareness'].get('disaster_feed_active'):
                feed_snippet = "Disaster feed data analyzed by agentic system"
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Ensure instructions is a list
        if not isinstance(instructions, list):
            if isinstance(instructions, str):
                instructions = [instructions]
            else:
                instructions = []
        
        print(f"Final classification - Category: {category}, Severity: {severity}, Instructions: {instructions}")
        
        # Update ReceivedMessage with agentic results
        try:
            received_message.ai_category = category
            received_message.ai_severity = severity
            received_message.ai_instructions = instructions
            received_message.external_feed = feed_snippet
            received_message.response_time_ms = processing_time_ms
            received_message.processed_at = timezone.now()
            
            # Store agentic system metadata
            received_message.ai_model = 'agentic-gemini-1.5-flash'
            
            received_message.save()
            print("ReceivedMessage saved successfully with agentic data")
        except Exception as save_error:
            print(f"Error saving ReceivedMessage: {save_error}")
            # Continue with response even if save fails

        # Prepare enhanced response data with agentic insights
        # Ensure instructions are JSON serializable and limited in length
        if isinstance(instructions, list):
            # Limit to 8 instructions max and ensure they're strings
            instructions = [str(instr)[:200] for instr in instructions[:8]]  # Truncate long instructions
        
        response_data = {
            "category": category,
            "severity": severity,
            "instructions": instructions,
            "feed": feed_snippet,
            # Additional agentic data for frontend (optional)
            "agentic_insights": {
                "system_enabled": True,
                "plan_quality": agentic_response.get('confidence_indicators', {}).get('plan_completeness', 'unknown'),
                "historical_context": len(agentic_response.get('contextual_awareness', {}).get('historical_incidents', [])) if isinstance(agentic_response.get('contextual_awareness', {}).get('historical_incidents'), list) else 0,
                "monitoring_tasks": len(agentic_response.get('monitoring_recommendations', [])) if isinstance(agentic_response.get('monitoring_recommendations'), list) else 0,
                "resources_identified": len(agentic_response.get('resource_requirements', [])) if isinstance(agentic_response.get('resource_requirements'), list) else 0
            }
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
    
    # Messages by severity - normalize to uppercase for consistency
    from django.db.models import Case, When, Value, CharField
    severity_stats = ReceivedMessage.objects.annotate(
        normalized_severity=Case(
            When(ai_severity__iexact='CRIT', then=Value('CRIT')),
            When(ai_severity__iexact='HIGH', then=Value('HIGH')),
            When(ai_severity__iexact='MED', then=Value('MED')),
            When(ai_severity__iexact='LOW', then=Value('LOW')),
            When(ai_severity__iexact='INFO', then=Value('INFO')),
            default=Value('UNKNOWN'),
            output_field=CharField()
        )
    ).values('normalized_severity').annotate(
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
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    
    return render(request, 'admin/dashboard.html', context)


@csrf_exempt
def voice_message(request):
    """Handle voice message processing"""
    if request.method != 'POST':
        return HttpResponseBadRequest(json.dumps({"error": "POST required"}), content_type="application/json")
    
    start_time = time.time()
    received_message = None
    temp_files = []  # Track temporary files for cleanup
    
    try:
        # Check if audio file is provided
        if 'audio' not in request.FILES:
            return JsonResponse({
                "success": False,
                "error": "No audio file provided"
            }, status=400)
        
        audio_file = request.FILES['audio']
        
        # Get additional parameters
        language = request.POST.get('language', 'en')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        client_ip = get_client_ip(request)
        
        print(f"Processing voice message - Language: {language}, File: {audio_file.name}")
        
        # Save uploaded audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            for chunk in audio_file.chunks():
                tmp_file.write(chunk)
            temp_audio_path = tmp_file.name
            temp_files.append(temp_audio_path)
        
        # Convert audio to WAV format for better compatibility
        wav_path = convert_audio_format(temp_audio_path, 'wav')
        if wav_path:
            temp_files.append(wav_path)
            audio_path_to_use = wav_path
        else:
            audio_path_to_use = temp_audio_path
        
        # Convert speech to text
        stt_result = speech_to_text(audio_path_to_use, language)
        
        if not stt_result['success']:
            return JsonResponse({
                "success": False,
                "error": f"Speech recognition failed: {stt_result['error']}"
            }, status=400)
        
        message_text = stt_result['text']
        print(f"Transcribed text: {message_text}")
        
        # Process the message through the normal classification pipeline
        lat = float(latitude) if latitude else 45.0703  # Default to Turin
        lon = float(longitude) if longitude else 7.6869
        classification_result = classify_message(message_text, lat, lon, user_lang=language)
        
        # Generate TTS response
        instructions = classification_result.get('instructions', ['Unable to process your request.'])
        if isinstance(instructions, list):
            response_text = ' '.join(instructions)
        else:
            response_text = str(instructions)
        
        print(f"Generating TTS for text: {response_text[:100]}...")
        tts_result = text_to_speech(response_text, language)
        print(f"TTS result: {tts_result}")
        
        # Create received message record
        received_message = ReceivedMessage.objects.create(
            user_message=message_text,
            message_text=message_text,
            message_type='voice',
            language=language,
            user_latitude=lat,
            user_longitude=lon,
            user_agent=user_agent,
            user_ip=client_ip,
            session_key='',
            ai_category=classification_result.get('category', 'general'),
            ai_severity=classification_result.get('severity', 'INFO'),
            ai_instructions=classification_result.get('instructions', []),
            response_time_ms=int((time.time() - start_time) * 1000),
            processed_at=timezone.now()
        )
        
        # Prepare response
        response_data = {
            "success": True,
            "message_id": str(received_message.id),
            "transcribed_text": message_text,
            "classification": classification_result.get('severity', 'unknown'),
            "category": classification_result.get('category', 'general'),
            "instructions": response_text,
            "response_time_ms": int((time.time() - start_time) * 1000),
            "audio_url": tts_result.get('audio_url') if tts_result.get('success') else None,
            "tts_success": tts_result.get('success', False),
            "tts_error": tts_result.get('error') if not tts_result.get('success') else None
        }
        
        # Add disaster feeds if coordinates provided
        if latitude and longitude:
            try:
                # Get earthquake data
                quakes = recent_quakes(lat, lon, radius_km=300, min_mag=3.0, minutes=60)
                
                # Get GDACS data
                gdacs = gdacs_events(lat, lon, radius_km=500)
                
                response_data["disaster_feeds"] = {
                    "earthquakes": quakes[:3],  # Limit to 3 most recent
                    "gdacs_events": gdacs[:3],  # Limit to 3 most relevant
                    "location": {"latitude": lat, "longitude": lon}
                }
                
                print(f"Found {len(quakes)} earthquakes and {len(gdacs)} GDACS events near {lat}, {lon}")
                
            except Exception as e:
                print(f"Error fetching disaster feeds: {e}")
                response_data["disaster_feeds"] = {"error": str(e)}
        
        return JsonResponse(response_data)
        
    except Exception as e:
        error_msg = f"Voice processing error: {str(e)}"
        print(error_msg)
        
        # Log error in database if possible
        if received_message:
            received_message.has_error = True
            received_message.error_message = error_msg
            received_message.save()
        
        return JsonResponse({
            "success": False,
            "error": error_msg,
            "response_time_ms": int((time.time() - start_time) * 1000)
        }, status=500)
    
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            cleanup_audio_file(temp_file)

def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on earth (in km)"""
    R = 6371  # Earth's radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))


@staff_member_required
def emergency_alerts(request):
    """API endpoint to check for emergency clusters and return alerts"""
    try:
        # Get time window for checking clusters
        time_window_hours = getattr(settings, 'EMERGENCY_CLUSTER_TIME_WINDOW_HOURS', 24)
        since_time = timezone.now() - timedelta(hours=time_window_hours)
        
        # Get recent messages within time window
        recent_messages = ReceivedMessage.objects.filter(
            processed_at__gte=since_time,
            user_latitude__isnull=False,
            user_longitude__isnull=False,
            ai_category__isnull=False
        ).exclude(ai_category='Unknown').order_by('-processed_at')
        
        # Group messages by category
        category_groups = {}
        for message in recent_messages:
            category = message.ai_category
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(message)
        
        alerts = []
        radius_km = getattr(settings, 'EMERGENCY_CLUSTER_RADIUS_KM', 50)
        min_count = getattr(settings, 'EMERGENCY_CLUSTER_MIN_COUNT', 10)
        
        # Check each category for clusters
        for category, messages in category_groups.items():
            if len(messages) < min_count:
                continue
                
            # Check for geographical clusters
            clusters = find_clusters(messages, radius_km, min_count)
            
            for cluster in clusters:
                # Calculate severity distribution
                severity_counts = {}
                for msg in cluster['messages']:
                    severity = msg.ai_severity or 'UNKNOWN'
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                # Determine dominant severity
                dominant_severity = max(severity_counts.items(), key=lambda x: x[1])[0] if severity_counts else 'UNKNOWN'
                
                alerts.append({
                    'id': f"{category}_{cluster['center_lat']:.4f}_{cluster['center_lon']:.4f}",
                    'category': category,
                    'count': cluster['count'],
                    'center_lat': cluster['center_lat'],
                    'center_lon': cluster['center_lon'],
                    'radius_km': radius_km,
                    'dominant_severity': dominant_severity,
                    'severity_distribution': severity_counts,
                    'first_occurrence': cluster['first_occurrence'].isoformat(),
                    'last_occurrence': cluster['last_occurrence'].isoformat(),
                    'time_span_hours': round((cluster['last_occurrence'] - cluster['first_occurrence']).total_seconds() / 3600, 1)
                })
        
        # Sort alerts by count (highest first)
        alerts.sort(key=lambda x: x['count'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'alerts': alerts,
            'total_alerts': len(alerts),
            'checked_time_window_hours': time_window_hours,
            'cluster_settings': {
                'radius_km': radius_km,
                'min_count': min_count
            }
        })
        
    except Exception as e:
        print(f"Error generating emergency alerts: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'alerts': []
        }, status=500)


def find_clusters(messages, radius_km, min_count):
    """Find geographical clusters of messages"""
    clusters = []
    processed_indices = set()
    
    for i, center_msg in enumerate(messages):
        if i in processed_indices:
            continue
            
        # Find all messages within radius of this message
        cluster_messages = []
        cluster_indices = []
        
        for j, msg in enumerate(messages):
            if j in processed_indices:
                continue
                
            distance = _haversine_distance(
                center_msg.user_latitude, center_msg.user_longitude,
                msg.user_latitude, msg.user_longitude
            )
            
            if distance <= radius_km:
                cluster_messages.append(msg)
                cluster_indices.append(j)
        
        # If cluster is large enough, add it
        if len(cluster_messages) >= min_count:
            # Calculate cluster center (centroid)
            center_lat = sum(msg.user_latitude for msg in cluster_messages) / len(cluster_messages)
            center_lon = sum(msg.user_longitude for msg in cluster_messages) / len(cluster_messages)
            
            # Get time range
            times = [msg.processed_at for msg in cluster_messages]
            first_occurrence = min(times)
            last_occurrence = max(times)
            
            clusters.append({
                'messages': cluster_messages,
                'count': len(cluster_messages),
                'center_lat': center_lat,
                'center_lon': center_lon,
                'first_occurrence': first_occurrence,
                'last_occurrence': last_occurrence
            })
            
            # Mark these messages as processed
            processed_indices.update(cluster_indices)
    
    return clusters

@csrf_exempt
def text_to_speech_api(request):
    """Convert text to speech for dashboard responses"""
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=400)
    
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        language = data.get('language', 'en')
        
        if not text:
            return JsonResponse({"error": "Text is required"}, status=400)
        
        # Clean the text (remove HTML tags and excessive whitespace)
        import re
        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        if not text:
            return JsonResponse({"error": "No valid text after cleaning"}, status=400)
        
        print(f"TTS API: Converting text to speech: '{text[:100]}...' in language: {language}")
        
        # Generate audio
        audio_result = text_to_speech(text, language)
        
        if audio_result['success'] and audio_result['audio_url']:
            print(f"TTS API: Audio generated successfully: {audio_result['audio_url']}")
            
            return JsonResponse({
                "success": True,
                "audio_url": audio_result['audio_url'],
                "text": text[:100] + "..." if len(text) > 100 else text
            })
        else:
            print(f"TTS API: Failed to generate audio: {audio_result.get('error', 'Unknown error')}")
            return JsonResponse({
                "success": False,
                "error": audio_result.get('error', 'Failed to generate audio')
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        print(f"TTS API Error: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

@csrf_exempt
def agentic_system_status(request):
    """API endpoint to get agentic system status and capabilities"""
    if request.method != 'GET':
        return HttpResponseBadRequest(json.dumps({"error": "GET required"}), content_type="application/json")
    
    try:
        # Initialize agentic system
        agentic_system = AgenticEmergencySystem()
        
        # Get system status
        status = agentic_system.get_system_status()
        
        # Get real metrics from the metrics system
        metrics = agentic_metrics.get_all_metrics()
        planner_metrics = metrics.get('planner', {})
        executor_metrics = metrics.get('executor', {})
        memory_metrics = metrics.get('memory', {})
        
        # Add runtime statistics with error handling
        try:
            recent_messages = ReceivedMessage.objects.filter(
                processed_at__gte=timezone.now() - timedelta(hours=24)
            )
            
            runtime_stats = {
                'messages_24h': recent_messages.count(),
                'avg_response_time_ms': recent_messages.aggregate(
                    avg_time=Avg('response_time_ms')
                )['avg_time'] or 0,
                'categories_processed': recent_messages.values('ai_category').distinct().count(),
                'severities_handled': recent_messages.values('ai_severity').distinct().count()
            }
            
        except Exception as e:
            print(f"Error calculating runtime stats: {e}")
            runtime_stats = {
                'messages_24h': 0,
                'avg_response_time_ms': 0,
                'categories_processed': 0,
                'severities_handled': 0
            }
        
        # Format response for frontend compatibility
        components = status.get('components', {})
        
        # Use real metrics from the metrics system
        plans_generated = planner_metrics.get('plans_generated', 0)
        plan_completeness = planner_metrics.get('completeness', 0)
        actions_executed = executor_metrics.get('actions_executed', 0) 
        execution_success = executor_metrics.get('success_rate', 0)
        stored_patterns = memory_metrics.get('patterns_stored', 0)
        context_hits = memory_metrics.get('context_hits', 0)
        
        response_data = {
            "status": "success",
            "planner_status": "Active" if components.get('planner', {}).get('status') == 'active' else "Inactive",
            "executor_status": "Active" if components.get('executor', {}).get('status') == 'active' else "Inactive", 
            "memory_status": "Active" if components.get('memory', {}).get('status') == 'active' else "Inactive",
            "plans_generated": plans_generated,
            "plan_completeness": plan_completeness,
            "actions_executed": actions_executed, 
            "execution_success": execution_success,
            "stored_patterns": stored_patterns,
            "context_hits": context_hits,
            "messages_24h": runtime_stats['messages_24h'],
            "avg_response_time": f"{runtime_stats['avg_response_time_ms']:.0f}",
            "categories_processed": runtime_stats['categories_processed'],
            "system_version": status.get('version', '1.0-agentic'),
            "capabilities": status.get('capabilities', [])
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"Agentic system status error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "status": "error",
            "error": f"System status error: {str(e)}"
        }, status=500)

@csrf_exempt 
def agentic_memory_insights(request):
    """API endpoint to get memory insights and situational awareness"""
    if request.method != 'POST':
        return HttpResponseBadRequest(json.dumps({"error": "POST required"}), content_type="application/json")
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
        lat = float(payload.get('lat', 0))
        lon = float(payload.get('lon', 0))
        
        # Initialize memory system
        from .memory import EmergencyMemory
        memory = EmergencyMemory()
        
        # Get situational awareness
        awareness = memory.get_situational_awareness(
            location={'lat': lat, 'lon': lon}
        )
        
        # Get interaction history
        history = memory.get_interaction_history(limit=10)
        
        response_data = {
            'situational_awareness': awareness,
            'recent_interactions': history,
            'memory_capabilities': [
                'location_pattern_recognition',
                'category_based_learning', 
                'effectiveness_tracking',
                'contextual_recall',
                'trend_analysis'
            ]
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            "error": f"Memory insights error: {str(e)}"
        }, status=500)


@staff_member_required
def disaster_feeds_cache_stats(request):
    """API endpoint to get disaster feeds cache statistics"""
    try:
        from .disaster_feeds import get_cache_stats, cleanup_expired_cache
        
        # Cleanup expired entries first
        cleanup_expired_cache()
        
        # Get cache statistics
        cache_stats = get_cache_stats()
        
        # Calculate cache efficiency
        total_entries = cache_stats['total_entries']
        cache_efficiency = 0
        if total_entries > 0:
            cache_efficiency = (cache_stats['valid_entries'] / total_entries) * 100
        
        response_data = {
            "status": "success",
            "cache_stats": {
                "total_entries": total_entries,
                "valid_entries": cache_stats['valid_entries'],
                "expired_entries": cache_stats['expired_entries'],
                "cache_size_kb": round(cache_stats['cache_size_bytes'] / 1024, 2),
                "cache_efficiency_pct": round(cache_efficiency, 1),
                "usgs_ttl_minutes": 5,  # USGS_CACHE_TTL / 60
                "gdacs_ttl_minutes": 15  # GDACS_CACHE_TTL / 60
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            "error": f"Cache stats error: {str(e)}"
        }, status=500)


@staff_member_required
def clear_disaster_feeds_cache(request):
    """API endpoint to clear disaster feeds cache"""
    if request.method != 'POST':
        return JsonResponse({"error": "POST method required"}, status=405)
    
    try:
        from .disaster_feeds import clear_cache
        
        clear_cache()
        
        return JsonResponse({
            "status": "success",
            "message": "Disaster feeds cache cleared successfully"
        })
        
    except Exception as e:
        return JsonResponse({
            "error": f"Cache clear error: {str(e)}"
        }, status=500)

@staff_member_required
def system_dashboard(request):
    """System dashboard for agentic AI status and cache monitoring"""
    context = {
        'page_title': 'System Dashboard - Agentic AI & Cache Monitoring'
    }
    return render(request, 'admin/system_dashboard.html', context)

@csrf_exempt 
def reset_agentic_metrics(request):
    """API endpoint to reset agentic metrics (admin only)"""
    if request.method != 'POST':
        return HttpResponseBadRequest(json.dumps({"error": "POST required"}), content_type="application/json")
    
    try:
        # Reset all metrics
        agentic_metrics.reset_metrics()
        
        return JsonResponse({
            "status": "success",
            "message": "Agentic metrics have been reset"
        })
        
    except Exception as e:
        print(f"Reset metrics error: {e}")
        return JsonResponse({
            "status": "error",
            "error": f"Failed to reset metrics: {str(e)}"
        }, status=500)
