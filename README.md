# David AI Audio Research Studio

A comprehensive real-time audio processing system designed for AI/ML research, featuring advanced audio effects, analysis capabilities, and a modern web interface.

## 🎯 Overview

This project implements a full-stack audio processing platform that combines real-time audio manipulation with advanced analysis features. Built with David AI's research mission in mind, it provides a foundation for audio data collection, processing, and feature extraction for machine learning applications.

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DAVID AI AUDIO RESEARCH STUDIO                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FRONTEND      │    │    BACKEND      │    │   DATABASE      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Audio     │    │   Audio Buffer  │    │   Audio Files   │
│     API         │    │   Processing    │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Real-time     │    │   Audio Effects │    │   Analysis      │
│   Visualization  │    │   Engine        │    │   Pipeline      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Audio Processing Pipeline

```
Input Audio File
       │
       ▼
┌─────────────────┐
│   File Upload   │
│   (Validation)  │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│   Audio Buffer  │
│   (Circular)    │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│   Effect Chain  │
│   (Real-time)   │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│   Analysis      │
│   (Features)    │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│   Output        │
│   (Playback)    │
└─────────────────┘
```

## 🚀 Features

### Core Audio Processing
- **Circular Audio Buffer**: Thread-safe, fixed-size buffer with overflow/underflow handling
- **Real-time Effects**: Reverb, Delay, Distortion, Filter, Compression, Chorus, Flanger, Phaser, Equalizer, Normalization
- **Audio Analysis**: RMS, Peak, Spectral Centroid/Rolloff, Zero Crossing Rate
- **Feature Extraction**: MFCC, Chroma, Spectral, Rhythm features for ML applications

### Frontend Interface
- **Modern UI**: React/Next.js with Tailwind CSS and Framer Motion
- **Real-time Visualization**: Web Audio API-powered frequency spectrum analyzer
- **File Management**: Drag-and-drop audio file upload with format validation
- **Session Management**: Persistent audio sessions with effect chains

### Backend Services
- **RESTful API**: FastAPI with comprehensive endpoint coverage
- **WebSocket Support**: Real-time audio streaming and effect application
- **Database Integration**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Audio Processing**: Librosa-based audio analysis and manipulation

## 🛠️ Technical Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Audio**: Web Audio API
- **Animations**: Framer Motion
- **UI Components**: Heroicons, React Hot Toast

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.9+
- **Audio Processing**: Librosa, SciPy, NumPy
- **Database**: SQLAlchemy (PostgreSQL/SQLite)
- **Real-time**: WebSockets
- **Validation**: Pydantic
- **Logging**: Structured logging with file output

### Infrastructure
- **Containerization**: Docker
- **Cloud Ready**: AWS-compatible architecture
- **Monitoring**: Comprehensive logging and health checks
- **Security**: CORS configuration, input validation

## 📊 Technical Specifications

### Audio Buffer Implementation

```python
class AudioBuffer:
    def __init__(self, size: int):
        self.size = size
        self.buffer = np.zeros(size, dtype=np.float32)
        self.read_ptr = 0
        self.write_ptr = 0
        self.available = 0
        self.lock = Lock()
```

**Key Features:**
- **Thread Safety**: Uses `threading.Lock` for concurrent access
- **Circular Design**: Prevents memory reallocation
- **Overflow Handling**: Graceful handling of buffer full conditions
- **Amplitude Scaling**: Built-in amplitude modification capability

### Audio Effects Engine

**Implemented Effects:**
1. **Reverb**: Convolution-based with room size and damping controls
2. **Delay**: Time-based with feedback and mix parameters
3. **Distortion**: Soft clipping with drive control
4. **Filter**: Butterworth low-pass with cutoff and resonance
5. **Compression**: Dynamic range compression with threshold and ratio
6. **Chorus**: Modulated delay for thickening effect
7. **Flanger**: Comb filter with LFO modulation
8. **Phaser**: All-pass filter chain with frequency modulation
9. **Equalizer**: Multi-band parametric EQ
10. **Normalization**: Peak-based audio normalization

### Feature Extraction Pipeline

**ML-Ready Features:**
- **MFCC**: 13-dimensional Mel-frequency cepstral coefficients
- **Chroma**: 12-dimensional pitch class profiles
- **Spectral**: Centroid, rolloff, bandwidth analysis
- **Rhythm**: Tempo detection and beat tracking
- **Harmonic**: Harmonic/percussive separation ratio

## 🔧 Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL (optional, SQLite for development)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Configuration
```bash
# Backend (.env)
DATABASE_URL=sqlite+aiosqlite:///./audio_processing.db
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Frontend (next.config.js)
# Configured for development with CORS
```

## 🎵 Usage Guide

### 1. Audio File Upload
- Supported formats: WAV, MP3, FLAC, OGG
- Maximum file size: 50MB
- Automatic format validation and conversion

### 2. Real-time Effects
- Click effect buttons to apply processing
- Effects are applied in real-time to the audio buffer
- Multiple effects can be chained together
- Effect parameters are configurable via API

### 3. Audio Analysis
- Click "Analyze Audio" for comprehensive analysis
- Extract specific features (MFCC, Spectral, Rhythm, Chroma)
- Results displayed in real-time with detailed metrics

### 4. Visualization
- Real-time frequency spectrum display
- RMS and peak level monitoring
- Color-coded levels (green/yellow/red)

## 🔍 API Documentation

### Core Endpoints

