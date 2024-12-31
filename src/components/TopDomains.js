import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';

function TopDomains({ data }) {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-6">Top Email Domains</h2>
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="domain" 
              angle={45} 
              textAnchor="start" 
              height={70}
              interval={0}
              tick={{ fontSize: 12 }}
            />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#2563EB" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default TopDomains;
