from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from .models import UserProfile, Review, Payment
from vehicles.models import Vehicle
from rentals.models import Rental
from datetime import date, timedelta
import re


class UserRegisterForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(
        label='邮箱',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入邮箱地址'
        })
    )
    username = forms.CharField(
        label='用户名',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入用户名'
        }),
        help_text='必填。150个字符以内。只能包含字母、数字和 @/./+/-/_ 字符。'
    )
    password1 = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入密码'
        }),
        help_text='至少8个字符，不能全是数字。'
    )
    password2 = forms.CharField(
        label='确认密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请再次输入密码'
        }),
        help_text='请再次输入密码以确认。'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('该邮箱已被注册，请使用其他邮箱。')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('用户名只能包含字母、数字和 @/./+/-/_ 字符。')
        if len(username) < 3:
            raise ValidationError('用户名至少需要3个字符。')
        return username


class UserLoginForm(AuthenticationForm):
    """用户登录表单"""
    username = forms.CharField(
        label='用户名',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入用户名',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入密码'
        })
    )
    remember_me = forms.BooleanField(
        label='记住我',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class PasswordResetRequestForm(forms.Form):
    """密码重置请求表单"""
    email = forms.EmailField(
        label='邮箱',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入注册邮箱'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError('该邮箱未注册。')
        return email


class PasswordResetForm(forms.Form):
    """密码重置表单"""
    new_password1 = forms.CharField(
        label='新密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入新密码'
        }),
        help_text='至少8个字符，不能全是数字。'
    )
    new_password2 = forms.CharField(
        label='确认新密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请再次输入新密码'
        })
    )
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('两次输入的密码不一致。')
        password_validation.validate_password(password2)
        return password2


class UserProfileForm(forms.ModelForm):
    """用户资料表单"""
    first_name = forms.CharField(
        label='名',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入名'
        })
    )
    last_name = forms.CharField(
        label='姓',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入姓'
        })
    )
    email = forms.EmailField(
        label='邮箱',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入邮箱'
        })
    )
    phone = forms.CharField(
        label='手机号',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入手机号'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'avatar']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入手机号'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            if hasattr(self.user, 'profile'):
                self.fields['phone'].initial = self.user.profile.phone
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.user and User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('该邮箱已被其他用户使用。')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^1[3-9]\d{9}$', phone):
            raise ValidationError('请输入有效的手机号码。')
        return phone
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            self.user.email = self.cleaned_data.get('email', '')
            if commit:
                self.user.save()
                profile.user = self.user
                profile.save()
        return profile


class PasswordChangeFormCustom(PasswordChangeForm):
    """密码修改表单"""
    old_password = forms.CharField(
        label='旧密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入旧密码'
        })
    )
    new_password1 = forms.CharField(
        label='新密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入新密码'
        }),
        help_text='至少8个字符，不能全是数字。'
    )
    new_password2 = forms.CharField(
        label='确认新密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请再次输入新密码'
        })
    )


class ReviewForm(forms.ModelForm):
    """评价表单"""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '请输入评价内容（可选）',
                'maxlength': 1000
            }),
        }
        labels = {
            'rating': '评分',
            'comment': '评价内容',
        }
        help_texts = {
            'rating': '请选择1-5星评分',
            'comment': '评价内容（可选，最多1000字）',
        }


class ReviewAdminForm(forms.ModelForm):
    """后台管理员编辑评价表单"""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '请输入或更新评价内容',
                'maxlength': 1000
            }),
        }
        labels = {
            'rating': '评分',
            'comment': '评价内容',
        }

class PaymentForm(forms.ModelForm):
    """支付表单"""
    class Meta:
        model = Payment
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
        }
        labels = {
            'payment_method': '支付方式',
        }


class VehicleCompareForm(forms.Form):
    """车辆对比表单"""
    vehicles = forms.ModelMultipleChoiceField(
        queryset=Vehicle.objects.filter(status='AVAILABLE'),
        label='选择要对比的车辆',
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text='最多选择3辆车进行对比'
    )
    
    def clean_vehicles(self):
        vehicles = self.cleaned_data.get('vehicles')
        if len(vehicles) > 3:
            raise ValidationError('最多只能选择3辆车进行对比。')
        if len(vehicles) < 2:
            raise ValidationError('至少需要选择2辆车进行对比。')
        return vehicles


class StudentCardDepositForm(forms.Form):
    """学生卡抵押信息表单"""
    student_card_image = forms.ImageField(
        label='学生卡照片',
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='请上传学生卡正面清晰照片，支持JPG/PNG格式，大小不超过5MB'
    )
    student_id = forms.CharField(
        label='学号',
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入学号'
        }),
        help_text='请输入你的学号'
    )
    student_name = forms.CharField(
        label='姓名',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入姓名'
        }),
        help_text='请输入与学生卡上一致的姓名'
    )
    student_school = forms.ChoiceField(
        label='所属学校',
        required=True,
        choices=[
            ('', '请选择学校'),
            ('浙江工商大学', '浙江工商大学'),
            ('杭州电子科技大学', '杭州电子科技大学'),
            ('中国计量大学', '中国计量大学'),
            ('浙江财经大学', '浙江财经大学'),
            ('浙江传媒学院', '浙江传媒学院'),
            ('其他', '其他')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text='选择你的学校'
    )
    student_major = forms.CharField(
        label='院系专业',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入院系专业（选填）'
        }),
        help_text='选填，例如：计算机学院软件工程'
    )
    
    def clean_student_card_image(self):
        image = self.cleaned_data.get('student_card_image')
        if image:
            # 验证文件大小（5MB）
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('学生卡照片大小不能超过5MB')
            # 验证文件格式
            if not image.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValidationError('仅支持JPG、PNG格式的图片')
        return image
    
    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if student_id:
            # 验证学号格式（一般为8-20位数字或字母数字组合）
            if not re.match(r'^[A-Za-z0-9]{6,20}$', student_id):
                raise ValidationError('学号格式不正确，应为6-20位的数字或字母')
        return student_id