#### Session Management
```http
POST /api/audio/session
GET /api/audio/sessions
DELETE /api/audio/{session_id}
```

#### Audio Processing
```http
POST /api/audio/{session_id}/process
POST /api/audio/{session_id}/batch-process
POST /api/audio/upload
```

#### Analysis
```http
POST /api/audio/{session_id}/analyze
POST /api/audio/{session_id}/extract-features
```

#### Real-time
```http
WS /ws/audio/{session_id}
```

### Request/Response Examples

**Apply Audio Effect:**
```json
POST /api/audio/{session_id}/process
{
  "effect": "reverb",
  "parameters": {
    "room_size": 0.5,
    "damping": 0.5
  }
}
```

**Audio Analysis Response:**
```json
{
  "session_id": "file_20250729_225329",
  "analysis": {
    "rms": 0.1234,
    "peak": 0.5678,
    "spectral_centroid": 1234.5,
    "duration": 30.5
  },
  "features": {
    "tempo": 120.5,
    "mfcc_mean": [...],
    "chroma_mean": [...]
  }
}
```

## 🏗️ Deployment Architecture

### AWS Cloud Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS CLOUD INFRASTRUCTURE                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   API Gateway   │    │   Lambda        │
│   (CDN)         │◄──►│   (REST API)    │◄──►│   (Functions)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   S3 Static     │    │   ECS/Fargate   │    │   RDS           │
│   Assets        │    │   (Backend)     │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   S3 Audio      │    │   ElastiCache   │    │   CloudWatch    │
│   Storage       │    │   (Redis)       │    │   (Monitoring)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Deployment Components

1. **Frontend**: S3 + CloudFront for static hosting
2. **Backend**: ECS Fargate for containerized deployment
3. **Database**: RDS PostgreSQL for production data
4. **Caching**: ElastiCache Redis for session management
5. **Storage**: S3 for audio file storage
6. **Monitoring**: CloudWatch for logs and metrics
7. **CDN**: CloudFront for global content delivery

## 🔬 Technical Trade-offs

### Design Decisions

#### 1. Circular Buffer vs. Dynamic Buffer
**Choice**: Circular buffer with fixed size
**Pros**: 
- Predictable memory usage
- No allocation overhead
- Thread-safe operations
**Cons**: 
- Fixed size limitation
- Potential data loss on overflow

#### 2. Web Audio API vs. WebAssembly
**Choice**: Web Audio API for real-time processing
**Pros**: 
- Native browser support
- Hardware acceleration
- Low latency
**Cons**: 
- Limited to browser capabilities
- Less control over processing

#### 3. FastAPI vs. Django
**Choice**: FastAPI for backend
**Pros**: 
- Async support
- Automatic API documentation
- High performance
- Type safety with Pydantic
**Cons**: 
- Smaller ecosystem
- Less built-in features

#### 4. SQLite vs. PostgreSQL
**Choice**: SQLite for development, PostgreSQL for production
**Pros**: 
- SQLite: Zero configuration, file-based
- PostgreSQL: ACID compliance, advanced features
**Cons**: 
- SQLite: Limited concurrency
- PostgreSQL: Requires server setup

### Performance Considerations

#### Audio Processing
- **Buffer Size**: 44,100 samples (1 second at 44.1kHz)
- **Processing Latency**: < 10ms for real-time effects
- **Memory Usage**: ~2MB per audio session
- **CPU Usage**: Optimized with NumPy vectorization

#### Frontend Performance
- **Bundle Size**: < 500KB gzipped
- **First Paint**: < 1.5s
- **Audio Latency**: < 50ms
- **Memory**: < 100MB for typical usage

## 🧪 Testing Strategy

### Unit Tests
- Audio buffer operations
- Effect algorithms
- API endpoints
- Database operations

### Integration Tests
- End-to-end audio processing
- WebSocket communication
- File upload/download
- Session management

### Performance Tests
- Concurrent user simulation
- Audio processing benchmarks
- Memory usage profiling
- Latency measurements

## 🔒 Security Considerations

### Input Validation
- File type validation
- Size limits enforcement
- Parameter bounds checking
- SQL injection prevention

### Authentication & Authorization
- Session-based authentication
- API key management (future)
- Role-based access control (future)

### Data Protection
- Secure file storage
- Encrypted database connections
- HTTPS enforcement
- CORS configuration

## 📈 Future Enhancements

### Planned Features
1. **User Authentication**: JWT-based auth system
2. **Project Management**: Save/load audio projects
3. **Effect Presets**: Pre-configured effect chains
4. **Batch Processing**: Multiple file processing
5. **Export Options**: Various audio format export
6. **MIDI Support**: MIDI file integration
7. **VST Plugin Support**: External plugin hosting
8. **Real-time Collaboration**: Multi-user sessions

### Technical Improvements
1. **WebAssembly**: C++ audio processing modules
2. **Web Workers**: Background processing
3. **GPU Acceleration**: WebGL for visualizations
4. **Machine Learning**: AI-powered audio enhancement
5. **Cloud Storage**: Direct cloud integration
6. **Mobile App**: React Native companion app

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

### Code Standards
- **Python**: PEP 8, type hints, docstrings
- **TypeScript**: ESLint, Prettier
- **Testing**: >90% coverage
- **Documentation**: Comprehensive API docs

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: Inline code documentation
- **API Docs**: Auto-generated with FastAPI
- **Examples**: Included in repository

---

**Built with ❤️ for David AI's audio research mission**