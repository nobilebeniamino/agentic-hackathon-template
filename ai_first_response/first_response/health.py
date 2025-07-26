from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for Cloud Run"""
    try:
        # Basic health checks
        from django.db import connection
        from django.core.cache import cache
        
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            "status": "healthy",
            "service": "ai-first-response",
            "database": "connected"
        })
    except Exception as e:
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status=503)

@csrf_exempt 
@require_http_methods(["GET"])
def readiness_check(request):
    """Readiness check endpoint"""
    return JsonResponse({
        "status": "ready",
        "service": "ai-first-response"
    })
