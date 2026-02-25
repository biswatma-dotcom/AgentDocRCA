# AgentDocRCA

A lightweight versioned documentation tool for AI voice-agent deployments.

## Features

- **Project Management**: Create and manage multiple documentation projects
- **Requirement Sets**: Define requirements with AI-powered normalization to bullet points
- **Block Templates**: Customizable document blocks (Persona, Flow, FAQs, etc.)
- **Version Control**: Immutable version history with change tracking
- **RCA (Root Cause Analysis)**: Map every change to requirement bullets with reason why
- **Export**: Download versions as DOCX or PDF

## Prerequisites

- Python 3.9+
- PostgreSQL database
- OpenAI API key (for requirement normalization)

## Installation

1. **Clone or download the project**

2. **Create virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

   Required variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `APP_PASSWORD`: Password for app access

5. **Initialize the database**:
   ```bash
   python -c "from modules.database import init_db; init_db()"
   ```

6. **(Optional) Seed sample data**:
   ```bash
   python seed_data.py
   ```

## Running the App

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## Usage

### 1. Create a Project
- Go to "Projects" page
- Click "Create New Project"
- Enter project name and client name

### 2. Add Requirements
- Select your project from sidebar
- Go to "Requirements" page
- Create requirement sets with raw text
- Click "Normalize" to convert to bullet points using AI

### 3. Configure Blocks
- Go to "Block Settings"
- Add document blocks (e.g., Persona, Flow, FAQs)
- Reorder using Up/Down buttons

### 4. Edit Documents
- Go to "Editor" page
- Edit content in each block
- Click "Check for Changes"
- Map changed blocks to requirements (required)
- Save new version

### 5. View Versions & RCA
- Go to "Versions" page
- View version timeline
- See RCA (Root Cause Analysis) for each change
- Download as DOCX or PDF

## Deployment

### Streamlit Community Cloud

1. Push your code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set environment variables in Streamlit Cloud dashboard:
   - `DATABASE_URL`
   - `OPENAI_API_KEY`
   - `APP_PASSWORD`
5. Deploy

### Render

1. Create a new Web Service
2. Connect your GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Add environment variables in Render dashboard

### Database Options

- **Neon**: Serverless PostgreSQL (free tier available)
- **Supabase**: PostgreSQL with additional features
- **Render**: PostgreSQL (free tier available)
- **Any standard PostgreSQL host**

## Project Structure

```
AgentDocRCA/
├── app.py                  # Main Streamlit app
├── modules/
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # Database utilities
│   ├── openai_helper.py   # OpenAI normalization
│   ├── docx_generator.py # DOCX export
│   └── pdf_generator.py  # PDF export
├── seed_data.py          # Sample data script
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

## License

MIT
