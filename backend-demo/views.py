def productToItem(p:Product):
    specsQs = p.specs.all()
    ruleImagesQs = p.rule_images.all()[:3]

    item = {
        "id":p.id,
        "title":p.title,
        "img":p.img,
        "desc":p.desc,
        "sales":p.sales_count,
        "rule_images":[img.image for img in ruleImagesQs]
    }
    if specsQs.exists():
        item["specs"] = [
            {
            "specId":s.spec_id,
            "name":s.name,
            "price":float(s.price),
            }
            for s in specsQs
        ]
    else: item["price"] = str(p.price or "0.00")
    return item
  
# for search function to return all items which name contains the keyword
def items_list(request):
    keyword = request.GET.get("keyword","").strip()

    qs = Product.objects.filter(is_active = True)
    if keyword:
        qs = qs.filter(title__icontains = keyword)

    qs = qs.order_by("-id")

    data = []
    for p in qs:
        item ={
            "id":p.id,
            "title":p.title,
            "price":str(p.price),
            "description":p.desc,
            "cover_url":p.img,
        }
        # if this item have an attribute "specs"
        if hasattr(p, "specs") and p.specs.exists():
            specs_list = []
            for s in p.specs.all():
                specs_list.append({
                    "specId": s.spec_id,
                    "name": s.name,
                    "price": float(s.price)
                })
            item["specs"] = specs_list
        else:
            item["price"] = float(p.price)

        data.append(item)

    return JsonResponse({
        "code":0,
        "data":data
    })


# when user clink a product, then this function will return this product detail
def items_detail(request,product_id):
    try:
        # p = Product.objects.get(id = product_id,is_active = True)
        p = Product.objects.prefetch_related("specs","rule_images").get(
            id = product_id,
            is_active = True
        )
    except Product.DoesNotExist:
        return JsonResponse({
            "code":404,
            "msg":"not found~"
        })
    return JsonResponse({
        "code":0,
        "data":productToItem(p)
    })

def category_list(request):
    qs = Category.objects.all().order_by("id")

    data = []
    for c in qs:
        data.append({
            "id": c.id,
            "name": c.name
        })

    return JsonResponse({
        "code": 0,
        "data": data
    })

# using this function to category different type of products
def goods_by_category(request):
    category_id = request.GET.get("category_id", "").strip()

    qs = Product.objects.filter(is_active=True)

    if category_id:
        qs = qs.filter(category_id=category_id)

    qs = qs.prefetch_related("specs").order_by("price", "id")

    data = []
    for p in qs:
        item = {
            "id": p.id,
            "title": p.title,
            "img": p.img,
            "desc": p.desc,
            "category_id": p.category_id,
            "sales":p.sales_count,
        }

        specs_qs = p.specs.all()
        if specs_qs.exists():
            specs = []
            min_price = None

            for s in specs_qs:
                price = float(s.price)
                specs.append({
                    "specId": s.spec_id,
                    "name": s.name,
                    "price": price
                })

                if min_price is None or price < min_price:
                    min_price = price

            item["specs"] = specs
            item["priceText"] = f"{min_price:.2f}" if min_price is not None else "0.00"
        else:
            price = float(p.price or 0)
            item["price"] = f"{price:.2f}"
            item["priceText"] = f"{price:.2f}"

        data.append(item)

    # always shows the lowest price of a product if it have different species
    data.sort(key=lambda x: float(x.get("priceText", "0.00")))

    return JsonResponse({
        "code": 0,
        "data": data
    })

