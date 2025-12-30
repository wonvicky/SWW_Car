"""
调整车辆租金和押金脚本
将车辆的日租金和车辆价值调整到更符合现实的水平
"""

from django.core.management.base import BaseCommand
from vehicles.models import Vehicle
from decimal import Decimal
from django.core.cache import cache


class Command(BaseCommand):
    help = '调整车辆租金和押金到合理水平'

    def handle(self, *args, **options):
        self.stdout.write('开始调整车辆租金和车辆价值...')
        
        # 定义不同车型的价格范围（根据现实市场定价）
        pricing_rules = {
            # 经济型轿车
            ('经济型', '轿车'): {
                'daily_rate_range': (80, 150),
                'vehicle_value_range': (60000, 120000)
            },
            # 中档轿车
            ('中档', '轿车'): {
                'daily_rate_range': (150, 300),
                'vehicle_value_range': (120000, 250000)
            },
            # 豪华轿车
            ('豪华', '轿车'): {
                'daily_rate_range': (400, 800),
                'vehicle_value_range': (400000, 1000000)
            },
            # SUV
            ('经济型', 'SUV'): {
                'daily_rate_range': (120, 200),
                'vehicle_value_range': (100000, 180000)
            },
            ('中档', 'SUV'): {
                'daily_rate_range': (200, 400),
                'vehicle_value_range': (180000, 350000)
            },
            ('豪华', 'SUV'): {
                'daily_rate_range': (500, 1000),
                'vehicle_value_range': (500000, 1500000)
            },
            # MPV
            ('经济型', 'MPV'): {
                'daily_rate_range': (150, 250),
                'vehicle_value_range': (120000, 200000)
            },
            ('中档', 'MPV'): {
                'daily_rate_range': (250, 450),
                'vehicle_value_range': (200000, 400000)
            },
            # 商务车
            ('经济型', '商务车'): {
                'daily_rate_range': (200, 350),
                'vehicle_value_range': (150000, 250000)
            },
            ('中档', '商务车'): {
                'daily_rate_range': (350, 600),
                'vehicle_value_range': (250000, 450000)
            },
            ('豪华', '商务车'): {
                'daily_rate_range': (600, 1000),
                'vehicle_value_range': (450000, 800000)
            },
            # 跑车
            ('经济型', '跑车'): {
                'daily_rate_range': (400, 600),
                'vehicle_value_range': (300000, 500000)
            },
            ('中档', '跑车'): {
                'daily_rate_range': (600, 1000),
                'vehicle_value_range': (500000, 800000)
            },
            ('豪华', '跑车'): {
                'daily_rate_range': (1000, 2000),
                'vehicle_value_range': (800000, 2000000)
            },
        }
        
        # 品牌等级分类（用于判断车辆档次）
        luxury_brands = ['宝马', 'BMW', '奔驰', 'Mercedes', '奥迪', 'Audi', '保时捷', 'Porsche', 
                        '雷克萨斯', 'Lexus', '凯迪拉克', 'Cadillac', '路虎', 'Land Rover']
        mid_brands = ['大众', 'Volkswagen', '丰田', 'Toyota', '本田', 'Honda', '日产', 'Nissan',
                     '别克', 'Buick', '福特', 'Ford', '马自达', 'Mazda', '现代', 'Hyundai']
        
        updated_count = 0
        
        for vehicle in Vehicle.objects.all():
            # 判断车辆档次
            if any(brand in vehicle.brand for brand in luxury_brands):
                tier = '豪华'
            elif any(brand in vehicle.brand for brand in mid_brands):
                tier = '中档'
            else:
                tier = '经济型'
            
            # 获取定价规则
            rule_key = (tier, vehicle.vehicle_type)
            if rule_key not in pricing_rules:
                # 如果没有精确匹配，使用默认规则
                if vehicle.vehicle_type == 'SUV':
                    rule_key = ('中档', 'SUV')
                elif vehicle.vehicle_type == 'MPV':
                    rule_key = ('经济型', 'MPV')
                elif vehicle.vehicle_type == '商务车':
                    rule_key = ('中档', '商务车')
                elif vehicle.vehicle_type == '跑车':
                    rule_key = ('中档', '跑车')
                else:
                    rule_key = ('经济型', '轿车')
            
            if rule_key in pricing_rules:
                rules = pricing_rules[rule_key]
                
                # 根据当前租金调整（保持相对关系）
                current_rate = float(vehicle.daily_rate)
                min_rate, max_rate = rules['daily_rate_range']
                
                # 如果当前租金过高，调整到合理范围的中等偏上水平
                if current_rate > max_rate:
                    new_rate = Decimal(str(int((min_rate + max_rate) * 0.6)))
                elif current_rate < min_rate:
                    new_rate = Decimal(str(int((min_rate + max_rate) * 0.4)))
                else:
                    new_rate = vehicle.daily_rate
                
                # 调整车辆价值
                min_value, max_value = rules['vehicle_value_range']
                current_value = float(vehicle.vehicle_value)
                
                if current_value > max_value:
                    new_value = Decimal(str(int((min_value + max_value) * 0.6)))
                elif current_value < min_value:
                    new_value = Decimal(str(int((min_value + max_value) * 0.5)))
                else:
                    new_value = vehicle.vehicle_value
                
                # 更新车辆信息
                old_rate = vehicle.daily_rate
                old_value = vehicle.vehicle_value
                
                vehicle.daily_rate = new_rate
                vehicle.vehicle_value = new_value
                vehicle.save()
                
                if old_rate != new_rate or old_value != new_value:
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {vehicle.brand} {vehicle.model} ({vehicle.license_plate})\n'
                            f'  档次: {tier} | 类型: {vehicle.vehicle_type}\n'
                            f'  日租金: ¥{old_rate} → ¥{new_rate}\n'
                            f'  车辆价值: ¥{old_value} → ¥{new_value}\n'
                        )
                    )
        
        # 清除相关缓存
        cache.delete('user_vehicle_brands_list')
        cache.delete('user_vehicle_types_list')
        cache.delete('user_vehicle_seats_list')
        cache.delete('popular_vehicles')
        # 清除所有用户的推荐缓存
        cache.delete_pattern('user_recommendations_*')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n调整完成！共更新 {updated_count} 辆车辆的定价信息。'
            )
        )
        self.stdout.write(self.style.SUCCESS('✓ 已清除相关缓存'))
        
        # 显示调整后的价格范围统计
        self.stdout.write('\n当前价格统计：')
        for vehicle_type in ['轿车', 'SUV', 'MPV']:
            vehicles = Vehicle.objects.filter(vehicle_type=vehicle_type)
            if vehicles.exists():
                rates = [float(v.daily_rate) for v in vehicles]
                self.stdout.write(
                    f'{vehicle_type}: 日租金范围 ¥{min(rates):.0f} - ¥{max(rates):.0f}'
                )
