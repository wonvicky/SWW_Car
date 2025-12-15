#!/usr/bin/env python
"""创建测试数据"""
import os
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from customers.models import Customer
from vehicles.models import Vehicle
from rentals.models import Rental

# 清理现有数据(可选)
# Rental.objects.all().delete()
# Customer.objects.all().delete()
# Vehicle.objects.all().delete()

print("开始创建测试数据...")

# 1. 创建车辆
vehicles_data = [
    {"brand": "丰田", "model": "凯美瑞", "license_plate": "京A12345", "daily_rate": 200, "status": "AVAILABLE", "vehicle_type": "轿车", "color": "白色"},
    {"brand": "本田", "model": "雅阁", "license_plate": "京B23456", "daily_rate": 220, "status": "AVAILABLE", "vehicle_type": "轿车", "color": "黑色"},
    {"brand": "大众", "model": "帕萨特", "license_plate": "京C34567", "daily_rate": 230, "status": "AVAILABLE", "vehicle_type": "轿车", "color": "银色"},
    {"brand": "奥迪", "model": "A6L", "license_plate": "京D45678", "daily_rate": 400, "status": "AVAILABLE", "vehicle_type": "轿车", "color": "黑色"},
    {"brand": "宝马", "model": "5系", "license_plate": "京E56789", "daily_rate": 450, "status": "AVAILABLE", "vehicle_type": "轿车", "color": "白色"},
]

vehicles = []
for vdata in vehicles_data:
    vehicle, created = Vehicle.objects.get_or_create(
        license_plate=vdata["license_plate"],
        defaults={
            "brand": vdata["brand"],
            "model": vdata["model"],
            "daily_rate": vdata["daily_rate"],
            "status": vdata["status"],
            "vehicle_type": vdata["vehicle_type"],
            "color": vdata["color"],
        }
    )
    vehicles.append(vehicle)
    if created:
        print(f"创建车辆: {vehicle.brand} {vehicle.model} ({vehicle.license_plate})")

# 2. 创建客户
customers_data = [
    {
        "name": "张三",
        "phone": "13800138000",
        "id_card": "330381200505212613",
        "email": "zhangsan@example.com",
        "member_level": "VIP",
        "license_number": "330100202001015678",
        "license_type": "C",
    },
    {
        "name": "李四",
        "phone": "13800138001",
        "id_card": "110101199001011234",
        "email": "lisi@example.com",
        "member_level": "NORMAL",
        "license_number": "110100201501025432",
        "license_type": "C",
    },
    {
        "name": "王五",
        "phone": "13800138002",
        "id_card": "310101198512123456",
        "member_level": "NORMAL",
        "license_number": "310100201201018765",
        "license_type": "C",
    },
]

customers = []
for cdata in customers_data:
    customer, created = Customer.objects.get_or_create(
        phone=cdata["phone"],
        defaults=cdata
    )
    customers.append(customer)
    if created:
        print(f"创建客户: {customer.name} ({customer.phone})")

# 3. 为第一个客户创建多条租赁记录(用于测试分页和筛选)
if customers:
    test_customer = customers[0]
    print(f"\n为客户 {test_customer.name} 创建租赁记录...")
    
    rental_statuses = ['PENDING', 'ONGOING', 'COMPLETED', 'CANCELLED', 'OVERDUE']
    base_date = datetime.now()
    
    # 创建15条租赁记录
    for i in range(15):
        start_date = base_date - timedelta(days=60-i*3)
        end_date = start_date + timedelta(days=random.randint(2, 7))
        vehicle = random.choice(vehicles)
        status = random.choice(rental_statuses)
        
        # 根据租期计算金额
        days = (end_date - start_date).days
        total_amount = Decimal(str(days * vehicle.daily_rate))
        
        rental, created = Rental.objects.get_or_create(
            customer=test_customer,
            vehicle=vehicle,
            start_date=start_date.date(),
            end_date=end_date.date(),
            defaults={
                "status": status,
                "total_amount": total_amount,
                "deposit": Decimal("1000.00"),
                "pickup_location": "北京市朝阳区",
                "return_location": "北京市朝阳区",
            }
        )
        if created:
            print(f"  创建租赁记录 #{i+1}: {vehicle.brand} {vehicle.model}, 状态: {status}, 金额: ¥{total_amount}")
    
    # 为其他客户创建少量记录
    for customer in customers[1:]:
        for i in range(random.randint(1, 3)):
            start_date = base_date - timedelta(days=random.randint(10, 50))
            end_date = start_date + timedelta(days=random.randint(2, 5))
            vehicle = random.choice(vehicles)
            status = random.choice(['COMPLETED', 'ONGOING'])
            
            days = (end_date - start_date).days
            total_amount = Decimal(str(days * vehicle.daily_rate))
            
            Rental.objects.get_or_create(
                customer=customer,
                vehicle=vehicle,
                start_date=start_date.date(),
                end_date=end_date.date(),
                defaults={
                    "status": status,
                    "total_amount": total_amount,
                    "deposit": Decimal("1000.00"),
                    "pickup_location": "北京市朝阳区",
                    "return_location": "北京市朝阳区",
                }
            )

print("\n测试数据创建完成!")
print(f"总客户数: {Customer.objects.count()}")
print(f"总车辆数: {Vehicle.objects.count()}")
print(f"总租赁记录数: {Rental.objects.count()}")

# 显示测试客户信息
test_customer = customers[0]
print(f"\n主测试客户: {test_customer.name} (ID: {test_customer.id})")
print(f"联系电话: {test_customer.phone}")
print(f"身份证号: {test_customer.id_card}")
print(f"租赁记录数: {test_customer.rentals.count()}")

print("\n各状态租赁记录分布:")
for status_code, status_name in Rental.RENTAL_STATUS_CHOICES:
    count = test_customer.rentals.filter(status=status_code).count()
    print(f"  {status_name}: {count}条")

print(f"\n可以访问以下URL测试功能:")
print(f"  基础详情页: http://127.0.0.1:8000/customers/{test_customer.id}/")
print(f"  筛选预订中: http://127.0.0.1:8000/customers/{test_customer.id}/?status=PENDING")
print(f"  按金额排序: http://127.0.0.1:8000/customers/{test_customer.id}/?sort=-total_amount")
print(f"  分页测试: http://127.0.0.1:8000/customers/{test_customer.id}/?page=2&per_page=5")
