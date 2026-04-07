lass Category(models.Model):
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class Product(models.Model):
    title = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null = True,
        blank= True,
        related_name="products"
    )
    price = models.DecimalField(max_digits=10,decimal_places=2, null = True, blank = True)
    desc = models.TextField(blank = True)
    img = models.URLField(blank=True)

    sales_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.title
    
# allows some product that can have different species with different price
class ProductSpec(models.Model):
    product = models.ForeignKey(
    Product,
    on_delete=models.CASCADE,
    related_name="specs"
    )
    spec_id = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"{self.product.title} - {self.name}    

class AppUser(models.Model):
    GENDER_CHOICE =(
        ("male","男士"),
        ("Female","女士"),
        ("unknown","保密"),
    )
    nickname = models.CharField(max_length=100)
    gender = models.CharField(max_length=20,choices=GENDER_CHOICE,default="unknown")
    email=models.EmailField(blank= True,null = True, unique = True)
    phone = models.CharField(max_length=20,blank=True,null=True,unique=True)
    
    # for customer login's account, we allow they use their phone# or email addr.
    LOGIN_ACCOUNT_CHOICES = (
        ("email","邮箱"),
        ("phone","手机号"),
    )
    login_account_type = models.CharField(max_length=20, choices=LOGIN_ACCOUNT_CHOICES)
    password = models.CharField(max_length=260)
    avatar = models.URLField(blank=True)
    points = models.IntegerField(default=0)
    coupon_count = models.IntegerField(default=0)
    
    # we provide top up function for customers
    balance = models.DecimalField(max_digits=10,decimal_places=2,default=0)

    login_token = models.CharField(max_length=100,blank=True,default="")
    last_login_at = models.DateTimeField(null=True, blank=True)
    token_expire_at = models.DateTimeField(null=True, blank=True)

    login_fail_count = models.IntegerField(default=0)
    last_fail_time = models.DateTimeField(null= True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    frozen_balance = models.DecimalField(max_digits=10,decimal_places=2,default=0)

    birth_date = models.DateField(null=True,blank=True)
    address = models.CharField(max_length=255,blank=True)
    pay_password = models.CharField(max_length=255,blank=True,default="")

    def __str__(self):
        return self.nickname
    

    
class Order(models.Model):
    STATUS_CHOICES = (
        ("unpaid","未付款"),
        ("pending_pay", "待支付"),
        ("paid_pending", "已支付待处理"),
        ("cancelled", "已取消"),
    )

    PAYMENT_CHOICES = (
        ("balance", "账户支付"),
        ("wechat", "微信支付"),
    )
    REFUND_STATU_CHOICES = (
        ("none","无退单申请"),
        ("applying","申请退单中"),
        ("approved","退单已通过"),
        ("rejected","退单已取消"),
    )

    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name="orders") #delete this table

    order_no = models.CharField(max_length=50, unique=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2,default="0.00")
    frozen_amount = models.DecimalField(max_digits=10, decimal_places=2, default="0.00")

    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unpaid")
    # status flow rule
    VALID_TRANSITIONS = {
        "unpaid": ["pending_pay", "cancelled"],
        "pending_pay": ["paid_pending", "cancelled"],
        "paid_pending": [],
        "cancelled": [],
    }

    digital_code = models.CharField(max_length=100, blank=True)
    text_code = models.CharField(max_length=100, blank=True)
    order_remark = models.TextField(blank=True)

    refund_status = models.CharField(max_length= 20, choices=REFUND_STATU_CHOICES, default="none")
    refund_playmate_id = models.CharField(max_length=50,blank=True,default="")
    refund_reason = models.TextField(blank=True,default="")

    expire_at = models.DateTimeField(null=True,blank=True)
    from_ready_to_pay = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    #function for transitions rules
    def can_transition(self, new_status):
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    def transition_to(self, new_status):
        if not self.can_transition(new_status):
            raise ValueError(f"非法状态变更: {self.status} → {new_status}")
        
        self.status = new_status

    def __str__(self):
        return f"{self.order_no} ({self.status})"
