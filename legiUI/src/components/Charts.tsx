import React from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ChartData {
  name: string;
  value: number;
  [key: string]: string | number;
}

interface ChartsProps {
  data: Record<string, number>;
  title: string;
  type?: 'bar' | 'pie';
}

// Yale color palette for charts
const COLORS = [
  '#00356b', // Yale Blue
  '#286dc0', // Medium Blue
  '#375597', // Royal Blue
  '#3E75AD', // Horizon
  '#346F6A', // Oceanic
  '#779FB1', // Shale
  '#D6A760', // Peach
  '#63aaff', // Light Blue
  '#FF6654', // Coral
];

export const Chart: React.FC<ChartsProps> = ({ data, title, type = 'bar' }) => {
  const chartData: ChartData[] = Object.entries(data)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  if (type === 'pie') {
    // Custom label that renders percentage only for cleaner display
    const renderLabel = (entry: any) => {
      const percent = (entry.percent * 100).toFixed(0);
      return `${percent}%`;
    };

    return (
      <div className="chart-container">
        <h3 className="chart-title">{title}</h3>
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="45%"
              labelLine={true}
              label={renderLabel}
              outerRadius={60}
              innerRadius={0}
              fill="#8884d8"
              dataKey="value"
              paddingAngle={2}
            >
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string) => [value, name]}
            />
            <Legend
              verticalAlign="bottom"
              height={80}
              formatter={(value: string) => <span style={{ fontSize: '0.875rem' }}>{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h3 className="chart-title">{title}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} margin={{ bottom: 100, left: 10, right: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={120}
            interval={0}
            tick={{ fontSize: 11, fill: 'var(--text-primary)' }}
          />
          <YAxis tick={{ fontSize: 12, fill: 'var(--text-primary)' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--background)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
            }}
          />
          <Bar dataKey="value" fill="#00356b" name="Bills" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
