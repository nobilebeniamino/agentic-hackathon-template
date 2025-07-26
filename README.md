# Agentic Emergency Response System

🚨 **An intelligent emergency first-response assistant powered by Google Gemini AI with full agentic architecture.**

This project implements a comprehensive **agentic AI system** for emergency response that follows the **Planner-Executor-Memory** architecture pattern. The system provides multilingual emergency assistance, real-time disaster feed integration, voice support, and intelligent response planning through autonomous AI agents.

## 🤖 Agentic Architecture Overview

The system implements a complete agentic architecture with three core components:

### **🎯 Planner** (`first_response/planner.py`)
- **Purpose**: Decomposes complex emergency situations into actionable sub-tasks
- **AI Model**: Google Gemini 1.5 Flash with structured JSON output  
- **Capabilities**: Priority management, resource planning, risk assessment
- **Output**: Comprehensive response plans with immediate actions, follow-up tasks, and resource requirements

### **⚡ Executor** (`first_response/executor.py`)  
- **Purpose**: Carries out planned actions using available tools and APIs
- **Tool Integration**: Disaster feeds, weather APIs, resource lookup, instruction generation
- **Execution Strategy**: Intelligent tool selection based on action classification
- **Monitoring**: Complete execution logging with success/failure tracking

### **🧠 Memory** (`first_response/memory.py`)
- **Purpose**: Maintains contextual awareness and learns from interactions  
- **Capabilities**: Location-based patterns, category learning, situational awareness
- **Storage**: Django cache with TTL-based expiration and geographic clustering
- **Learning**: Feedback-based continuous improvement of response quality

### **🎭 Orchestrator** (`first_response/agentic_system.py`)
- **Purpose**: Main coordinator that orchestrates all agentic components
- **Workflow**: Context gathering → Memory retrieval → Planning → Execution → Memory storage
- **Integration**: Seamless integration with existing emergency classification system
- **Enhancement**: Provides comprehensive responses with agentic insights

## 🌟 Key Features

### Emergency Response Capabilities
- **� Intelligent Classification**: AI-powered emergency categorization and severity assessment
- **📋 Comprehensive Planning**: Multi-step response plans with priority management
- **🔧 Tool Orchestration**: Automated execution using disaster feeds, weather APIs, and resource databases
- **🧠 Contextual Memory**: Historical pattern recognition and situational awareness
- **🌍 Multilingual Support**: Italian and English with automatic language detection
- **🎤 Voice Integration**: Speech-to-text input and text-to-speech responses
- **📊 Real-time Analytics**: Emergency clustering, trend analysis, and performance metrics

### Technical Architecture
- **Backend**: Django framework deployed on Google Cloud Run
- **Database**: Google Cloud SQL (PostgreSQL) for data persistence  
- **AI/ML**: Google Gemini 1.5 Flash API integration
- **Frontend**: Bootstrap 5 with Chart.js for analytics
- **APIs**: USGS Earthquake, GDACS Disaster, Google Maps integration
- **Audio**: WebRTC speech recognition and Web Speech API
- **Deployment**: Docker containerization on Google Cloud Platform
- **Storage**: Google Cloud SQL for relational data, Django cache for temporary agentic memory

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL database
- Google Gemini API key
- (Optional) Google Maps API key for location visualization

### Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd agentic-hackathon-template
   ```

2. **Set Up Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   Create `.env` file in `ai_first_response/` directory:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   DATABASE_URL=your_postgresql_connection_string
   GOOGLE_MAPS_API_KEY=your_maps_api_key  # Optional
   ```

5. **Database Setup**
   ```bash
   cd ai_first_response
   python manage.py migrate
   python manage.py loaddata initial_categories.json  # If available
   ```

6. **Create Superuser** (for admin dashboard)
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

8. **Access the Application**
   - User Dashboard: http://localhost:8000/
   - Admin Dashboard: http://localhost:8000/admin-dashboard/
   - Django Admin: http://localhost:8000/admin/

## 🛠️ API Endpoints

### Core Emergency API
- `POST /api/first-response/emergency/` - Main emergency processing (agentic)
- `POST /api/first-response/voice/` - Voice message processing
- `POST /api/first-response/tts/` - Text-to-speech conversion

