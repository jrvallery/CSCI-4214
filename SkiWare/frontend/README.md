# SkiWare Frontend

A React-based ski and snowboard maintenance assistant web application.

## Project Structure

```
src/
├── pages/
│   ├── HomePage.jsx      - Landing page with feature cards
│   ├── FormPage.jsx      - Assessment form with equipment details
│   └── ResultsPage.jsx   - Results and recommendations display
├── components/
│   └── Header.jsx        - Header with branding
├── App.jsx              - Main app component with routing logic
├── App.css              - App-level styles
├── index.css            - Global styles
└── main.jsx             - React entry point
```

## Setup & Running Locally

### Prerequisites
- Node.js 20.19+ or 22.12+
- npm

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

When running through the root `docker-compose.yml`, Vite proxies `/api/*` requests to the FastAPI container at `http://app:8080`, which serves `backend.main:app`.

### Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Features

### Home Page
- Hero section with app description
- Feature cards explaining the three core benefits
- Call-to-action button to start assessment

### Assessment Form
The form collects:
- **Equipment Type**: Skis or Snowboard
- **Equipment Details**: Brand, length, age
- **Riding Preferences**: Terrain preference, skiing style
- **Maintenance History**: Days since waxing, edge work, visible damage
- **Rider Info** (optional): Height, weight for personalization

### Results Page
Displays:
- Equipment assessment summary
- Personalized recommendations with severity levels
- General maintenance tips
- Actions to start a new assessment or return home

## Component Architecture

All state is managed in the main `App.jsx` component:
- `currentPage`: Tracks which page to display (home/form/results)
- `formData`: Stores submitted equipment assessment data
- `results`: Stores API response with recommendations

Page navigation is handled through callback functions passed down from App.

## API Integration

The form data is sent to `/api/assess` endpoint with this structure:

```json
{
  "equipmentType": "skis",
  "brand": "Rossignol",
  "length": 170,
  "age": "1-2 years",
  "terrain": "hybrid",
  "style": "both",
  "daysSinceWax": 5,
  "daysSinceEdgeWork": 10,
  "coreShots": 0,
  "height": 175,
  "weight": 70,
  "issueDescription": ""
}
```

Expected response format:

```json
{
  "equipmentType": "skis",
  "brand": "Rossignol",
  "terrain": "hybrid",
  "style": "both",
  "daysSinceWax": 5,
  "daysSinceEdgeWork": 10,
  "recommendations": [
    {
      "title": "Waxing Recommended Soon",
      "severity": "LOW",
      "description": "You're at 5 days since waxing..."
    }
  ],
  "tips": [
    "Wax your skis every 5-7 days of riding",
    "..."
  ]
}
```

## Styling

- **CSS Variables**: Root-level color and sizing variables in `index.css`
- **Responsive Design**: Mobile-first approach with breakpoints at 768px
- **Colors**:
  - Primary Blue: `#0066ff`
  - Secondary Blue: `#00b8d4`
  - Dark Text: `#1a1a1a`
  - Light Gray: `#999`

## Development Notes

### Form Inputs
- Text inputs, number inputs, and selects are fully styled
- Radio buttons and sliders use custom styling for consistency
- Sliders have visual fill indicators based on value

### State Management
Currently using React's built-in `useState`. For a more complex app, consider Redux or Context API.

### Error Handling
Currently, if the API request fails, mock data is displayed. This should be updated to show proper error states once the backend is ready.

## Docker Development

From the repo root:

```bash
docker compose up --build
```

This starts:

- React/Vite at `http://localhost:5173`
- FastAPI at `http://localhost:8080`

## Environment Variables

None currently required for development. In production, you may need:
- `VITE_API_URL`: Base URL for API calls (defaults to same host)

Use `.env` file for local overrides:

```
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Node version issues
If you get "Node.js version" warnings or errors:
```bash
# Ensure you're using Node 20.19+ or 22.12+
node --version

# If too old, upgrade Node.js
```

### Module not found
```bash
rm -rf node_modules package-lock.json
npm install
```

### Port 5173 already in use
```bash
npm run dev -- --port 3000
```
