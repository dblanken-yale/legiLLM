import React from 'react';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon?: React.ReactNode;
  subtitle?: string;
}

export const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, subtitle }) => {
  return (
    <div className="stats-card">
      <div className="stats-card-header">
        {icon && <div className="stats-card-icon">{icon}</div>}
        <h3 className="stats-card-title">{title}</h3>
      </div>
      <div className="stats-card-value">{value}</div>
      {subtitle && <div className="stats-card-subtitle">{subtitle}</div>}
    </div>
  );
};