### Agentic System APIs
- `GET /api/first-response/agentic/status/` - System status and capabilities
- `POST /api/first-response/agentic/memory/` - Memory insights and situational awareness

### Analytics & Monitoring
- `GET /api/first-response/alerts/` - Emergency cluster detection
- Admin dashboard with real-time metrics and system status

## 🔬 Agentic System Testing

### Test System Status
```bash
curl -X GET "http://localhost:8000/api/first-response/agentic/status/"
```

### Test Emergency Processing
```bash
curl -X POST "http://localhost:8000/api/first-response/emergency/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Earthquake emergency - building shaking!",
    "lat": 37.7749,
    "lon": -122.4194,
    "language": "en"
  }'
```

### Test Memory Insights
```bash
curl -X POST "http://localhost:8000/api/first-response/agentic/memory/" \
  -H "Content-Type: application/json" \
  -d '{"lat": 37.7749, "lon": -122.4194}'
```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                AGENTIC EMERGENCY SYSTEM                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │    PLANNER      │ │    EXECUTOR     │ │     MEMORY      │   │
│  │ • Task decomp   │ │ • Action exec   │ │ • Context store │   │
│  │ • Priority mgmt │ │ • Tool calling  │ │ • Pattern learn │   │
│  │ • Resource plan │ │ • API integr    │ │ • Situation awrn│   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
┌─────────────────────────────────────────────────────────────────┐
│                     TOOL INTEGRATION LAYER                     │
│  Gemini AI API │ Disaster Feeds │ Audio Processing │ Maps API   │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Performance & Monitoring

### Key Metrics
- **Response Time**: Average ~2-5 seconds for complete agentic processing
- **Plan Completeness**: Tracks quality of generated response plans  
- **Execution Success**: Tool execution success rates and failure analysis
- **Memory Effectiveness**: Historical context relevance and retrieval accuracy
- **Multi-language Support**: Automatic language detection with 95%+ accuracy

### Observability
- **Component Logging**: Each agentic component logs decisions and actions
- **Performance Tracking**: Response times, success rates, resource usage
- **Error Handling**: Graceful degradation with detailed error tracking
- **Admin Dashboard**: Real-time system status and emergency cluster alerts

## 🌐 Deployment

### Docker Deployment
```bash
# Build and run with Docker
docker build -t agentic-emergency-system .
docker run -p 8000:8000 --env-file .env agentic-emergency-system
```

### Production Considerations
- Use PostgreSQL for production database
- Configure proper logging and monitoring
- Set up load balancing for horizontal scaling
- Implement proper SSL/TLS certificates
- Configure environment-specific settings

## 🧪 Testing & Quality Assurance

### Automated Testing
```bash
# Run Django tests
python manage.py test

# Test agentic components
python -m pytest tests/test_agentic_system.py
```

### Manual Testing Scenarios
1. **Basic Emergency Classification**: Test standard emergency messages
2. **Agentic Planning**: Verify comprehensive response plan generation
3. **Tool Execution**: Validate disaster feed integration and resource lookup
4. **Memory Integration**: Test historical context retrieval and learning
5. **Multilingual Support**: Test Italian and English emergency processing
6. **Voice Integration**: Test speech input and audio response generation

## 📈 Future Enhancements

### Planned Features
- **Vector Memory Store**: Semantic similarity search for historical context
- **Real-time Streaming**: WebSocket-based live emergency updates  
- **Multi-modal Input**: Image and video analysis for emergency assessment
- **Advanced Analytics**: Predictive emergency modeling and prevention
- **Mobile App**: Native iOS/Android application with offline capabilities

### Scalability Roadmap
- **Microservices Architecture**: Break down into independent services
- **Event-Driven Architecture**: Implement async message queuing
- **Edge Computing**: Deploy lightweight agents for faster local response
- **Federated Learning**: Cross-system learning while maintaining privacy

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Contact & Support

For questions, issues, or contributions related to this agentic emergency response system, please open an issue on GitHub or contact the development team.

---

**🏆 Built for the Agentic AI Hackathon** - Demonstrating advanced AI agent architecture with real-world emergency response applications.


