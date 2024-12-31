# Gmail Analytics

A web application for analyzing your Gmail messages, providing insights into your email patterns and allowing you to browse your email history.

## Features

- **Email Analytics Dashboard**
  - View top email senders
  - Analyze email domains
  - Interactive data visualizations

- **Email Browser**
  - Search through all emails
  - Filter by date
  - Sort by sender frequency, domain frequency, or date
  - Paginated results

## Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- Gmail account
- Google Cloud Platform project with Gmail API enabled

### Backend Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Cloud credentials:
   - Go to Google Cloud Console
   - Create a new project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials and save as `credentials.json` in project root

### Frontend Setup

1. Install Node.js dependencies:
```bash
npm install
```

### Running the Application

1. Start the backend server:
```bash
make debug_server
```
Or without debug logging:
```bash
make server
```

2. Start the frontend development server:
```bash
npm start
```

3. Open `http://localhost:3000` in your browser

4. On first run:
   - Click "Sync Emails"
   - Authenticate with your Google account
   - Wait for initial email sync to complete

## Project Structure

```
gmail_analyzer/
├── app/                    # Backend Python code
│   ├── api/               # API routes
│   ├── services/          # Business logic
│   ├── main.py           # FastAPI application
│   ├── models.py         # Database models
│   └── schemas.py        # Pydantic schemas
├── src/                    # Frontend React code
│   ├── components/       # React components
│   ├── services/        # API services
│   └── App.js
├── requirements.txt       # Python dependencies
└── package.json          # Node.js dependencies
```

## Development

### Debug Mode

Run the backend with debug logging:
```bash
make debug_server
```

### Database

The application uses SQLite for data storage. The database file is created automatically as `gmail_analyzer.db`.

## Technology Stack

- **Backend**
  - FastAPI
  - SQLAlchemy
  - Gmail API

- **Frontend**
  - React
  - Tailwind CSS
  - Recharts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Open a pull request

## License

MIT License
