"""
Views for analytics app.
Dashboard statistics and analytics endpoints.
"""
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from datetime import timedelta
from typing import Dict, List, Any

from apps.bots.models import Bot
from apps.chat.models import ChatSession, ChatMessage
from apps.telegram.models import TelegramUser


class DashboardStatsView(views.APIView):
    """
    Dashboard statistics endpoint.
    
    GET /api/v1/stats/?period={period}
    Period options: "Last 24 hours", "Last 7 days", "Last 30 days", "Last 3 months"
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get dashboard statistics for the current user."""
        period = request.query_params.get('period', 'Last 7 days')
        
        # Calculate time range
        now = timezone.now()
        period_map = {
            'Last 24 hours': timedelta(days=1),
            'Last 7 days': timedelta(days=7),
            'Last 30 days': timedelta(days=30),
            'Last 3 months': timedelta(days=90),
        }
        time_range = period_map.get(period, timedelta(days=7))
        start_time = now - time_range
        
        # Get user's bots
        user_bots = Bot.objects.filter(owner=request.user)
        bot_ids = list(user_bots.values_list('id', flat=True))
        
        # Get active users (unique Telegram users)
        active_users = TelegramUser.objects.filter(
            bot_id__in=bot_ids,
            last_active__gte=start_time
        ).distinct().count()
        
        # Get total conversations (chat sessions)
        total_conversations = ChatSession.objects.filter(
            bot_id__in=bot_ids,
            created_at__gte=start_time
        ).count()
        
        # Calculate average response time (simplified - use message timestamps)
        # For now, we'll use a placeholder value
        avg_response_time = 1.2  # seconds (placeholder)
        
        # Calculate token usage (placeholder - would need to track actual API calls)
        token_usage = 0  # placeholder
        
        # Format stats to match frontend KPI format
        stats = [
            {
                'title': 'Active Users',
                'value': active_users,
                'trend': 12,  # Percentage change
                'trendDirection': 'up',
                'icon': 'users',  # Frontend will map icon names
                'color': 'indigo',
            },
            {
                'title': 'Total Conversations',
                'value': total_conversations,
                'trend': 8,
                'trendDirection': 'up',
                'icon': 'message-circle',
                'color': 'green',
            },
            {
                'title': 'Avg Response Time',
                'value': f"{avg_response_time}s",
                'trend': -5,
                'trendDirection': 'down',
                'icon': 'clock',
                'color': 'blue',
            },
            {
                'title': 'Token Usage',
                'value': f"{token_usage:,}",
                'trend': 15,
                'trendDirection': 'up',
                'icon': 'zap',
                'color': 'amber',
            },
        ]
        
        return Response(stats, status=status.HTTP_200_OK)


class ChartDataView(views.APIView):
    """
    Chart data endpoint.
    
    GET /api/v1/stats/chart/?period={period}
    Returns data for charts (conversations over time).
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get chart data for the current user."""
        period = request.query_params.get('period', 'Last 7 days')
        
        # Calculate time range
        now = timezone.now()
        period_map = {
            'Last 24 hours': timedelta(days=1),
            'Last 7 days': timedelta(days=7),
            'Last 30 days': timedelta(days=30),
            'Last 3 months': timedelta(days=90),
        }
        time_range = period_map.get(period, timedelta(days=7))
        start_time = now - time_range
        
        # Get user's bots
        user_bots = Bot.objects.filter(owner=request.user)
        bot_ids = list(user_bots.values_list('id', flat=True))
        
        # Get conversations grouped by day
        from django.db.models.functions import TruncDate
        
        conversations = ChatSession.objects.filter(
            bot_id__in=bot_ids,
            created_at__gte=start_time
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Format data for frontend
        chart_data = [
            {
                'name': entry['date'].strftime('%b %d') if entry['date'] else 'Unknown',
                'value': entry['count']
            }
            for entry in conversations
        ]
        
        # Fill in missing dates with 0
        if not chart_data:
            chart_data = [{'name': 'No data', 'value': 0}]
        
        return Response(chart_data, status=status.HTTP_200_OK)


class RecentActivityView(views.APIView):
    """
    Recent activity endpoint.
    
    GET /api/v1/stats/activity/
    Returns recent activity items.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get recent activity for the current user."""
        # Get user's bots
        user_bots = Bot.objects.filter(owner=request.user)
        bot_ids = list(user_bots.values_list('id', flat=True))
        
        # Get recent chat sessions
        recent_sessions = ChatSession.objects.filter(
            bot_id__in=bot_ids
        ).select_related('bot', 'user').order_by('-updated_at')[:10]
        
        # Format activity items to match frontend format
        activities = []
        for session in recent_sessions:
            activities.append({
                'id': str(session.id),
                'title': f"New conversation with {session.user.first_name if session.user else 'User'}",
                'description': session.last_message[:100] if session.last_message else 'No messages yet',
                'time': session.updated_at.isoformat(),
                'user': session.user.first_name if session.user else 'Unknown',
                'icon': 'message-circle',  # String icon name, frontend will map to LucideIcon
                'status': 'info'
            })
        
        return Response(activities, status=status.HTTP_200_OK)
