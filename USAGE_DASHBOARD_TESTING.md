# Usage Dashboard Testing Guide

## Quick Start

### 1. Start Backend
```bash
cd backend
# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Start server
uvicorn app.main:app --reload --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Access Usage Tab
- Open browser: http://localhost:5173
- Click the **"Usage"** tab (5th tab)

## Features to Test

### ✅ Date Range Selector
- [ ] Click "Today" - should show today's usage
- [ ] Click "7 Days" - should show last week
- [ ] Click "30 Days" (default) - should show last month
- [ ] Click "All Time" - should show all usage data
- [ ] Click "Custom" - should show date pickers
- [ ] Select custom date range and verify data updates

### ✅ Summary Statistics
Should display:
- [ ] Total Cost (USD)
- [ ] Total Requests
- [ ] Total Tokens
- [ ] Average Cost per Request
- [ ] Unique Models used
- [ ] Unique Sessions

### ✅ Cost Over Time Chart
- [ ] Line chart displays correctly
- [ ] X-axis shows dates
- [ ] Y-axis shows cost in USD
- [ ] Hover tooltip shows exact values
- [ ] Chart responds to date range changes

### ✅ Token Usage Chart
- [ ] Line chart shows token consumption
- [ ] Green line color
- [ ] Hover tooltip works

### ✅ Model Cost Comparison
- [ ] Horizontal bar chart displays
- [ ] Shows top 10 models by cost
- [ ] Model names are visible (truncated to 30 chars)
- [ ] Bars are proportional to cost

### ✅ Model Usage Table
- [ ] Table displays all models
- [ ] Columns: Model, Prompt Tokens, Completion Tokens, Total Tokens, Cost
- [ ] Numbers are formatted correctly
- [ ] Scrollable if many models

### ✅ Budget Alerts
1. Click **"Budget Settings"** button
2. Set budgets:
   - Daily: $1.00
   - Weekly: $5.00
   - Monthly: $20.00
3. Generate usage (send messages in Chat tab)
4. Return to Usage tab
5. Should see alerts when:
   - [ ] 80%+ of budget used (⚠️ warning, orange)
   - [ ] 100%+ of budget exceeded (⛔ critical, red)

### ✅ CSV Export
1. Click **"Export CSV"** button
2. Should download file: `usage_YYYY-MM-DD_to_YYYY-MM-DD.csv`
3. Open CSV in Excel/text editor
4. Verify columns: Date, Session ID, Model, Prompt Tokens, Completion Tokens, Total Tokens, Cost
5. Verify data matches dashboard

### ✅ Refresh Button
- [ ] Click "Refresh" - should reload all data
- [ ] Button shows "Loading..." during fetch
- [ ] Data updates after refresh

### ✅ Error Handling
- [ ] If no data exists, shows "No usage data found" message
- [ ] Network errors display in red error card
- [ ] Export failures show error message

## Expected Behavior

### First Time (No Usage Data)
- Should show "No usage data found" message
- Charts will be empty
- Stats will show zeros
- No budget alerts

### After Generating Usage
1. Go to **Chat** tab
2. Send a few messages using different models
3. Return to **Usage** tab
4. Click **Refresh**
5. Should see:
   - Charts populated with data
   - Statistics updated
   - Models listed in table
   - Budget alerts if limits set

## API Endpoints Verification

Test backend endpoints directly:

### Timeline
```bash
curl "http://localhost:8000/api/usage/timeline?start_date=2025-12-01&end_date=2025-12-15&granularity=day"
```

Expected response:
```json
[
  {
    "period": "2025-12-15",
    "total_tokens": 1500,
    "prompt_tokens": 800,
    "completion_tokens": 700,
    "total_cost": 0.0023,
    "request_count": 3
  }
]
```

### Stats
```bash
curl "http://localhost:8000/api/usage/stats?start_date=2025-12-01&end_date=2025-12-15"
```

Expected response:
```json
{
  "total_requests": 10,
  "total_tokens": 15000,
  "total_prompt_tokens": 8000,
  "total_completion_tokens": 7000,
  "total_cost": 0.0234,
  "avg_cost_per_request": 0.00234,
  "first_request": "2025-12-01T10:30:00",
  "last_request": "2025-12-15T14:20:00",
  "unique_models": 3,
  "unique_sessions": 5
}
```

## Troubleshooting

### Charts not displaying
- Check browser console for errors
- Verify recharts is installed: `npm list recharts`
- Check if data array is empty

### Date picker not working
- Verify date-fns is installed: `npm list date-fns`
- Check date format (must be YYYY-MM-DD)

### Budget alerts not showing
- Set budgets in Budget Settings
- Generate usage that exceeds 80% of limit
- Ensure today's date matches data in timeline

### CSV export fails
- Check browser console for error details
- Verify backend `/api/usage/sessions/` endpoint works
- Check for CORS issues

### Backend errors
- Check backend logs for Python errors
- Verify database has usage_logs table with data
- Test endpoints with curl/Postman

## Performance Notes

- Charts limited to 365 days for performance
- Table shows all models (no pagination yet)
- Budget calculations use last 7/30 days from timeline data
- CSV export fetches full dataset (may be slow with >10k records)

## Next Steps (Optional Enhancements)

Future improvements to consider:
- [ ] Persistent budget settings (store in DB vs localStorage)
- [ ] Email/browser notifications for budget alerts
- [ ] Cost per 1K tokens metric
- [ ] Filter by session type (Chat/Code/Documents)
- [ ] Pagination for model table
- [ ] Download charts as PNG
- [ ] Comparison mode (compare two date ranges)
- [ ] Real-time usage updates (WebSocket)

## Success Criteria

✅ All charts render correctly
✅ Date range filtering works
✅ Budget alerts trigger appropriately
✅ CSV export produces valid file
✅ No console errors
✅ Responsive on mobile (charts scale)
✅ Fast performance (<2 seconds to load)
