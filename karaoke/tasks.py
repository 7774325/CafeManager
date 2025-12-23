from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def trigger_new_order_alert(order):
    """
    Sends a real-time message to the 'order_monitor' group via WebSockets.
    """
    channel_layer = get_channel_layer()
    
    # We build a list of items to show on the monitor card
    items = []
    
    # We use 'order.items.all()' because 'items' is the related_name in your OrderItem model
    for oi in order.items.all():
        items.append({
            # FIX: We use 'oi.item.name' because the field in your model is named 'item'
            'name': oi.item.name,
            'quantity': oi.quantity,
        })

    # This sends the data to the staff_monitor.html JavaScript
    async_to_sync(channel_layer.group_send)(
        'order_monitor',
        {
            'type': 'order_alert',
            'order_id': order.id,
            'room_name': order.booking.room.name,
            'items': items,
            'created_at': order.created_at.strftime('%H:%M'),
        }
    )