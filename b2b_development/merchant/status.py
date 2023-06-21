from django.db.models import TextChoices
class ProductStatus(TextChoices):
    DRAFT = "DRAFT","Draft"
    PUBLISHED = "PUBLISHED","Published"
    UNPUBLISHED = "UNPUBLISHED","Unpublished"
    ARCHIVED = "ARCHIVED","Urchived"
    HIDDEN = "HIDDEN","Hidden"
    REMOVED = "REMOVED","Removed"

class ConnectionStatus(TextChoices):
    PENDING = "PENDING","Pending"
    APPROVED = "APPROVED","Approved"
    DECLINED = "DECLINED","Declined"

class PaymentOption(TextChoices):
    CASH_ON_DELIVERY = "CASH ON DELIVERY", "Cash on delivery"
    MOBILE_BANKING = "MOBILE BANKING","Mobile Banking"
    ONLINE_BANKING = "ONLINE BANKING","Moble Banking"

class UserRole(TextChoices):
    OWNER = "OWNER", "Owner"
    STAFF = "STAFF", "Staff"
    ADMIN = "ADMIN","Admin"

class OrderStatus(TextChoices):
    ON_PROCESSING = "ON PROCESSING", "On Processing"
    COMPLETE = "COMPLETED","Completed"