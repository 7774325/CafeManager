from django.urls import path
from . import views

urlpatterns = [
    # Main Site Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Tools
    path('import/', views.import_data, name='import_data'),
    path('export/', views.export_data, name='export_data'),
    path('stock/bulk/', views.bulk_stock_entry, name='bulk_stock_entry'),
    path('spoilage/', views.log_spoilage, name='log_spoilage'),
    
    # Financials - UPDATED NAME TO MATCH VIEWS
    path('reports/financial/', views.financial_summary_report, name='financial_summary'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('payroll/', views.payroll_report, name='payroll_report'),
    
    # Settings & Credit
    path('settings/', views.outlet_settings, name='outlet_settings'),
    path('credit/', views.customer_credit_list, name='customer_credit_list'),
    path('credit/clear/<int:customer_id>/', views.clear_partial_credit, name='clear_partial_credit'),
]