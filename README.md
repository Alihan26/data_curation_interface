# Human-AI Metadata Curation System

A desktop web application that helps data curators build high-quality metadata for digital editions collected from project websites. The system ingests entities and pages from an API, uses LLMs to propose field values, and lets curators review suggestions in context with highlighted evidence from the original HTML.

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.8+ (Anaconda recommended)
- **Node.js**: 16+ and npm
- **Modern web browser**: Chrome, Firefox, Safari, or Edge
- **OpenAI API key**: For AI-powered suggestions

### Backend Setup
```bash
# Navigate to backend directory
cd backend
leaove everything about adding new
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp env_template.txt .env

# Edit .env file and add your OpenAI API key
# OPENAI_API_KEY=your_actual_api_key_here
# OPENAI_MODEL=gpt-4o-mini
# AI_TEMPERATURE=0.3
# AI_MAX_TOKENS=2000

# Start the backend server
python app.py
```

The backend will start on **http://localhost:8000**

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

The frontend will start on **http://localhost:4000**

### First Run
1. Open your browser and navigate to **http://localhost:4000**
2. Ensure the backend is running on port 8000
3. Check "🤖 Use AI Suggestions" if you want AI-powered metadata suggestions
4. Start curating metadata!

## 🏗️ Architecture

### Backend (Flask)
- **Port**: 8000
- **Framework**: Flask with RESTful API
- **Features**:
  - In-memory data store (demo purposes)
  - HTML content fetching and processing
  - Comprehensive input validation
  - Structured error handling
  - Request logging

### Frontend (Vue.js + Vite)
- **Port**: 4000
- **Framework**: Vue.js 3 with Vite build tool
- **Features**:
  - Three-panel workspace layout
  - Real-time metadata suggestions
  - Accept/Reject actions for suggestions
  - Responsive design with modern UI

## 📚 API Endpoints

### Core Metadata Endpoints
- `GET/POST /api/sources` - Manage data sources
- `GET/POST /api/properties` - Manage metadata properties
- `GET/POST /api/editions` - Manage digital editions
- `GET/POST /api/suggestions` - Manage metadata suggestions
- `POST /api/sources/<id>/ingestion_complete` - Mark ingestion complete

### Preview & Processing Endpoints
- `POST /api/process-curation` - Process curation workflow
- `GET /api/fetch-external` - Fetch external page data
- `GET /api/health` - Health check

## 🎯 Key Features

### 1. Inbox with Source-based Filters
- Browse entities by source (one source → many editions)
- Filter and organize curation tasks

### 2. Three-Panel Workspace
- **Left Panel**: Configuration and entity selection
- **Center Panel**: Page content with highlights
- **Right Panel**: Metadata fields and suggestions

### 3. Evidence-Gated Acceptance
- Review suggestions with source context
- Accept/reject/edit metadata values
- Quick keyboard actions
- **AI-Powered Suggestions**: OpenAI GPT models analyze HTML content
- **Confidence Scoring**: Each suggestion includes confidence level (0-100%)
- **Evidence Highlighting**: Supporting text snippets for each suggestion

### 4. Provenance & History
- Versioning for all field changes
- Rollback capabilities
- Full audit trail
- **AI Attribution**: Track which suggestions were AI-generated vs manual

## 🤖 AI Integration

### OpenAI Configuration
The system integrates with OpenAI's GPT models to automatically generate metadata suggestions:

1. **Set API Key**: Create `.env` file in backend directory:
   ```bash
   OPENAI_API_KEY=your_actual_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   AI_TEMPERATURE=0.3
   AI_MAX_TOKENS=2000
   ```

2. **Enable AI**: Check "🤖 Use AI Suggestions" in the frontend

3. **AI Processing**: When enabled, the system will:
   - Fetch HTML content from URLs
   - Send content to OpenAI with property definitions
   - Generate contextual metadata suggestions
   - Display confidence scores and evidence
   - Store AI-generated suggestions with attribution

### AI Features
- **Smart Analysis**: Understands webpage content and context
- **Property-Aware**: Generates suggestions matching existing metadata schemas
- **Confidence Scoring**: Provides reliability indicators for each suggestion
- **Evidence Extraction**: Highlights supporting text from source content
- **Fallback Handling**: Gracefully degrades when AI service unavailable

## 🔧 Development

### Code Quality
- Python syntax validation
- Frontend build verification
- Comprehensive error handling
- Request validation and sanitization

### Testing
```bash
# Backend syntax check
cd backend && python -m py_compile app.py

# Frontend build test
cd frontend && npm run build

# API testing
curl http://localhost:8000/api/health
curl http://localhost:8000/api/sources
```

### Project Structure
```
Alihan_Script/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── curation_preview.py # HTML preview generator
│   ├── ai_curation.py      # AI integration logic
│   ├── dummy_data.py       # Sample data for testing
│   ├── requirements.txt    # Python dependencies
│   └── env_template.txt    # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── App.vue        # Main Vue component
│   │   ├── AuditLogViewer.vue # Audit log component
│   │   ├── FieldHistoryModal.vue # Field history modal
│   │   ├── api.js         # API service layer
│   │   ├── main.js        # Vue app entry point
│   │   └── style.css      # Global styles
│   ├── package.json       # Node.js dependencies
│   └── vite.config.js     # Vite configuration
├── features_implement.txt  # Feature implementation status
└── README.md              # This file
```

## 🎨 UI Components

### Metadata Suggestions Panel
- Property name and type display
- Suggested values with confidence indicators
- Accept/Reject action buttons
- Hover effects and visual feedback

### Page Content Viewer
- HTML content rendering
- Character and word count statistics
- URL display with clickable links
- Responsive text formatting

### Configuration Panel
- Entity name input
- Source selection
- Process initiation controls
- Status indicators

## 🔒 Security & Validation

### Input Validation
- JSON content-type enforcement
- Required field validation
- Reference integrity checks
- Property type validation

### Error Handling
- Structured error responses
- HTTP status code compliance
- Comprehensive logging
- Graceful degradation

## 🚧 Roadmap

### Phase 1 ✅ (Completed)
- Basic backend API implementation
- Frontend integration
- Mock data and endpoints
- Basic UI components

### Phase 2 🔄 (In Progress)
- Enhanced error handling
- Input validation
- Logging and monitoring
- UI polish and styling

### Phase 3 📋 (Planned)
- Persistent data storage
- User authentication
- Advanced search and filtering
- Export capabilities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Submit a pull request

## 📄 License

This project is part of a Bachelor's thesis on Human-AI Metadata Curation.

## 🆘 Troubleshooting

### Common Issues

**Backend won't start:**
- Check if port 8000 is available
- Verify Python dependencies are installed
- Check `.env` file configuration

**Frontend won't start:**
- Ensure Node.js 16+ is installed
- Check if port 4000 is available
- Verify all npm packages are installed

**AI suggestions not working:**
- Verify OpenAI API key in `.env` file
- Check API key has sufficient credits
- Ensure backend is running

**API errors:**
- Check backend console for error logs
- Verify frontend is connecting to correct backend URL
- Check browser console for frontend errors

### Getting Help
1. Check the logs in the backend console
2. Verify API endpoints are accessible
3. Check browser console for frontend errors
4. Ensure all dependencies are installed
5. Review the error messages for specific guidance

---

**Status**: 🟢 Production Ready (Demo Mode)  
**Last Updated**: December 2024  
**Version**: 1.0.0  
**Author**: Alihan Karatasli - Bachelor's Thesis Project
