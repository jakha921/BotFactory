"""
URLs for analytics app.
"""
from django.urls import path
from apps.analytics.views import (
    DashboardStatsView,
    ChartDataView,
    RecentActivityView,
)

app_name = 'analytics'

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('stats/chart/', ChartDataView.as_view(), name='chart-data'),
    path('stats/activity/', RecentActivityView.as_view(), name='recent-activity'),
]

