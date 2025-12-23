# CafeManager

## Overview
CafeManager is a Django-based point-of-sale and cafe management system with karaoke room management features. It includes:
- Core POS functionality (sales, inventory, products)
- Karaoke room session management with real-time updates via WebSockets
- Staff management, attendance, and payroll
- Financial reporting

## Project Architecture
- **Framework**: Django 5.2 with Django REST Framework
- **ASGI Server**: Daphne (for WebSocket support)
- **WebSocket**: Django Channels for real-time features
- **Database**: SQLite (development)
- **Language**: Python 3.11

## Directory Structure
```
CafeManager/          # Main Django project settings
core/                 # Core app (POS, inventory, staff)
  - templates/core/   # Core HTML templates
  - models.py         # Core models (Product, Employee, Sale, etc.)
  - views.py          # Core views
karaoke/              # Karaoke management app
  - templates/karaoke/# Karaoke HTML templates
  - consumers.py      # WebSocket consumers
  - routing.py        # WebSocket routing
  - models.py         # Karaoke models (Room, Session, etc.)
templates/            # Global templates (login, base)
media/                # Uploaded media (product images)
staticfiles/          # Collected static files
```

## Running the Application
The app runs with Daphne ASGI server:
```bash
daphne -b 0.0.0.0 -p 5000 CafeManager.asgi:application
```

## Key Configuration
- ALLOWED_HOSTS: ['*'] (for Replit proxy)
- CSRF_TRUSTED_ORIGINS configured for Replit domains
- X_FRAME_OPTIONS: 'ALLOWALL' (for iframe embedding)

## Recent Changes
- 2025-12-23: Initial Replit setup, configured for development environment
