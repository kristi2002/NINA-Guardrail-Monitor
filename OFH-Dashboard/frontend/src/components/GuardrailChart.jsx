import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './GuardrailChart.css'

function GuardrailChart({ data }) {
  return (
    <div className="chart-container">
      <h3>Guardrail Performance Over Time</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="requests" 
            stroke="#667eea" 
            strokeWidth={2}
            name="Total Requests"
          />
          <Line 
            type="monotone" 
            dataKey="violations" 
            stroke="#ff6b6b" 
            strokeWidth={2}
            name="Violations"
          />
          <Line 
            type="monotone" 
            dataKey="success" 
            stroke="#51cf66" 
            strokeWidth={2}
            name="Successful"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default GuardrailChart

