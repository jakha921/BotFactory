"""
Views for analytics app.
Dashboard statistics and analytics endpoints using new analytics models.
"""
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import timedelta
from typing import Dict, List, Any
import logging

from apps.bots.models import Bot
from apps.chat.models import ChatSession, ChatMessage
from apps.telegram.models import TelegramUser
from apps.analytics.models import BotAnalytics, MessageEvent, TokenUsage, UserRetention


@method_decorator(cache_page(60 * 5), name='dispatch')  # Cache for 5 minutes
class DashboardStatsView(views.APIView):
    """
    Dashboard statistics endpoint using BotAnalytics model.
    Cached for 5 minutes to reduce database load.
    
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
        start_date = (now - time_range).date()
        
        # Get user's bots (only need IDs for filtering)
        user_bots = Bot.objects.filter(owner=request.user).only('id')
        bot_ids = list(user_bots.values_list('id', flat=True))
        
        # Aggregate stats from BotAnalytics
        analytics = BotAnalytics.objects.filter(
            bot_id__in=bot_ids,
            date__gte=start_date
        ).aggregate(
            total_users=Sum('unique_users'),
            total_messages=Sum('messages_sent'),
            avg_response=Avg('avg_response_time_ms'),
            total_tokens=Sum('tokens_used'),
            positive_feedback=Sum('positive_feedback'),
            negative_feedback=Sum('negative_feedback')
        )
        
        # Calculate trends (compare with previous period)
        previous_start = start_date - time_range
        previous_analytics = BotAnalytics.objects.filter(
            bot_id__in=bot_ids,
            date__gte=previous_start,
            date__lt=start_date
        ).aggregate(
            prev_users=Sum('unique_users'),
            prev_messages=Sum('messages_sent')
        )
        
        # Calculate trend percentages
        user_trend = self._calculate_trend(
            analytics['total_users'] or 0,
            previous_analytics['prev_users'] or 0
        )
        message_trend = self._calculate_trend(
            analytics['total_messages'] or 0,
            previous_analytics['prev_messages'] or 0
        )
        
        # Format stats for frontend
        stats = [
            {
                'title': 'Active Users',
                'value': analytics['total_users'] or 0,
                'trend': abs(user_trend),
                'trendDirection': 'up' if user_trend > 0 else 'down',
                'icon': 'users',
                'color': 'indigo',
            },
            {
                'title': 'Total Messages',
                'value': analytics['total_messages'] or 0,
                'trend': abs(message_trend),
                'trendDirection': 'up' if message_trend > 0 else 'down',
                'icon': 'message-circle',
                'color': 'green',
            },
            {
                'title': 'Avg Response Time',
                'value': f"{(analytics['avg_response'] or 0) / 1000:.2f}s",
                'trend': 0,
                'trendDirection': 'neutral',
                'icon': 'clock',
                'color': 'blue',
            },
            {
                'title': 'Token Usage',
                'value': f"{analytics['total_tokens'] or 0:,}",
                'trend': 0,
                'trendDirection': 'up',
                'icon': 'zap',
                'color': 'amber',
            },
        ]
        
        return Response(stats, status=status.HTTP_200_OK)
    
    def _calculate_trend(self, current: int, previous: int) -> int:
        """Calculate percentage change."""
        if previous == 0:
            return 100 if current > 0 else 0
        return int(((current - previous) / previous) * 100)


class ChartDataView(views.APIView):
    """
    Chart data endpoint using BotAnalytics.
    
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
        start_date = (now - time_range).date()
        
        # Get user's bots (only need IDs for filtering)
        user_bots = Bot.objects.filter(owner=request.user).only('id')
        bot_ids = list(user_bots.values_list('id', flat=True))
        
        # Get analytics grouped by date
        analytics = BotAnalytics.objects.filter(
            bot_id__in=bot_ids,
            date__gte=start_date
        ).values('date').annotate(
            messages=Sum('messages_sent'),
            users=Sum('unique_users')
        ).order_by('date')
        
        # Format data for frontend
        chart_data = [
            {
                'name': entry['date'].strftime('%b %d'),
                'messages': entry['messages'] or 0,
                'users': entry['users'] or 0
            }
            for entry in analytics
        ]
        
        if not chart_data:
            chart_data = [{'name': 'No data', 'messages': 0, 'users': 0}]
        
        return Response(chart_data, status=status.HTTP_200_OK)


