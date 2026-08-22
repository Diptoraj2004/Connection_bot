"""
services/payment_service.py — Institutional Payment via Razorpay.

Mode 1: Simulated invoices (no real money)
Mode 2: Real Razorpay API (free account, live payments)

Pricing:
  ₹100/student/year — B2B institutional license
  15% NGO referral commission per booked session
  ₹3,000/cohort — volunteer training certification fee
"""
from datetime import datetime
from config import settings
from data.db import insert_record, query_records

RAZORPAY_KEY_ID     = settings.__dict__.get("razorpay_key_id", "")
RAZORPAY_KEY_SECRET = settings.__dict__.get("razorpay_key_secret", "")
PRICE_PER_STUDENT_INR = 100
NGO_COMMISSION_PCT    = 0.15


def create_institutional_order(college_name: str, student_count: int,
                                contact_email: str, academic_year: str = "2025-26") -> dict:
    """Create a payment order for a college license."""
    amount_inr   = student_count * PRICE_PER_STUDENT_INR
    amount_paise = amount_inr * 100  # Razorpay uses paise

    record = insert_record("payment_order", {
        "college_name":   college_name,
        "student_count":  student_count,
        "amount_inr":     amount_inr,
        "contact_email":  contact_email,
        "academic_year":  academic_year,
        "status":         "pending",
        "created_at":     datetime.utcnow().isoformat(),
    })

    if not RAZORPAY_KEY_ID or settings.is_testing:
        return {
            "mode":         "simulated",
            "order_id":     f"order_DEMO_{record['id'][:8]}",
            "amount_inr":   amount_inr,
            "college":      college_name,
            "students":     student_count,
            "invoice_note": f"₹{amount_inr:,} for {student_count} students × ₹{PRICE_PER_STUDENT_INR}/year",
            "pay_link":     "https://razorpay.com (configure RAZORPAY_KEY_ID for live payments)",
            "record_id":    record["id"][:8],
        }

    try:
        import razorpay
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        order  = client.order.create({
            "amount":   amount_paise,
            "currency": "INR",
            "notes":    {"college": college_name, "students": str(student_count)},
        })
        insert_record("razorpay_order", {"order": order, "record_id": record["id"]})
        return {
            "mode":       "live",
            "order_id":   order["id"],
            "amount_inr": amount_inr,
            "college":    college_name,
            "students":   student_count,
            "razorpay_key": RAZORPAY_KEY_ID,
        }
    except ImportError:
        return {"error": "pip install razorpay to enable live payments"}
    except Exception as e:
        return {"error": str(e)}


def record_ngo_commission(ngo_id: str, session_fee_inr: int) -> dict:
    commission = int(session_fee_inr * NGO_COMMISSION_PCT)
    return insert_record("commission", {
        "ngo_id":      ngo_id,
        "session_fee": session_fee_inr,
        "commission":  commission,
        "ts":          datetime.utcnow().isoformat(),
    })


def get_revenue_summary() -> dict:
    orders     = query_records("payment_order", {"status": "paid"})
    commissions= query_records("commission")
    total_rev  = sum(o.get("amount_inr", 0) for o in orders)
    total_comm = sum(c.get("commission", 0) for c in commissions)
    return {
        "total_license_revenue_inr": total_rev,
        "total_ngo_commissions_inr": total_comm,
        "total_inr":                 total_rev + total_comm,
        "paid_orders":               len(orders),
        "pricing_note":              f"₹{PRICE_PER_STUDENT_INR}/student/year | {int(NGO_COMMISSION_PCT*100)}% NGO commission",
    }
