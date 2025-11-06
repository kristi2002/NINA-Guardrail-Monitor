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
├── components/          # Domain-organized components
│   ├── conversations/   # Conversation domain components
│   │   ├── ConversationCard.jsx
│   │   ├── ConversationList.jsx
│   │   └── ...
│   ├── notifications/  # Notification domain components
│   │   ├── NotificationCenter.jsx
│   │   └── NotificationPreferences.jsx
│   ├── analytics/      # Analytics domain components
│   │   ├── AlertCard.jsx
│   │   ├── GuardrailChart.jsx
│   │   └── MetricCard.jsx
│   ├── ui/             # Reusable UI components
│   │   ├── CustomSelect.jsx
│   │   ├── DataTable.jsx
│   │   └── LoadingSkeleton.jsx
│   └── common/         # Shared/common components
│       ├── ErrorBoundary.jsx
│       ├── ProtectedRoute.jsx
│       └── UserProfile.jsx
├── pages/              # Main pages
│   ├── Dashboard.jsx   # Main dashboard view
│   └── Analytics.jsx   # Analytics page
├── services/           # Domain-organized services
│   ├── api/           # API services
│   └── notifications/ # Notification services
├── contexts/          # React contexts
├── styles/            # Global styles
├── translations/       # i18n files
├── utils/             # Utility functions
├── App.jsx            # Main app with routing
└── main.jsx           # Entry point
```

## Key Components

### Domain Organization

Components are organized by domain for better maintainability:

- **Conversations**: `components/conversations/` - Conversation-related components
- **Notifications**: `components/notifications/` - Notification-related components  
- **Analytics**: `components/analytics/` - Analytics and metrics components
- **UI**: `components/ui/` - Reusable UI components
- **Common**: `components/common/` - Shared/common components

### Example Components

#### MetricCard (`components/analytics/MetricCard.jsx`)
Displays a single metric with icon, value, and trend indicator.

**Props:**
- `title`: Metric name
- `value`: Current value
- `icon`: Emoji icon
- `trend`: Percentage change (optional)
- `isAlert`: Highlight for critical metrics

#### GuardrailChart (`components/analytics/GuardrailChart.jsx`)
Line chart showing metrics over time using Recharts library.

**Props:**
- `data`: Array of time-series data points

#### ConversationList (`components/conversations/ConversationList.jsx`)
Displays and manages conversation lists with filtering and actions.

#### Dashboard (`pages/Dashboard.jsx`)
Main dashboard page that:
- Fetches metrics from backend API
- Displays metric cards
- Shows time-series chart
- Auto-refreshes every 30 seconds

## API Integration

The frontend communicates with the backend using organized service layers:

```javascript
// Using domain-organized services
import { dataService } from './services/api'
import { notificationService } from './services/notifications'

// Fetch metrics
const metrics = await dataService.getMetrics()

// Fetch notifications
const notifications = await notificationService.getNotifications()
```

Services are organized by domain:
- **API Services**: `services/api/` - General API services (auth, data, messaging)
- **Notification Services**: `services/notifications/` - Notification-specific services

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

