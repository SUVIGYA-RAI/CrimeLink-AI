"""
Accounts app views.
Handles login, logout, registration, profile, and user management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import LoginForm, RegisterForm, ProfileUpdateForm
from .models import UserProfile


def login_view(request):
    """Handle user login."""
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                # Redirect to next page or dashboard
                next_url = request.GET.get('next', 'dashboard:home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


def register_view(request):
    """Handle new investigator registration."""
    # Only admins should register new users (or this page can be open for initial setup)
    # For now, we allow open registration but non-admins get 'investigator' role default
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}. You can now login.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    """Show and update the current user's profile."""
    # Get or create profile if it doesn't exist (defensive coding)
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            # Update User model fields
            request.user.first_name = form.cleaned_data.get('first_name', request.user.first_name)
            request.user.last_name = form.cleaned_data.get('last_name', request.user.last_name)
            request.user.email = form.cleaned_data.get('email', request.user.email)
            request.user.save()
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        # Pre-fill user data in the form
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = ProfileUpdateForm(instance=profile, initial=initial)

    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})


@login_required
def user_list_view(request):
    """Show all registered users. Admin only."""
    # Check if current user is admin
    try:
        if not request.user.profile.is_admin() and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to view this page.')
            return redirect('dashboard:home')
    except UserProfile.DoesNotExist:
        return redirect('dashboard:home')

    users = User.objects.all().select_related('profile').order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})
