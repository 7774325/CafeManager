from django.urls import path
from . import views

urlpatterns = [
    # Landing page & Dashboard
    path('', views.homepage, name='homepage'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # POS System
    path('pos/', views.record_sale, name='record_sale'),
    path('api/pos/submit/', views.submit_sale, name='submit_sale'),
    path('api/product/<int:product_id>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('receipt/<int:transaction_id>/', views.receipt_detail, name='receipt_detail'),
    
    # Tools
    path('import/', views.import_data, name='import_data'),
    path('export/', views.export_data, name='export_data'),
    path('stock/bulk/', views.bulk_stock_entry, name='bulk_stock_entry'),
    path('stock/low/', views.low_stock_report, name='low_stock_report'),
    path('spoilage/', views.log_spoilage, name='log_spoilage'),
    
    # Financials
    path('reports/financial/', views.financial_summary_report, name='financial_summary'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('payroll/', views.payroll_report, name='payroll_report'),
    
    # Settings & Credit
    path('settings/', views.outlet_settings, name='outlet_settings'),
    path('credit/', views.customer_credit_list, name='customer_credit_list'),
    path('credit/clear/<int:customer_id>/', views.clear_partial_credit, name='clear_partial_credit'),
    
    # HR & Payroll
    path('attendance/check-in/', views.attendance_check_in, name='attendance_check_in'),
    path('attendance/check-out/', views.attendance_check_out, name='attendance_check_out'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    path('payroll/calculate/', views.payroll_calculate, name='payroll_calculate'),
    path('payroll/report/', views.payroll_report, name='payroll_report'),
]