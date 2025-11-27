import React, { useEffect, useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Calendar, MoreHorizontal } from 'lucide-react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { cn, formatNumber } from '../utils';
import { api } from '../services/api';
import { KPI } from '../types';
import { useThemeStore } from '../store/useThemeStore';
import { AnimatePresence, motion } from 'framer-motion';

export const Dashboard: React.FC = () => {
  console.log('[Dashboard] Component rendered');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<KPI[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [activity, setActivity] = useState<any[]>([]);
  const [timeRange, setTimeRange] = useState('Last 7 days');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const { theme } = useThemeStore();
  console.log('[Dashboard] State initialized, loading:', loading);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [statsData, chart, acts] = await Promise.all([
          api.stats.dashboard(timeRange),
          api.stats.chart(timeRange),
          api.stats.activity(),
        ]);
        setStats(statsData);
        setChartData(chart);
        setActivity(acts);
      } catch (e) {
        console.error('Dashboard Load Error', e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [timeRange]); // Reload when timeRange changes

  const handleExport = () => {
    const headers = ['Title', 'Value', 'Trend'];
    const rows = stats.map((s) => [s.title, String(s.value), s.trend + '%']);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      headers.join(',') +
      '\n' +
      rows.map((e) => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'analytics_report.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const timeRanges = ['Last 24 hours', 'Last 7 days', 'Last 30 days', 'Last 3 months'];

  return (
    <div className="space-y-8 pb-8">
      {/* Welcome Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">
            Overview
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Here's what's happening with your bots today.
          </p>
        </div>
        <div className="flex gap-2 relative">
          <div className="relative">
            <Button
              variant="secondary"
              size="sm"
              icon={<Calendar className="w-4 h-4" />}
              onClick={() => setIsFilterOpen(!isFilterOpen)}
            >
              {timeRange}
            </Button>
            <AnimatePresence>
              {isFilterOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setIsFilterOpen(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 5 }}
                    className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-black/5 dark:border-white/5 z-20 overflow-hidden py-1"
                  >
                    {timeRanges.map((range) => (
                      <button
                        key={range}
                        onClick={() => {
                          setTimeRange(range);
                          setIsFilterOpen(false);
                        }}
                        className={cn(
                          'w-full text-left px-4 py-2 text-sm transition-colors',
                          timeRange === range
                            ? 'bg-primary/10 text-primary'
                            : 'text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5'
                        )}
                      >
                        {range}
                      </button>
                    ))}
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
          <Button variant="primary" size="sm" onClick={handleExport}>
            Export Report
          </Button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {loading
          ? // Skeleton Loader
            [1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-32" variant="default" />)
          : stats.map((stat, index) => {
              const Icon = stat.icon;
              const isPositive =
                (stat.trendDirection === 'up' && stat.title !== 'Avg. Response Time') ||
                (stat.trendDirection === 'down' && stat.title === 'Avg. Response Time');

              return (
                <Card
                  key={index}
                  className="relative overflow-hidden group border-black/5 dark:border-white/5"
                >
                  <CardContent className="p-6 relative z-10">
                    <div className="flex justify-between items-start mb-4">
                      <div
                        className={cn(
                          'p-2.5 rounded-xl transition-colors duration-300',
                          'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-300 group-hover:text-white',
                          stat.color === 'blue' && 'group-hover:bg-blue-500',
                          stat.color === 'indigo' && 'group-hover:bg-indigo-500',
                          stat.color === 'amber' && 'group-hover:bg-amber-500',
                          stat.color === 'green' && 'group-hover:bg-emerald-500'
                        )}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div
                        className={cn(
                          'flex items-center text-xs font-semibold rounded-full px-2 py-1 border',
                          isPositive
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20'
                            : 'bg-red-50 text-red-700 border-red-100 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20'
                        )}
                      >
                        {stat.trendDirection === 'up' ? (
                          <ArrowUpRight className="w-3 h-3 mr-1" />
                        ) : (
                          <ArrowDownRight className="w-3 h-3 mr-1" />
                        )}
                        {stat.trend}%
                      </div>
                    </div>
                    <div className="space-y-1">
                      <h3 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
                        {typeof stat.value === 'number' ? formatNumber(stat.value) : stat.value}
                      </h3>
                      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                        {stat.title}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 border-black/5 dark:border-white/5">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Engagement Overview</CardTitle>
              <CardDescription>Conversations vs Active Users</CardDescription>
            </div>
            <Button variant="icon" size="md">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full min-h-[300px]">
              {loading ? (
                <Skeleton className="w-full h-full" variant="rect" />
              ) : chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="var(--grid-color)"
                      className="stroke-black/5 dark:stroke-white/5"
                    />
                    <XAxis
                      dataKey="name"
                      axisLine={false}
                      tickLine={false}
                      tickMargin={10}
                      className="text-xs font-medium fill-gray-500 dark:fill-gray-400"
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tickMargin={10}
                      className="text-xs font-medium fill-gray-500 dark:fill-gray-400"
                      tickFormatter={(value) => (value >= 1000 ? `${value / 1000}k` : value)}
                    />
                    <Tooltip
                      contentStyle={{
                        borderRadius: '12px',
                        border:
                          theme === 'dark'
                            ? '1px solid rgba(255,255,255,0.1)'
                            : '1px solid rgba(0,0,0,0.05)',
                        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                        backgroundColor:
                          theme === 'dark' ? 'rgba(24, 24, 27, 0.9)' : 'rgba(255, 255, 255, 0.9)',
                        backdropFilter: 'blur(8px)',
                        padding: '12px',
                      }}
                      itemStyle={{
                        color: theme === 'dark' ? '#e4e4e7' : '#1f2937',
                        fontSize: '14px',
                        fontWeight: 500,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#6366f1"
                      strokeWidth={3}
                      fillOpacity={1}
                      fill="url(#colorValue)"
                      activeDot={{ r: 6, strokeWidth: 0 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                  No chart data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-black/5 dark:border-white/5">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest actions system-wide</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-16" variant="default" />
                ))}
              </div>
            ) : (
              <div className="space-y-0 relative">
                {activity.map((item, i) => {
                  const Icon = item.icon;
                  return (
                    <div key={item.id} className="flex gap-4 pb-6 relative last:pb-0">
                      {/* Connector Line - 1px subtle border */}
                      {i !== activity.length - 1 && (
                        <div className="absolute left-[15px] top-8 bottom-0 w-px bg-black/5 dark:bg-white/5" />
                      )}

                      <div
                        className={cn(
                          'w-8 h-8 rounded-full flex items-center justify-center shrink-0 border z-10 bg-white dark:bg-gray-900',
                          item.status === 'success' &&
                            'border-emerald-100 text-emerald-600 dark:border-emerald-900/50 dark:text-emerald-400',
                          item.status === 'warning' &&
                            'border-amber-100 text-amber-600 dark:border-amber-900/50 dark:text-amber-400',
                          item.status === 'info' &&
                            'border-blue-100 text-blue-600 dark:border-blue-900/50 dark:text-blue-400'
                        )}
                      >
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 pt-0.5">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {item.title}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-1">
                          {item.description}
                        </p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span className="text-[10px] font-medium text-gray-400 bg-gray-100 dark:bg-white/5 px-1.5 py-0.5 rounded">
                            {item.time}
                          </span>
                          <span className="text-[10px] text-gray-400">•</span>
                          <span className="text-[10px] text-gray-400">{item.user}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
