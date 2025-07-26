# Architecture Overview

The Agentic Emergency Response System implements a comprehensive multi-agent architecture for emergency response, with three core components working together to provide intelligent emergency assistance.

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                        │
├─────────────────────┬─────────────────┬─────────────────────────┤
│  User Dashboard     │  Admin Dashboard │  Voice/Text Interface   │
│  (Bootstrap 5)      │  (Analytics)     │  (Multilingual)        │
└─────────────────────┴─────────────────┴─────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                           │
├─────────────────────┬─────────────────┬─────────────────────────┤
│  Emergency API      │  Voice API       │  Agentic Status API     │
│  /api/.../emergency │  /api/.../voice  │  /api/.../agentic/      │
└─────────────────────┴─────────────────┴─────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                AGENTIC EMERGENCY SYSTEM                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │    PLANNER      │ │    EXECUTOR     │ │     MEMORY      │   │
│  │                 │ │                 │ │                 │   │
│  │ • Task decomp   │ │ • Action exec   │ │ • Context store │   │
│  │ • Priority mgmt │ │ • Tool calling  │ │ • Pattern learn │   │
│  │ • Resource plan │ │ • API integr    │ │ • Situation awrn│   │
│  │ • Risk assess  │ │ • Results track │ │ • Memory recall │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
┌─────────────────────────────────────────────────────────────────┐
│                     TOOL INTEGRATION LAYER                     │
├─────────────────────┬─────────────────┬─────────────────────────┤
│  Gemini AI API      │  Disaster Feeds  │  Audio Processing       │
│  • Classification   │  • USGS/GDACS    │  • Speech-to-Text      │
│  • Planning         │  • Real-time     │  • Text-to-Speech      │
│  • Reasoning        │  • Geospatial    │  • Audio conversion    │
│  • Instructions     │  • Contextual    │  • Voice response      │
└─────────────────────┴─────────────────┴─────────────────────────┘
           │                    │                    │
