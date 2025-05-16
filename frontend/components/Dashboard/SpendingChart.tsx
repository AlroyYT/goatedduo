// components/Dashboard/SpendingChart.tsx
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import React from 'react';

interface SpendingData {
  category: string;
  value: number;
}

interface SpendingChartProps {
  data: SpendingData[];
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7f50', '#a29bfe'];

const SpendingChart: React.FC<SpendingChartProps> = ({ data }) => {
  return (
    <div className="bg-white rounded shadow p-4">
      <h3 className="text-xl font-semibold mb-3">Spending Breakdown</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data || []}
            dataKey="value"
            nameKey="category"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label
          >
            {(data || []).map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SpendingChart;
