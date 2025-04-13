from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    verbose_name = 'Order Tracking'

    def ready(self):
        # Import signals when the app is ready
        import orders.signals  # We'll create this later when implementing status history tracking