┌─────────────────────────────────────────────────────────────────┐
│                     DATA PERSISTENCE LAYER                     │
├─────────────────────┬─────────────────┬─────────────────────────┤
│  Django ORM         │  Cache System    │  Media Storage          │
│  • Emergency msgs   │  • Memory store  │  • Audio files         │
│  • Categories       │  • Session data  │  • Response audio      │
│  • Analytics        │  • Temp data     │  • User uploads        │
└─────────────────────┴─────────────────┴─────────────────────────┘
```

## Core Agentic Components

### 1. **Planner** (`planner.py`)
The Emergency Planner implements intelligent task decomposition:
- **Input**: Emergency message, location, severity, category
- **Process**: Breaks down emergencies into actionable sub-tasks using Gemini AI
- **Output**: Comprehensive response plan with priorities, timelines, and resource requirements

**Key Functions**:
- `plan_response()`: Main planning orchestration
- `prioritize_tasks()`: Task priority management  
- `estimate_resource_requirements()`: Resource allocation planning

### 2. **Executor** (`executor.py`)
The Emergency Executor carries out planned actions using available tools:
- **Input**: Response plan from Planner + emergency context
- **Process**: Executes actions using appropriate tools and APIs
- **Output**: Execution log with results and outcomes

**Available Tools**:
- `disaster_feed_check`: Real-time disaster data integration
- `weather_check`: Weather condition analysis (extensible)
- `resource_lookup`: Emergency resource identification
- `generate_instructions`: AI-powered instruction generation
- `gemini_reasoning`: General AI reasoning and analysis

### 3. **Memory** (`memory.py`)  
The Emergency Memory provides contextual awareness and learning:
- **Input**: Complete emergency interactions (context + plan + execution)
- **Process**: Stores, indexes, and analyzes historical data
- **Output**: Relevant context for current emergencies + situational awareness

**Memory Capabilities**:
- Location-based pattern recognition
- Category-specific learning and insights
- Effectiveness tracking and optimization
- Situational awareness (geographic clustering, trends)
- Feedback-based continuous learning

## Agentic Workflow

The system processes each emergency through a complete agentic cycle for both text and voice messages:

1. **Context Gathering**: Collect user input + location + historical context
2. **Initial Classification**: Basic emergency categorization using Gemini
3. **Memory Retrieval**: Get relevant historical patterns and insights  
4. **Comprehensive Planning**: Generate detailed response plan with sub-tasks
5. **Action Execution**: Execute plan using available tools and APIs
6. **Memory Storage**: Store complete interaction for future learning
7. **Response Generation**: Provide enhanced response with agentic insights

### Voice Message Processing
Voice messages follow the same agentic workflow with additional steps:
- **Speech-to-Text**: Convert audio input to text using Web Speech API
- **Agentic Processing**: Process transcribed text through full agentic pipeline  
- **Text-to-Speech**: Convert enhanced agentic response to audio output
- **Audio Filtering**: Remove technical "System Analysis" messages from voice responses

## Tool Integration

### External APIs
- **Google Gemini 1.5 Flash**: Core AI reasoning, planning, and classification
- **USGS Earthquake API**: Real-time earthquake data
- **GDACS Global Disaster API**: Comprehensive disaster information
- **Browser Speech API**: Voice input/output capabilities

### Internal Tools  
- **Disaster Feed Integration**: Contextual emergency data
- **Audio Processing Pipeline**: Speech recognition and synthesis
- **Geospatial Analysis**: Location-based emergency clustering
- **Analytics Engine**: Performance tracking and insights

## Observability & Monitoring

### Logging Strategy
- **Component-level logging**: Each agent component logs decisions and actions
- **Request tracing**: Complete emergency processing pipeline tracking
- **Performance metrics**: Response times, success rates, resource usage
- **Error handling**: Graceful degradation with detailed error tracking

### Key Metrics Tracked
- Emergency classification accuracy
- Response plan completeness scores  
- Tool execution success rates
- Memory retrieval effectiveness
- User satisfaction indicators (when available)
- **Cache performance**: Hit rates, efficiency, and size monitoring
- **API usage optimization**: External API call reduction metrics

### System Dashboard
- **Real-time component status**: Planner, Executor, Memory health monitoring
- **Performance metrics**: Plans generated, actions executed, stored patterns
- **Cache management**: Efficiency tracking, manual clearing, TTL monitoring
- **Historical analytics**: 24-hour message volumes, response times
- **Operational controls**: System restart, cache clearing, metric refresh

### Testing & Validation
- **Unit tests**: Individual component functionality
- **Integration tests**: Full agentic workflow testing
- **Load testing**: System performance under stress
- **A/B testing**: Agentic vs non-agentic response comparison
- **Cache testing**: TTL validation, efficiency benchmarking

## Performance Optimizations

### Horizontal Scaling
- Stateless agentic components for easy scaling
- Distributed memory system using Django cache framework
- Async execution capabilities for tool calling
- Load balancing across multiple system instances

### Performance Optimizations
- **Memory caching** for frequent pattern lookups
- **Disaster feeds caching** with intelligent TTL management:
  - USGS earthquake data: 5-minute cache TTL
  - GDACS disaster alerts: 15-minute cache TTL
  - Automatic cache cleanup and monitoring
- **Batch processing** for multiple emergency contexts
- **Intelligent tool selection** to minimize API calls
- **Response streaming** for real-time user feedback

### Cache Management
- **In-memory caching system** for external API responses
- **Cache efficiency monitoring** with real-time statistics
- **TTL-based expiration** to ensure data freshness
- **Administrative controls** for cache clearing and monitoring
- **Redundancy protection** against API rate limiting

## Security & Privacy

### Data Protection
- No permanent storage of sensitive user data
- Encrypted communication with external APIs
- Session-based temporary data storage
- GDPR-compliant data handling

### API Security
- Rate limiting on all endpoints
- Input validation and sanitization  
- Error message sanitization
- Audit logging for administrative access  