# this function is for user to register
def register_user(request):
    if request.method != "POST":
        return JsonResponse({"code": 405, "msg": "method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"code": 400, "msg": "invalid json"}, status=400)

    nickname = (body.get("nickname") or "").strip()
    gender = (body.get("gender") or "unknown").strip()
    email = (body.get("email") or "").strip()
    phone = (body.get("phone") or "").strip()
    login_account_type = (body.get("login_account_type") or "").strip()
    password = (body.get("password") or "").strip()
    confirm_password = (body.get("confirm_password") or "").strip()
    
    #these attributes are used to check whether the user is a human
    captcha_key = (body.get("captcha_key") or "").strip()
    captcha_code = (body.get("captcha_code") or "").strip()

    if not nickname:
        return JsonResponse({"code": 400, "msg": "请输入昵称"})

    if login_account_type not in ["email", "phone"]:
        return JsonResponse({"code": 400, "msg": "请选择登录账号类型"})
    
    if email and not is_valid_email(email):
        return JsonResponse({"code":400,"msg":"邮件格式不正确"})
    
    if phone and not is_valid_phone(phone):
        return JsonResponse({"code":400,"msg":"手机格式不正确"})
# this function is used to check whether this type is allowed or not
    if login_account_type == "email":
        if not email:
            return JsonResponse({"code": 400, "msg": "请输入邮箱"})
        if AppUser.objects.filter(email=email).exists():
            return JsonResponse({"code": 400, "msg": "该邮箱已注册"})

    if login_account_type == "phone":
        if not phone:
            return JsonResponse({"code": 400, "msg": "请输入手机号"})
        # if not is_valid_phone(phone):
        #     return JsonResponse({"code": 400, "msg": "手机号格式不正确"})
        if AppUser.objects.filter(phone=phone).exists():
            return JsonResponse({"code": 400, "msg": "该手机号已注册"})

    if not password:
        return JsonResponse({"code": 400, "msg": "请输入密码"})
    # use our function to check whether user's password is safe enough
    if not is_valid_password(password):
        return JsonResponse({"code": 400, "msg": "密码至少13位，且包含大小字母，符合和数字"})

    if password != confirm_password:
        return JsonResponse({"code": 400, "msg": "两次输入密码不一致"})
    
    captcha_ok, captcha_msg = verify_captcha(captcha_key, captcha_code)
    if not captcha_ok:
        return JsonResponse({"code": 400, "msg": captcha_msg})
    
    # we only allows our users to registers 5 time during one day! Avoid being maliciously registered
    
    ok, ip = check_ip_daily_limit(request, "register", 5)
    if not ok:
        return JsonResponse({
            "code": 403,
            "msg": "当前网络今日注册次数已达上限，请明天再试"
        }, status=403)
    
    try:
        with transaction.atomic():
            # 正常创建新账户
            user = AppUser.objects.create(
                nickname=nickname,
                gender=gender,
                email=email or None,
                phone=phone or None,
                login_account_type=login_account_type,
                password=make_password(password)
            )
          
            # token = uuid.uuid4().hex
            # user.login_token = token

            raw_token = uuid.uuid4().hex
          # save the hash value in our db, avid someone get our db, then get all user's inform.
            user.login_token = hash_token(raw_token)

           # we limit the token's life cycle
            user.token_expire_at = timezone.now() + timedelta(days= 7)
            user.last_login_at = timezone.now()
            user.save()
          
            increase_ip_daily_count(ip, "register")

            return JsonResponse({
                "code": 0,
                "msg": "注册成功",
                "data": {
                    "userId": user.id,
                    "nickname": user.nickname,
                    "gender": user.gender,
                    "email": user.email,
                    "phone": user.phone,
                    "login_account_type": user.login_account_type,
                    "points": user.points,
                    "coupon_count": user.coupon_count,
                    "balance": str(user.balance),
                    "avatar":user.avatar,
                    "token":raw_token
                }
            })
    except Exception as e:
        return JsonResponse({
            "code":500,
            "msg":f"注册失败{str(e)}"
        },status = 500)


def logout_user(request):
    if request.method != "POST":
        return JsonResponse({"code": 405, "msg": "method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"code": 400, "msg": "invalid json"}, status=400)

    token = (body.get("token") or "").strip()
    if not token:
        return JsonResponse({"code": 400, "msg": "缺少token"})

    user = AppUser.objects.filter(login_token=token).first()
    if not user:
        return JsonResponse({"code": 400, "msg": "用户未登录或token无效"})
    
    # when user log out, we will set token to empty
    user.login_token = ""
    user.token_expire_at = None
    user.save()

    return JsonResponse({
        "code": 0,
        "msg": "退出登录成功"
    })

# create order
def create_balance_order(request):
    if request.method != "POST":
        return JsonResponse({"code": 405, "msg": "method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"code": 400, "msg": "invalid json"}, status=400)

    token = (body.get("token") or "").strip()
    product_id = body.get("product_id")
    spec_id = (body.get("spec_id") or "").strip()
    #qty = int(body.get("qty") or 1)

    digital_code = (body.get("digital_code") or "").strip()
    text_code = (body.get("text_code") or "").strip()
    order_remark = (body.get("order_remark") or "").strip()

  # we only trust the quality and price from backend instead of front
    try:
        qty = int(body.get("qty") or 1)
    except Exception:
        return JsonResponse({"code":400,"msg":"购买数量不正确"})

    user = get_user_from_token(token)
    if not user:
        return JsonResponse({"code": 401, "msg": "请先登录"}, status=401)

    if not product_id:
        return JsonResponse({"code": 400, "msg": "缺少商品ID"})

    if qty <= 0:
        return JsonResponse({"code": 400, "msg": "购买数量不正确"})

    try:
        product = Product.objects.prefetch_related("specs").get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({"code": 404, "msg": "商品不存在"}, status=404)

    spec_name = ""
    unit_price = Decimal("0.00")

    specs_qs = product.specs.all()

    if specs_qs.exists():
        if not spec_id:
            return JsonResponse({"code":400,"msg":"请选择规格"})
        
        spec = specs_qs.filter(spec_id=spec_id).first()
        if not spec:
            return JsonResponse({"code": 400, "msg": "规格不存在"})
        
        spec_name = spec.name
        unit_price = Decimal(str(spec.price))
    else:
        unit_price = Decimal(str(product.price or "0.00"))

    total_amount = unit_price * qty

    try:
        with transaction.atomic():
            user = AppUser.objects.select_for_update().get(id = user.id)
            
            existed_order = Order.objects.filter(
                user=user,
                status="pending_pay",
                payment_method="balance",
                total_amount=total_amount,
                items__product=product,
                items__spec_id=spec_id
            ).distinct().first()

            if existed_order:
                return JsonResponse({
                    "code": 400,
                    "msg": "请勿重复提交订单",
                    "data": {
                        "order_id": existed_order.id,
                        "order_no": existed_order.order_no
                    }
                })

          # check user's balance
            available_balance = Decimal(str(user.balance or "0.00")) - Decimal(str(user.frozen_balance or "0.00"))
            if available_balance < total_amount:
                return JsonResponse({
                    "code": 400,
                    "msg": "余额不足",
                    "data": {
                        "balance": str(user.balance),
                        "frozen_balance": str(user.frozen_balance),
                        "available_balance": str(available_balance)
                    }
                })
            # let order ir more form, it will more easier to check by admin
            order_no = "0"+timezone.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:8].upper()

    
            order = Order.objects.create(
                user=user,
                order_no=order_no,
                total_amount=total_amount,
                frozen_amount=total_amount,
                payment_method="balance",
                status="pending_pay",
                refund_status = "none",
                digital_code=digital_code,
                text_code=text_code,
                order_remark=order_remark
            )

            OrderItem.objects.create(
                order=order,
                product=product,
                product_title=product.title,
                product_img=product.img,
                spec_id=spec_id,
                spec_name=spec_name,
                unit_price=unit_price,
                qty=qty,
                subtotal=total_amount
            )
            
            user.frozen_balance = Decimal(str(user.frozen_balance)) + total_amount
            user.save()

            #recording
            BalanceLog.objects.create(
                user=user,
                change_type="freeze",
                amount=total_amount,
                note=f"订单冻结：{order.order_no}",
                order=order
            )

            return JsonResponse({
                "code": 0,
                "msg": "下单成功",
                "data": {
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "status": order.status,
                    "payment_method": order.payment_method,
                    "total_amount": str(order.total_amount),
                    "frozen_amount": str(order.frozen_amount),
                    "balance": str(user.balance),
                    "frozen_balance": str(user.frozen_balance)
                }
            })
    except Exception as e:
        return JsonResponse({
            "code":500,
            "msg":f"下单失败:{str(e)}"
        
        },status = 500)
