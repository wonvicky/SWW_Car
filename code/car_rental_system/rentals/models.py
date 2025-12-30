from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from datetime import date
from decimal import Decimal
from django.utils import timezone
from customers.models import Customer
from vehicles.models import Vehicle


class Rental(models.Model):
    RENTAL_STATUS_CHOICES = [
        ('PENDING', '预订中'),
        ('ONGOING', '进行中'),
        ('OVERDUE', '已超时未归还'),
        ('COMPLETED', '已完成'),
        ('CANCELLED', '已取消'),
    ]
    
    SETTLEMENT_STATUS_CHOICES = [
        ('UNSETTLED', '未结算'),
        ('PARTIAL', '部分结算'),
        ('SETTLED', '已结算'),
    ]
    
    DEPOSIT_METHOD_CHOICES = [
        ('CASH', '现金押金'),
        ('STUDENT_CARD', '学生卡抵押'),
        ('VIP_FREE', 'VIP免押金'),
        ('FIRST_FREE', '首次租车免押金'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='rentals',
        verbose_name='客户'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='rentals',
        verbose_name='车辆'
    )
    start_date = models.DateField(
        '租赁开始日期',
        help_text='租赁开始日期'
    )
    end_date = models.DateField(
        '租赁结束日期',
        help_text='租赁结束日期'
    )
    actual_return_date = models.DateField(
        '实际还车日期',
        blank=True,
        null=True,
        help_text='实际还车日期'
    )
    actual_return_location = models.CharField(
        '实际还车门店',
        max_length=200,
        blank=True,
        null=True,
        help_text='实际还车门店'
    )
    overdue_fee = models.DecimalField(
        '超时还车费用',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='超时还车产生的赔偿费用'
    )
    total_amount = models.DecimalField(
        '总金额',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='租赁总费用'
    )
    deposit = models.DecimalField(
        '押金',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='租赁押金金额'
    )
    pickup_location = models.CharField(
        '取车地点',
        max_length=200,
        default='门店',
        help_text='取车地点'
    )
    return_location = models.CharField(
        '还车地点',
        max_length=200,
        blank=True,
        null=True,
        help_text='还车地点（异地还车时填写）'
    )
    is_cross_location_return = models.BooleanField(
        '是否异地还车',
        default=False,
        help_text='是否异地还车'
    )
    cross_location_fee = models.DecimalField(
        '异地还车费用',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='异地还车产生的额外费用'
    )
    status = models.CharField(
        '订单状态',
        max_length=20,
        choices=RENTAL_STATUS_CHOICES,
        default='PENDING',
        help_text='当前订单状态'
    )
    notes = models.TextField(
        '备注',
        blank=True,
        null=True,
        help_text='订单备注信息'
    )
    created_at = models.DateTimeField(
        '创建时间',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        '更新时间',
        auto_now=True
    )
    settlement_status = models.CharField(
        '结算状态',
        max_length=20,
        choices=SETTLEMENT_STATUS_CHOICES,
        default='UNSETTLED',
        help_text='订单费用结算状态'
    )
    settled_at = models.DateTimeField(
        '结算时间',
        blank=True,
        null=True,
        help_text='订单完成并结算的时间'
    )
    amount_paid = models.DecimalField(
        '累计支付金额',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='用户累计支付金额（不含退款）'
    )
    amount_refunded = models.DecimalField(
        '累计退款金额',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='系统累计退款金额'
    )
    
    # 学生卡抵押相关字段
    deposit_method = models.CharField(
        '押金方式',
        max_length=20,
        choices=DEPOSIT_METHOD_CHOICES,
        default='CASH',
        help_text='押金缴纳方式'
    )
    student_card_image = models.ImageField(
        '学生卡照片',
        upload_to='student_cards/%Y/%m/',
        blank=True,
        null=True,
        help_text='学生卡正面照片'
    )
    student_id = models.CharField(
        '学号',
        max_length=50,
        blank=True,
        null=True,
        help_text='学生学号'
    )
    student_name = models.CharField(
        '学生姓名',
        max_length=100,
        blank=True,
        null=True,
        help_text='学生姓名'
    )
    student_school = models.CharField(
        '学校名称',
        max_length=200,
        blank=True,
        null=True,
        help_text='所属学校'
    )
    student_major = models.CharField(
        '院系专业',
        max_length=200,
        blank=True,
        null=True,
        help_text='院系专业（选填）'
    )
    card_verified = models.BooleanField(
        '学生卡已核验',
        default=False,
        help_text='学生卡是否已线下核验'
    )
    card_returned = models.BooleanField(
        '学生卡已归还',
        default=False,
        help_text='学生卡是否已归还'
    )
    
    class Meta:
        db_table = 'rentals'
        verbose_name = '租赁订单'
        verbose_name_plural = '租赁订单'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['status']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['vehicle', 'status']),
        ]
    
    @classmethod
    def auto_update_status(cls):
        """
        自动更新订单状态
        - 预订中 → 进行中：当到达开始日期时
        - 进行中 → 已超时未归还：当超过结束日期时
        使用缓存避免频繁更新（每5分钟最多更新一次）
        """
        from django.core.cache import cache
        from django.db import transaction
        
        cache_key = 'rental_status_auto_update'
        last_update = cache.get(cache_key)
        
        # 如果5分钟内已更新过，跳过
        if last_update:
            return
        
        today = date.today()
        updated_count = 0
        
        try:
            with transaction.atomic():
                # 1. 激活预订中订单（预订中 → 进行中）
                pending_rentals = cls.objects.filter(
                    status='PENDING',
                    start_date__lte=today
                ).select_related('vehicle')
                
                for rental in pending_rentals:
                    rental.status = 'ONGOING'
                    rental.save(update_fields=['status', 'updated_at'])
                    updated_count += 1
                    
                    # 更新车辆状态为已租
                    if rental.vehicle.status == 'AVAILABLE':
                        rental.vehicle.status = 'RENTED'
                        rental.vehicle.save(update_fields=['status'])
                
                # 2. 更新过期订单（进行中 → 已超时未归还）
                overdue_rentals = cls.objects.filter(
                    status='ONGOING',
                    end_date__lt=today
                )
                
                for rental in overdue_rentals:
                    rental.status = 'OVERDUE'
                    rental.save(update_fields=['status', 'updated_at'])
                    updated_count += 1
            
            # 设置缓存，5分钟内不再更新
            cache.set(cache_key, timezone.now(), 300)  # 5分钟缓存
            
        except Exception as e:
            # 更新失败不影响正常流程
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'自动更新订单状态失败: {e}')
    
    def clean(self):
        """自定义验证方法"""
        super().clean()
        
        # 验证日期逻辑
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError('租赁结束日期不能早于开始日期')
            
            # 如果是更新，验证实际还车日期
            if self.actual_return_date:
                if self.actual_return_date < self.start_date:
                    raise ValidationError('实际还车日期不能早于租赁开始日期')
                if self.actual_return_date > date.today():
                    raise ValidationError('实际还车日期不能晚于今天')
    
    def save(self, *args, **kwargs):
        """保存时计算总金额和押金"""
        if not self.total_amount and self.start_date and self.end_date and self.vehicle:
            # 计算租赁天数
            rental_days = (self.end_date - self.start_date).days + 1
            self.total_amount = self.vehicle.daily_rate * rental_days
        
        # 使用动态押金计算机制
        if self.customer and self.vehicle and self.start_date and self.end_date:
            # 如果押金为0且还没有设置，计算动态押金
            if self.deposit == Decimal('0.00'):
                dynamic_deposit, deposit_details = self.calculate_dynamic_deposit()
                self.deposit = dynamic_deposit
        
        # 如果设置了异地还车，但还车地点为空，则使用取车地点
        if self.is_cross_location_return and not self.return_location:
            self.return_location = self.pickup_location
        
        # 如果异地还车但费用为0，设置默认费用（可以根据业务规则调整）
        if self.is_cross_location_return and self.cross_location_fee == Decimal('0.00'):
            # 默认异地还车费用为日租金的50%（可根据实际业务调整）
            if self.vehicle:
                self.cross_location_fee = self.vehicle.daily_rate * Decimal('0.5')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.customer.name} - {self.vehicle.license_plate} ({self.start_date})"
    
    def __repr__(self):
        return f"<Rental: {self.customer.name} - {self.vehicle.license_plate}>"
    
    @property
    def rental_days(self):
        """计算租赁天数（预订天数）"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @property
    def actual_rental_days(self):
        """
        计算实际租赁天数
        如果已还车，根据实际还车日期计算；否则使用预订天数
        """
        if self.actual_return_date and self.start_date:
            return (self.actual_return_date - self.start_date).days + 1
        return self.rental_days
    
    def calculate_dynamic_deposit(self):
        """
        动态计算押金金额
        根据以下因素综合计算：
        1. 押金方式：学生卡抵押、VIP免押金、首次免押金均为0
        2. 车辆价值：车辆越贵，押金越高
        3. 租赁时长：租期越长，风险系数越大
        4. 客户信用：信用越高，押金折扣越多
        5. 会员等级：VIP免押金
        6. 首次租车：首次租车用户免押金
        
        计算公式：
        基础押金 = 车辆价值 * 基础押金率（0.03）
        时长系数 = 1 + (min(租赁天数, 30) - 1) * 0.01  （0-30天，每天增加1%）
        信用折扣 = 信用评分 / 100  （0.0-1.0）
        最终押金 = 基础押金 * 时长系数 * (2 - 信用折扣)
        
        返回：(押金金额, 计算明细字典)
        """
        if not self.vehicle or not self.customer:
            return Decimal('0.00'), {}
        
        # 学生卡抵押免押金
        if self.deposit_method == 'STUDENT_CARD':
            return Decimal('0.00'), {
                'base_deposit': Decimal('0.00'),
                'vehicle_value': getattr(self.vehicle, 'vehicle_value', Decimal('100000.00')),
                'rental_days': self.rental_days,
                'duration_factor': Decimal('1.00'),
                'credit_score': getattr(self.customer, 'credit_score', 100),
                'credit_discount': Decimal('1.00'),
                'final_deposit': Decimal('0.00'),
                'reason': '学生卡抵押，免押金'
            }
        
        # VIP用户免押金
        if self.customer.member_level == 'VIP' or self.deposit_method == 'VIP_FREE':
            return Decimal('0.00'), {
                'base_deposit': Decimal('0.00'),
                'vehicle_value': getattr(self.vehicle, 'vehicle_value', Decimal('100000.00')),
                'rental_days': self.rental_days,
                'duration_factor': Decimal('1.00'),
                'credit_score': getattr(self.customer, 'credit_score', 100),
                'credit_discount': Decimal('1.00'),
                'final_deposit': Decimal('0.00'),
                'reason': 'VIP会员享受免押金优惠'
            }
        
        # 首次租车用户免押金
        # 检查该客户是否有已完成的订单（不包括当前订单）
        if self.deposit_method == 'FIRST_FREE':
            return Decimal('0.00'), {
                'base_deposit': Decimal('0.00'),
                'vehicle_value': getattr(self.vehicle, 'vehicle_value', Decimal('100000.00')),
                'rental_days': self.rental_days,
                'duration_factor': Decimal('1.00'),
                'credit_score': getattr(self.customer, 'credit_score', 100),
                'credit_discount': Decimal('1.00'),
                'final_deposit': Decimal('0.00'),
                'reason': '首次租车用户享受免押金优惠'
            }
        
        completed_rentals_count = Rental.objects.filter(
            customer=self.customer,
            status__in=['COMPLETED', 'CANCELLED']
        ).exclude(id=self.id).count()
        
        if completed_rentals_count == 0:
            return Decimal('0.00'), {
                'base_deposit': Decimal('0.00'),
                'vehicle_value': getattr(self.vehicle, 'vehicle_value', Decimal('100000.00')),
                'rental_days': self.rental_days,
                'duration_factor': Decimal('1.00'),
                'credit_score': getattr(self.customer, 'credit_score', 100),
                'credit_discount': Decimal('1.00'),
                'final_deposit': Decimal('0.00'),
                'reason': '首次租车用户享受免押金优惠'
            }
        
        # 获取车辆价值（如果没有vehicle_value字段，使用日租金*365作为估算）
        vehicle_value = getattr(self.vehicle, 'vehicle_value', None)
        if vehicle_value is None:
            vehicle_value = self.vehicle.daily_rate * Decimal('365')  # 估算车辆价值
        
        # 1. 计算基础押金（车辆价值的3%，更符合实际）
        base_deposit_rate = Decimal('0.03')
        base_deposit = vehicle_value * base_deposit_rate
        
        # 2. 租赁时长系数（0-30天，每天增加1%，最多30%）
        rental_days = self.rental_days
        capped_days = min(rental_days, 30)
        duration_factor = Decimal('1.00') + (Decimal(str(capped_days)) - Decimal('1')) * Decimal('0.01')
        
        # 3. 获取客户信用评分（0-100，初始100）
        credit_score = getattr(self.customer, 'credit_score', 100)
        credit_score = max(0, min(100, credit_score))  # 限制0-100
        
        # 4. 信用系数（评分越高，系数越小，押金越少）
        # 公式：2 - (评分/100)  ->  评分98分=1.02x, 评分100分=1.0x, 评刉50分=1.5x, 评刅0分=2.0x
        credit_discount = Decimal(str(credit_score)) / Decimal('100')
        credit_factor = Decimal('2.00') - credit_discount
        
        # 5. 计算最终押金
        final_deposit = base_deposit * duration_factor * credit_factor
        
        # 6. 设置押金上下限
        min_deposit = self.vehicle.daily_rate * Decimal('3')  # 最少为3天租金
        max_deposit = vehicle_value * Decimal('0.15')  # 最多为车辆价值的15%
        
        final_deposit = max(min_deposit, min(final_deposit, max_deposit))
        
        # 返回计算结果和明细
        details = {
            'base_deposit': base_deposit.quantize(Decimal('0.01')),
            'vehicle_value': vehicle_value.quantize(Decimal('0.01')),
            'base_deposit_rate': float(base_deposit_rate),
            'rental_days': rental_days,
            'duration_factor': duration_factor.quantize(Decimal('0.01')),
            'credit_score': credit_score,
            'credit_discount': credit_discount.quantize(Decimal('0.01')),
            'credit_factor': credit_factor.quantize(Decimal('0.01')),
            'final_deposit': final_deposit.quantize(Decimal('0.01')),
            'min_deposit': min_deposit.quantize(Decimal('0.01')),
            'max_deposit': max_deposit.quantize(Decimal('0.01')),
        }
        
        return final_deposit.quantize(Decimal('0.01')), details
    
    def calculate_order_total(self):
        """计算订单总额（基础租金 + 押金 + 异地费用 + 超时费用）"""
        base_amount = self.total_amount or Decimal('0.00')
        deposit_amount = self.deposit or Decimal('0.00')
        cross_location_fee = self.cross_location_fee or Decimal('0.00')
        overdue_fee = self.overdue_fee or Decimal('0.00')
        if not self.is_cross_location_return:
            cross_location_fee = Decimal('0.00')
        return base_amount + deposit_amount + cross_location_fee + overdue_fee
    
    def refresh_financials(self, save=True):
        """根据支付记录刷新累计支付/退款信息"""
        from accounts.models import Payment  # 避免循环导入
        paid_total = Payment.objects.filter(
            rental=self,
            status='PAID',
            transaction_type='CHARGE'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        refunded_total = Payment.objects.filter(
            rental=self,
            status='REFUNDED',
            transaction_type='REFUND'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        self.amount_paid = paid_total
        self.amount_refunded = refunded_total
        
        # 根据支付情况更新结算状态
        order_total = self.calculate_order_total()
        if self.status == 'COMPLETED' and order_total <= paid_total:
            self.settlement_status = 'SETTLED'
            if not self.settled_at:
                self.settled_at = timezone.now()
        elif paid_total > Decimal('0.00'):
            self.settlement_status = 'PARTIAL'
        else:
            self.settlement_status = 'UNSETTLED'
            self.settled_at = None
        
        if save:
            self.save(update_fields=[
                'amount_paid',
                'amount_refunded',
                'settlement_status',
                'settled_at',
                'updated_at'
            ])
    
    def refund_deposit(self, user=None):
        """
        退还押金
        如果订单有押金且未退还，创建退款记录
        返回：(是否已退款, 退款金额)
        """
        from accounts.models import Payment  # 避免循环导入
        from django.db.models import Sum
        
        deposit_amount = self.deposit or Decimal('0.00')
        if deposit_amount <= Decimal('0.00'):
            return False, Decimal('0.00')
        
        # 检查已退还的押金总额
        refunded_amount = Payment.objects.filter(
            rental=self,
            transaction_type='REFUND',
            status='REFUNDED'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # 计算可退还金额（押金减去已退还金额）
        refundable = deposit_amount - refunded_amount
        
        if refundable <= Decimal('0.00'):
            return False, Decimal('0.00')
        
        # 获取退款用户
        refund_user = user
        if not refund_user:
            # 优先使用支付记录中的用户
            payment_user = Payment.objects.filter(
                rental=self,
                transaction_type='CHARGE',
                status='PAID'
            ).order_by('created_at').first()
            refund_user = payment_user.user if payment_user else None
            # 如果没有支付记录，使用客户关联的用户
            if not refund_user and self.customer and self.customer.user:
                refund_user = self.customer.user
        
        if not refund_user:
            return False, Decimal('0.00')
        
        # 创建退款记录
        Payment.objects.create(
            rental=self,
            user=refund_user,
            amount=refundable,
            payment_method='BANK',
            transaction_type='REFUND',
            status='REFUNDED',
            description='订单完成，押金自动退还',
            paid_at=timezone.now(),
            transaction_id=f'REF{int(timezone.now().timestamp())}'
        )
        
        # 刷新财务信息
        self.refresh_financials()
        
        return True, refundable
    
    @property
    def outstanding_amount(self):
        """计算仍需支付的金额（不考虑退款，用于判断是否欠费）"""
        order_total = self.calculate_order_total()
        remaining = order_total - self.amount_paid
        return remaining if remaining > Decimal('0.00') else Decimal('0.00')
