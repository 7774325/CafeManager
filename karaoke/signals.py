# karaoke/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .models import Order, OrderItem # Import the models we want to track

@receiver(post_save, sender=Order)
@receiver(post_save, sender=OrderItem)
def order_update_signal(sender, instance, **kwargs):
    """
    Triggers a WebSocket broadcast whenever an Order or OrderItem is saved/updated.
    """
    # Determine the booking and room ID from the instance
    if sender == Order:
        booking = instance.booking
    elif sender == OrderItem:
        if not instance.order:
             return
        booking = instance.order.booking
    else:
        return

    room_id = booking.room.id
    room_group_name = f'karaoke_{room_id}'
    
    channel_layer = get_channel_layer()

    payload = {
        'type': 'status_update', 
        'data': {
            'type': 'order_update',
            'room_id': room_id,
            'status': instance.status if sender == Order else 'item_added',
            'order_id': instance.id,
            'summary': f"Update for Room {booking.room.name}"
        }
    }
    
    # Send the event to the dedicated room group
    async_to_sync(channel_layer.group_send)(
        room_group_name,
        payload
    )