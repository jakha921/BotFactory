/**
 * Icon mapper utility for mapping icon names from API to Lucide React icons
 */
import {
  Users,
  MessageCircle,
  Clock,
  Zap,
  Activity,
  Bot as BotIcon,
  User,
  FileText,
  Settings,
  BarChart3,
  TrendingUp,
  TrendingDown,
  LucideIcon,
} from 'lucide-react';

const iconMap: Record<string, LucideIcon> = {
  users: Users,
  'message-circle': MessageCircle,
  clock: Clock,
  zap: Zap,
  activity: Activity,
  bot: BotIcon,
  user: User,
  'file-text': FileText,
  settings: Settings,
  'bar-chart-3': BarChart3,
  'trending-up': TrendingUp,
  'trending-down': TrendingDown,
};

/**
 * Get Lucide icon component from icon name string
 */
export const getIcon = (iconName: string): LucideIcon => {
  return iconMap[iconName.toLowerCase()] || Activity; // Default to Activity if not found
};

/**
 * Map KPI data from API format to frontend format
 */
import { KPI } from '../types';

export const mapKPIData = (apiData: any): KPI => {
  return {
    title: apiData.title || apiData.label || '',
    value: apiData.value || 0,
    trend: typeof apiData.trend === 'number' ? apiData.trend : 0,
    trendDirection: apiData.trendDirection || 'neutral',
    icon: getIcon(apiData.icon || 'activity'),
    color: apiData.color || 'indigo',
  };
};

