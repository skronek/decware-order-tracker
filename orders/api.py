import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
from datetime import datetime
from .models import OrderRecord, StatusHistory
from .scraper import DecwareOrderScraper

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def bulk_update_orders(request):
    """
    API endpoint to receive order data from the local update script.
    
    Expected JSON payload:
    {
        "orders": [
            {
                "customer_name": "...",
                "origin": "...",
                "quantity": "...",
                "model": "...",
                "base": "...",
                "volts": "...",
                "options": "...",
                "status": "...",
                "order_date": "..."
            },
            ...
        ],
        "source": "local_update_script",
        "timestamp": "2025-04-16T22:26:38-04:00"
    }
    """
    try:
        # Parse the JSON payload
        data = json.loads(request.body)
        
        # Validate the payload
        if 'orders' not in data or not isinstance(data['orders'], list):
            return JsonResponse({'error': 'Invalid payload format'}, status=400)
        
        # Log the request
        source = data.get('source', 'unknown')
        timestamp = data.get('timestamp', timezone.now().isoformat())
        logger.info(f"Received bulk update request from {source} at {timestamp}")
        logger.info(f"Received {len(data['orders'])} orders")
        
        # Process the orders
        scraper = DecwareOrderScraper()
        updated, created = scraper.update_orders(data['orders'])
        
        # Return the result
        return JsonResponse({
            'status': 'success',
            'updated': updated,
            'created': created,
            'total': updated + created
        })
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        
    except Exception as e:
        logger.error(f"Error processing bulk update: {e}")
        return JsonResponse({'error': str(e)}, status=500)