class RecentActivityView(views.APIView):
    """
    Recent activity endpoint using MessageEvent.
    
    GET /api/v1/stats/activity/
    Returns recent activity items.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get recent activity for the current user."""
        # Get user's bots (only need IDs for filtering)
        user_bots = Bot.objects.filter(owner=request.user).only('id')
        bot_ids = list(user_bots.values_list('id', flat=True))
        
        # Get recent message events
        recent_events = MessageEvent.objects.filter(
            bot_id__in=bot_ids,
            event_type='sent'
        ).select_related('bot', 'telegram_user').order_by('-timestamp')[:10]
        
        # Format activity items
        activities = []
        for event in recent_events:
            user_name = event.telegram_user.first_name if event.telegram_user else 'Unknown'
            activities.append({
                'id': str(event.id),
                'title': f"Message sent to {user_name}",
                'description': f"Bot: {event.bot.name}, Response time: {event.response_time_ms}ms",
                'time': event.timestamp.isoformat(),
                'user': user_name,
                'icon': 'message-circle',
                'status': 'success' if event.response_time_ms < 2000 else 'warning'
            })
        
        return Response(activities, status=status.HTTP_200_OK)


class TokenUsageView(views.APIView):
    """
    Token usage statistics endpoint.
    
    GET /api/v1/stats/tokens/?period={period}
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get token usage statistics."""
        period = request.query_params.get('period', 'Last 7 days')
        
        now = timezone.now()
        period_map = {
            'Last 24 hours': timedelta(days=1),
            'Last 7 days': timedelta(days=7),
            'Last 30 days': timedelta(days=30),
            'Last 3 months': timedelta(days=90),
        }
        time_range = period_map.get(period, timedelta(days=7))
        start_date = (now - time_range).date()
        
        # Get user's bots (only need IDs for filtering)
        user_bots = Bot.objects.filter(owner=request.user).only('id')
        bot_ids = list(user_bots.values_list('id', flat=True))
        
        # Get token usage
        token_stats = TokenUsage.objects.filter(
            bot_id__in=bot_ids,
            date__gte=start_date
        ).aggregate(
            total_input=Sum('input_tokens'),
            total_output=Sum('output_tokens'),
            total_cost=Sum('estimated_cost_cents')
        )
        
        # Get daily breakdown
        daily_usage = TokenUsage.objects.filter(
            bot_id__in=bot_ids,
            date__gte=start_date
        ).values('date').annotate(
            tokens=Sum('total_tokens')
        ).order_by('date')
        
        return Response({
            'summary': {
                'input_tokens': token_stats['total_input'] or 0,
                'output_tokens': token_stats['total_output'] or 0,
                'total_tokens': (token_stats['total_input'] or 0) + (token_stats['total_output'] or 0),
                'estimated_cost': f"${(token_stats['total_cost'] or 0) / 100:.4f}"
            },
            'daily': [
                {
                    'date': entry['date'].strftime('%b %d'),
                    'tokens': entry['tokens'] or 0
                }
                for entry in daily_usage
            ]
        }, status=status.HTTP_200_OK)


class RetentionView(views.APIView):
    """
    User retention statistics endpoint.
    
    GET /api/v1/stats/retention/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get retention statistics."""
        # Get user's bots (only need IDs for filtering)
        user_bots = Bot.objects.filter(owner=request.user).only('id')
        bot_ids = list(user_bots.values_list('id', flat=True))
        
        # Get recent cohorts
        cohorts = UserRetention.objects.filter(
            bot_id__in=bot_ids
        ).order_by('-cohort_date')[:10]
        
        retention_data = [
            {
                'cohort': cohort.cohort_date.strftime('%b %d'),
                'total_users': cohort.total_users_in_cohort,
                'day_1': cohort.day_1_retention_rate,
                'day_7': cohort.day_7_retention_rate,
                'day_30': cohort.day_30_retention_rate,
            }
            for cohort in cohorts
        ]
        
        return Response(retention_data, status=status.HTTP_200_OK)
