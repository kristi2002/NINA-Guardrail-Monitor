# OFH Dashboard Frontend

React-based frontend for the NINA Chatbot Monitoring Dashboard.

## Quick Start

```bash
npm install
npm run dev
```

Visit `http://localhost:3000`

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── MetricCard.jsx  # Dashboard metric cards
│   └── GuardrailChart.jsx  # Time-series charts
├── pages/              # Main pages
│   ├── Dashboard.jsx   # Main dashboard view
│   └── Analytics.jsx   # Analytics page
├── App.jsx             # Main app with routing
└── main.jsx            # Entry point
```

## Key Components

### MetricCard
Displays a single metric with icon, value, and trend indicator.

**Props:**
- `title`: Metric name
- `value`: Current value
- `icon`: Emoji icon
- `trend`: Percentage change (optional)
- `isAlert`: Highlight for critical metrics

### GuardrailChart
Line chart showing metrics over time using Recharts library.

**Props:**
- `data`: Array of time-series data points

### Dashboard
Main dashboard page that:
- Fetches metrics from backend API
- Displays metric cards
- Shows time-series chart
- Auto-refreshes every 30 seconds

## API Integration

The frontend communicates with the backend using Axios:

```javascript
import axios from 'axios'

// Fetch metrics
const response = await axios.get('/api/metrics')
```

The `/api` prefix is automatically proxied to `http://localhost:5000` (configured in `vite.config.js`).

## Styling

Each component has its own CSS file:
- `MetricCard.css`
- `Dashboard.css`
- `App.css`

Global styles are in `index.css`.

## Customization

### Change Colors
Edit the CSS files to customize the color scheme:
- Primary: `#667eea` (purple-blue)
- Accent: `#764ba2` (purple)
- Alert: `#ff6b6b` (red)
- Success: `#51cf66` (green)

### Add New Metrics
1. Add new `<MetricCard>` in `Dashboard.jsx`
2. Update backend to provide the data
3. Customize the card's appearance

### Add New Pages
1. Create new page in `src/pages/`
2. Add route in `App.jsx`
3. Add navigation link in navbar

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Learning Resources

### React Concepts Used
- **Hooks**: useState, useEffect
- **Components**: Functional components
- **Props**: Component data passing
- **Routing**: React Router DOM
- **API Calls**: Axios for HTTP requests

### Recommended Learning
1. React documentation: https://react.dev
2. Recharts docs: https://recharts.org
3. Axios docs: https://axios-http.com

## Troubleshooting

**"Failed to load metrics"**:
- Ensure backend is running on port 5000
- Check browser console for detailed errors

**Port 3000 already in use**:
- Change port in `vite.config.js`

**Chart not displaying**:
- Check that data is in correct format
- Verify Recharts is installed

