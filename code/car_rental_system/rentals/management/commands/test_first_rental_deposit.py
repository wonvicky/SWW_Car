"""
测试首次租车免押金功能
"""

from django.core.management.base import BaseCommand
from customers.models import Customer
from vehicles.models import Vehicle
from rentals.models import Rental
from datetime import datetime, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = '测试首次租车免押金功能'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('测试首次租车免押金功能')
        self.stdout.write('=' * 60)
        self.stdout.write('')
        
        # 查找一个普通客户（非VIP）
        customer = Customer.objects.filter(member_level='NORMAL').first()
        if not customer:
            self.stdout.write(self.style.ERROR('未找到普通客户，请先创建客户'))
            return
        
        # 查找一辆可用车辆
        vehicle = Vehicle.objects.filter(status='AVAILABLE').first()
        if not vehicle:
            self.stdout.write(self.style.ERROR('未找到可用车辆'))
            return
        
        # 统计该客户已完成的订单数
        completed_count = Rental.objects.filter(
            customer=customer,
            status__in=['COMPLETED', 'CANCELLED']
        ).count()
        
        self.stdout.write(f'客户信息：')
        self.stdout.write(f'  姓名: {customer.name}')
        self.stdout.write(f'  会员等级: {customer.get_member_level_display()}')
        self.stdout.write(f'  信用评分: {getattr(customer, "credit_score", 100)}')
        self.stdout.write(f'  已完成订单数: {completed_count}')
        self.stdout.write('')
        
        self.stdout.write(f'测试车辆：')
        self.stdout.write(f'  {vehicle.brand} {vehicle.model} ({vehicle.license_plate})')
        self.stdout.write(f'  日租金: ¥{vehicle.daily_rate}')
        self.stdout.write(f'  车辆价值: ¥{vehicle.vehicle_value}')
        self.stdout.write('')
        
        # 创建一个临时订单来测试押金计算
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=3)
        
        test_rental = Rental(
            customer=customer,
            vehicle=vehicle,
            start_date=start_date,
            end_date=end_date,
            total_amount=vehicle.daily_rate * 3,
            status='PENDING'
        )
        
        # 计算押金
        deposit, details = test_rental.calculate_dynamic_deposit()
        
        self.stdout.write('押金计算结果：')
        self.stdout.write(f'  租期: {test_rental.rental_days} 天')
        self.stdout.write(f'  计算押金: ¥{deposit}')
        
        if 'reason' in details:
            self.stdout.write(self.style.SUCCESS(f'  优惠原因: {details["reason"]}'))
        else:
            self.stdout.write(f'  基础押金: ¥{details.get("base_deposit", 0)}')
            self.stdout.write(f'  时长系数: {details.get("duration_factor", 1)}')
            self.stdout.write(f'  信用系数: {details.get("credit_factor", 1)}')
        
        self.stdout.write('')
        
        # 显示判断逻辑
        if completed_count == 0:
            self.stdout.write(self.style.SUCCESS('✓ 该客户是首次租车用户，享受免押金优惠！'))
        else:
            self.stdout.write(f'✓ 该客户已有 {completed_count} 个订单，需要缴纳押金')
        
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('测试说明：')
        self.stdout.write('  1. VIP会员：免押金')
        self.stdout.write('  2. 首次租车用户：免押金（新增功能）')
        self.stdout.write('  3. 其他用户：根据车辆价值、租期、信用评分计算押金')
        self.stdout.write('=' * 60)
