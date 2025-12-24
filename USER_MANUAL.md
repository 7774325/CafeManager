# CafeManager - User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [Outlet & Superuser Setup](#outlet--superuser-setup)
3. [POS System Usage](#pos-system-usage)
4. [Karaoke Sessions](#karaoke-sessions)
5. [Inventory Management](#inventory-management)
6. [HR & Payroll](#hr--payroll)
7. [Manager Dashboard](#manager-dashboard)

---

## Getting Started

### System Access
- **Admin Panel**: `/admin/`
- **Manager Dashboard**: `/dashboard/` (after login)
- **POS Interface**: `/pos/`
- **Karaoke Management**: `/karaoke/rooms/`

### Login Credentials
- Username & password are set by your outlet owner/superuser
- Each user is associated with ONE outlet (no cross-outlet access)

---

## Outlet & Superuser Setup

### Creating a New Outlet (Superuser Only)

1. Navigate to `/admin/` and login with superuser account
2. Go to **Outlets** section
3. Click **Add Outlet**
4. Fill in:
   - **Name**: Your café/karaoke name
   - **Owner**: Select the user account for this outlet
   - **Location**: Physical address
   - **Logo**: Upload your outlet's branding image (optional, jpg/png)
5. Click **Save**

### Creating Employees

1. Go to **Employees** section in admin
2. Click **Add Employee**
3. Fill in:
   - **Name**: Full name
   - **Outlet**: Select the outlet
   - **Role**: e.g., "Cashier", "Server", "Manager"
   - **Payment Type**: Choose one:
     - **P (Permanent)**: Fixed monthly salary
     - **C (Commission-Based)**: Base salary + commission on sales
     - **D (Daily-Rated)**: Salary per day worked
   - **Base Salary**: Monthly (P), Minimum (C), or Daily rate (D)
   - **Commission Rate**: % of sales (only for C type)
   - **Phone & Email**: Contact details
   - **Active**: Check to enable employee
4. Click **Save**

---

## POS System Usage

### Quick Checkout (Counter Sales)

1. Go to `/pos/` or click **POS** from manager dashboard
2. **Select Products**:
   - Click product cards to add to cart
   - Adjust quantities with +/- buttons
3. **Review Cart**:
   - See all items, prices, and real-time total
4. **Apply Discount** (optional):
   - Enter discount amount in text field
5. **Checkout**:
   - Select payment method: Cash, Card, Credit (for later payment)
   - Enter customer name (optional)
   - Click **Submit Sale**
6. **Stock Automatically Deducted**: Product inventory is updated instantly

### Stock Management
- **View Low Stock**: Go to `/stock/low/` to see items below threshold
- **Low Stock Alerts**: Displayed on manager dashboard
- **Reorder**: Contact supplier when stock drops

---

## Karaoke Sessions

### Starting a Karaoke Session

1. Go to `/karaoke/rooms/` and click **Start Session**
2. Fill in:
   - **Room**: Select VIP or Standard room
   - **Customer Name**: Name of the customer
   - **Duration**: Booking time in minutes (minimum varies by room)
3. Click **Start**
4. Session timer begins - room is now **Active**

### During Session

- **Pause Session**: Click **Pause** button (time still runs, but customer can control music)
- **Resume**: Click **Resume** to continue
- **Add Extra Time**: Add more minutes at any time
- **Food & Beverage Ordering**: Customer can order from tablet integrated in room

### Calculating Charges

**Billing Formula**: 
```
Room Charge = (Duration in minutes / 60) × Hourly Rate
Extra Charges = Food/Beverage items + extra time fees
Total = Room Charge + Extra Charges
```

### Ending Session

1. Click **Checkout Session**
2. Review:
   - **Room Charge**: Auto-calculated based on elapsed time
   - **Food/Beverage Total**: Sum of all ordered items
   - **Grand Total**: Room + Food charges
3. Select payment method: Cash, Card, or Credit
4. Click **Complete** to finalize and mark room as **Available**

---

## Inventory Management

### Adding Inventory (Superuser)

1. Go to **Products** in admin
2. Click **Add Product**
3. Fill in:
   - **Name**: Product name (e.g., "Beer", "Biryani")
   - **Outlet**: Select outlet
   - **Category**: Group type (e.g., "Beverages", "Food")
   - **SKU**: Unique code (optional)
   - **Cost Price**: What you paid for it
   - **Selling Price**: What you charge customer
   - **Current Stock**: Quantity on hand
   - **Image**: Product photo (optional)
4. Click **Save**

### Tracking Stock Changes

All inventory changes are logged in **Inventory Logs**:
- **Sale**: Deducted when customer buys
- **Purchase**: Added when you buy from supplier
- **Adjustment**: Manual corrections
- **Spoilage**: Items damaged/expired
- **Transfer**: Moved between outlets (future)

### Low Stock Alerts

- Products below 10 units appear in `/stock/low/`
- Alerts on manager dashboard
- Plan reorders proactively

---

## HR & Payroll

### Employee Check-In/Check-Out

**For Employees**:
1. Click **Check-In** on dashboard when arriving
   - Records check-in time
2. Click **Check-Out** when leaving
   - Records check-out time
   - Automatically calculates hours worked

**For Managers**:
1. Go to `/attendance/report/`
2. Select month/year to filter
3. View all employee check-in/out times and hours worked

### Three Payment Structures

#### 1. PERMANENT (P) - Fixed Monthly Salary
- **Calculation**: Same amount every month regardless of hours
- **Use Case**: Full-time staff with fixed contracts
- **Example**: Employee paid MVR 5,000/month
- **On Payroll Report**: Base Amount = MVR 5,000

#### 2. DAILY-RATED (D) - Paid Per Day Worked
- **Calculation**: Daily Rate × Number of days worked (based on attendance)
- **Use Case**: Casual staff paid by the day
- **Example**: Employee with MVR 200/day who worked 20 days = MVR 4,000
- **On Payroll Report**: Base Amount = MVR 200 × 20 days

#### 3. COMMISSION-BASED (C) - Minimum Salary + Sales Bonus
- **Calculation**: Base Salary + (Total Outlet Sales × Commission Rate / 100)
- **Use Case**: Managers or incentive-based staff
- **Example**: 
  - Base Salary: MVR 3,000
  - Commission Rate: 2%
  - Outlet sales this month: MVR 150,000
  - Total = MVR 3,000 + (150,000 × 2/100) = MVR 6,000
- **On Payroll Report**: Shows Base Amount + Commission Amount separately

### Calculating Monthly Payroll

1. Go to `/payroll/calculate/?month=12&year=2025`
2. Click **Calculate Payroll** button
3. System automatically:
   - Sums hours from attendance records
   - Pulls sales data from POS
   - Calculates payroll for ALL active employees at your outlet
   - Creates payroll records
4. Redirect to payroll report showing results

### Viewing Payroll Report

1. Go to `/payroll/report/`
2. See breakdown for each employee:
   - **Type**: Payment structure (Permanent/Daily/Commission)
   - **Base Amount**: Fixed amount or calculated from days/hours
   - **Commission**: Sales bonus (commission-based only)
   - **Total Earnings**: Base + Commission
   - **Deductions**: Any reductions (future feature)
   - **Net Pay**: Final amount employee receives
3. **Total Payroll**: Sum of all employee payments

### Payroll Status Workflow

- **Draft**: Initial state after calculation
- **Calculated**: Amounts finalized, ready for review
- **Approved**: Manager approved payment
- **Paid**: Employee has received payment

---

## Manager Dashboard

### Access
- Go to `/dashboard/` after logging in
- Shows real-time summaries for your outlet

### Dashboard Displays

**POS Sales (Today)**
- Total sales from POS transactions
- Updates in real-time as customers checkout

**Karaoke Revenue (Today)**
- Sum of all completed karaoke session charges
- Includes room charges + food/beverage

**Total Revenue**
- POS Sales + Karaoke Revenue
- Full picture of daily performance

**Low Stock Alerts**
- List of products below 10 units
- Quick reference for ordering

**Quick Action Buttons**
- **Open POS**: Jump to sales counter
- **Karaoke Sessions**: Manage active rooms
- **Attendance**: View employee check-in/out
- **Payroll**: Calculate and view monthly payroll

---

## UI Features

### Lavender & Black Gradient Theme
- **Primary Color**: Lavender (#8b5cf6)
- **Accent Color**: Dark (#1a1a2e)
- **Professional Look**: Modern, clean interface
- **Consistent Design**: Applied across all pages

### Responsive Design
- Works on desktop, tablet, and mobile
- Touch-friendly buttons and inputs
- Auto-adjusting layouts

### Multi-Tenant Isolation
- Each user only sees data for their outlet
- No cross-outlet access
- Completely separate databases per outlet

---

## Troubleshooting

### "Cannot access other outlet's data"
- Each user is linked to ONE outlet
- Contact admin to change outlet assignment

### "Low Stock Alert keeps showing"
- Purchase more inventory
- Or adjust "Current Stock Level" in admin

### "Check-out time shows 0 hours"
- Ensure both check-in AND check-out times are recorded
- Times must be on the same day

### "Payroll shows MVR 0"
- Ensure employees have attendance records
- For commission-based: check if sales exist for the month
- Verify payment type is set correctly

---

## Support

For issues or questions:
1. Check this manual first
2. Contact your outlet superuser/admin
3. Check system error messages for guidance

---

## Summary Checklist

- ✅ Created outlet with owner
- ✅ Added employees with payment types
- ✅ Processed POS sales
- ✅ Managed karaoke sessions
- ✅ Tracked inventory
- ✅ Recorded employee attendance
- ✅ Calculated monthly payroll
- ✅ Viewed manager dashboard

**You're ready to manage your café!** 🎉
