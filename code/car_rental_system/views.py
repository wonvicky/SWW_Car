"""  
租车管理系统 - 全局视图函数
包含仪表盘、首页重定向、错误页面和评论管理视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import json

from vehicles.models import Vehicle
from customers.models import Customer
from rentals.models import Rental
from accounts.models import Review


def home_redirect(request):
    """
    智能首页重定向视图
    - 未登录用户：跳转到登录界面
    - 已登录管理员：跳转到管理员仪表板
    - 已登录普通用户：跳转到用户主页
    """
    if not request.user.is_authenticated:
        # 未登录用户跳转到登录页面
        return redirect('accounts:login')
    
    # 已登录用户根据身份跳转
    if request.user.is_staff:
        # 管理员跳转到仪表板
        return redirect('dashboard')
    else:
        # 普通用户跳转到用户主页
        return redirect('accounts:home')


@login_required(login_url='/accounts/login/')
def dashboard(request):
    """
    管理员仪表板视图
    显示系统关键统计数据和最近活动
    只有管理员可以访问
    """
    # 检查管理员权限
    if not request.user.is_staff:
        messages.error(request, '访问被拒绝：您没有管理员权限。')
        return redirect('accounts:home')  # 普通用户跳转到用户主页
    
    # 获取统计数据
    today = date.today()
    
    # 车辆统计
    total_vehicles = Vehicle.objects.count()
    available_vehicles = Vehicle.objects.filter(status='AVAILABLE').count()
    rented_vehicles = Vehicle.objects.filter(status='RENTED').count()
    maintenance_vehicles = Vehicle.objects.filter(status='MAINTENANCE').count()
    
    # 客户统计
    total_customers = Customer.objects.count()
    vip_customers = Customer.objects.filter(member_level='VIP').count()
    regular_customers = total_customers - vip_customers
    
    # 订单统计
    total_rentals = Rental.objects.count()
    ongoing_rentals = Rental.objects.filter(status='ONGOING').count()
    pending_rentals = Rental.objects.filter(status='PENDING').count()
    overdue_rentals = Rental.objects.filter(status='OVERDUE').count()
    completed_rentals = Rental.objects.filter(status='COMPLETED').count()
    active_rentals = ongoing_rentals + pending_rentals
    
    # 财务统计（本月、今日、总收入）
    month_start = today.replace(day=1)
    month_revenue = Rental.objects.filter(
        created_at__gte=month_start,
        status='COMPLETED'
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    today_revenue = Rental.objects.filter(
        created_at__date=today,
        status='COMPLETED'
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    total_revenue = Rental.objects.filter(
        status='COMPLETED'
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    # 本周新增订单
    week_start = today - timedelta(days=today.weekday())
    week_new_rentals = Rental.objects.filter(created_at__gte=week_start).count()
    
    # 最近活动（最近5条订单）
    recent_rentals = Rental.objects.select_related(
        'customer', 'vehicle'
    ).order_by('-created_at')[:5]
    
    # 车辆状态列表
    vehicle_status = Vehicle.objects.all()[:10]
    
    # 近6个月收入趋势（用于图表）
    monthly_revenue_data = []
    monthly_labels = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=i*30)
        month_start_calc = month_date.replace(day=1)
        if i == 0:
            month_end = today
        else:
            next_month = month_start_calc.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day)
        
        month_total = Rental.objects.filter(
            created_at__gte=month_start_calc,
            created_at__lte=month_end,
            status='COMPLETED'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        monthly_revenue_data.append(float(month_total))
        monthly_labels.append(month_start_calc.strftime('%Y-%m'))
    
    context = {
        # 车辆统计（匹配模板格式）
        'vehicle_stats': {
            'total': total_vehicles,
            'available': available_vehicles,
            'rented': rented_vehicles,
            'maintenance': maintenance_vehicles,
        },
        
        # 客户统计（匹配模板格式）
        'customer_stats': {
            'total': total_customers,
            'vip': vip_customers,
            'regular': regular_customers,
        },
        
        # 订单统计（匹配模板格式）
        'rental_stats': {
            'total': total_rentals,
            'active': active_rentals,
            'ongoing': ongoing_rentals,
            'pending': pending_rentals,
            'completed': completed_rentals,
            'overdue': overdue_rentals,
        },
        
        # 财务统计（匹配模板格式）
        'revenue_stats': {
            'total': total_revenue,
            'monthly': month_revenue,
            'today': today_revenue,
        },
        
        # 活动数据
        'recent_rentals': recent_rentals,
        'vehicle_status': vehicle_status,
        
        # 图表数据
        'monthly_revenue_data': json.dumps(monthly_revenue_data),
        'monthly_labels': json.dumps(monthly_labels),
    }
    
    return render(request, 'dashboard.html', context)


# 错误处理视图
def page_not_found(request, exception):
    """404 错误页面"""
    return render(request, 'page_not_found.html', status=404)


def server_error(request):
    """500 错误页面"""
    return render(request, 'server_error.html', status=500)


def permission_denied(request, exception):
    """403 错误页面"""
    return render(request, 'permission_denied.html', status=403)


# 评论管理视图
@login_required
def review_list_view(request):
    """评论列表视图"""
    if not request.user.is_staff:
        messages.error(request, '访问被拒绝：您没有管理员权限。')
        return redirect('accounts:home')
    
    reviews = Review.objects.select_related(
        'rental__customer', 'rental__vehicle'
    ).order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        reviews = reviews.filter(
            Q(rental__customer__name__icontains=search_query) |
            Q(rental__vehicle__license_plate__icontains=search_query) |
            Q(comment__icontains=search_query)
        )
    
    context = {
        'reviews': reviews,
        'search_query': search_query,
    }
    
    return render(request, 'reviews/review_list.html', context)


@login_required
def review_edit_view(request, pk):
    """编辑评论视图（管理员）"""
    if not request.user.is_staff:
        messages.error(request, '访问被拒绝：您没有管理员权限。')
        return redirect('accounts:home')
    
    review = get_object_or_404(Review, pk=pk)
    
    if request.method == 'POST':
        # 管理员可以修改评论的可见性
        is_visible = request.POST.get('is_visible') == 'on'
        review.is_visible = is_visible
        review.save()
        
        messages.success(request, '评论状态已更新。')
        return redirect('review_list')
    
    context = {
        'review': review,
    }
    
    return render(request, 'reviews/review_edit.html', context)


@login_required
def review_delete_view(request, pk):
    """删除评论视图（管理员）"""
    if not request.user.is_staff:
        messages.error(request, '访问被拒绝：您没有管理员权限。')
        return redirect('accounts:home')
    
    review = get_object_or_404(Review, pk=pk)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, '评论已删除。')
        return redirect('review_list')
    
    # GET 请求返回确认删除页面
    return redirect('review_list')
