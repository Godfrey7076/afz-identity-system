# Add this import at the top
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Add these new authentication views


def admin_login_view(request):
    """Admin login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(
                request, 'Invalid credentials or insufficient permissions.')

    return render(request, 'login.html')


def admin_logout_view(request):
    """Admin logout view"""
    logout(request)
    return redirect('admin_login')

# Update the dashboard views to require login


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(
                request, 'Access denied. Staff permissions required.')
            return redirect('admin_login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get date ranges
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        # Dashboard statistics
        context.update({
            'total_users': CustomUser.objects.count(),
            'verified_users': CustomUser.objects.filter(is_verified=True).count(),
            'pending_verification': CustomUser.objects.filter(is_verified=False).count(),
            'today_logs': AccessLog.objects.filter(timestamp__date=today).count(),
            'weekly_logs': AccessLog.objects.filter(timestamp__date__gte=week_ago).count(),
            'successful_logins': AccessLog.objects.filter(
                verification_method='face',
                success=True
            ).count(),
            'failed_logins': AccessLog.objects.filter(
                verification_method='face',
                success=False
            ).count(),
            'total_visitors': Visitor.objects.count(),
            'active_visitors': Visitor.objects.filter(status='active').count(),
        })

        # Recent activity
        context['recent_activity'] = AccessLog.objects.select_related(
            'user').order_by('-timestamp')[:10]

        # User type breakdown
        context['user_types'] = CustomUser.objects.values('user_type').annotate(
            count=Count('user_type')
        )

        return context


@login_required
def user_management_view(request):
    """User management page"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff permissions required.')
        return redirect('admin_login')

    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'user_management.html', {'users': users})


@login_required
def visitor_management_view(request):
    """Visitor management page"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff permissions required.')
        return redirect('admin_login')

    visitors = Visitor.objects.all().order_by('-created_at')
    return render(request, 'visitor_management.html', {'visitors': visitors})
