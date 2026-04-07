# show a function belongs to admin
# we can approve customer's order to cancel
def approve_refund(modeladmin, request, queryset):
    success_count = 0
    skip_count = 0
    error_count = 0

    for raw_order in queryset:
        try:
            with transaction.atomic():
                try:
                    # we need to check this order belongs which users (avid 
                    order = Order.objects.select_for_update().select_related("user").get(id = raw_order.id)  
                except Order.DoesNotExist:
                    skip_count +=1
                    continue

                # admin can approve the status of order that is pending instead of already completed
                if order.refund_status != "applying" or order.status != "pending_pay":
                    skip_count += 1
                    continue

                user = AppUser.objects.select_for_update().get(id = order.user.id)

                frozen_amount = Decimal(str(order.frozen_amount or "0.00"))
                current_frozen = Decimal(str(user.frozen_balance or "0.00"))

                if frozen_amount <= Decimal("0.00"):
                    error_count +=1
                    continue
                if current_frozen < frozen_amount:
                    error_count +=1
                    continue
                
                #let Pending money free
                user.frozen_balance = current_frozen - frozen_amount
                user.save()

                order.status = "cancelled"
                order.refund_status = "approved"
                order.frozen_amount = Decimal("0.00")
                order.save()

                BalanceLog.objects.create(
                    user=user,
                    change_type="unfreeze",
                    amount=frozen_amount,
                    note=f"确认退单释放冻结：{order.order_no}",
                    order=order
                )

                success_count += 1
        except Exception:
            error_count +=1
            continue

    if success_count:
        messages.success(request, f"已成功确认 {success_count} 笔退单。")
    if skip_count:
        messages.warning(request, f"有 {skip_count} 笔订单不是“申请退单中”，已跳过。")
    if error_count:
        messages.error(request, f"有 {error_count} 笔订单不是“申请退单中”，已跳过。")
