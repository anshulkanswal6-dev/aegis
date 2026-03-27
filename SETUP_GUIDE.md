# AEGIS - AI-Enabled Agent System

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Node.js 16+ and npm/yarn
- Git

### Backend Setup

1. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in the required credentials and API keys

4. **Run the backend server:**
   ```bash
   python backend/main.py
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment:**
   - Create `.env.local` in the `frontend` directory
   - Add necessary API endpoints and configuration

3. **Start development server:**
   ```bash
   npm run dev
   ```

### Project Structure

```
AEGIS/
├── backend/          # Python backend services
│   ├── main.py      # Entry point
│   ├── agent.py     # AI agent logic
│   ├── action_engine.py
│   ├── trigger_engine.py
│   └── ...
├── frontend/         # React TypeScript frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── walletcontracttemplate.sol  # Smart contract
├── requirements.txt  # Python dependencies
└── README.md
```

### Environment Variables

Key environment variables needed:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase API key
- `OPENAI_API_KEY` - OpenAI API key
- `GOOGLE_API_KEY` - Google Generative AI API key
- Database credentials and other service keys

See `.env.example` for the complete template.

### Development

- **Backend testing:** Run test files in `backend/` (e.g., `python backend/test_agent_response.py`)
- **Frontend building:** `npm run build` from the `frontend` directory
- **Linting:** ESLint is configured for the frontend

### Deployment

- Smart contract can be deployed using the scripts in `backend/`
- Backend can be containerized with Docker
- Frontend can be deployed to any static hosting service

### License

See LICENSE file for details.
