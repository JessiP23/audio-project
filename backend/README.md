# Audio Processing Backend

A high-performance, scalable audio processing backend built with FastAPI, featuring real-time audio effects using Spotify's Pedalboard library.

## 🚀 Features

- **High-Quality Audio Effects**: Powered by Spotify's Pedalboard library for professional-grade reverb and other effects
- **Real-Time Processing**: WebSocket support for live audio streaming and processing
- **Scalable Architecture**: Modular design with clean separation of concerns
- **Efficient File Management**: AVL tree-based file indexing with LRU caching
- **Thread-Safe Buffers**: Circular audio buffers with overflow protection
- **Comprehensive API**: RESTful endpoints with OpenAPI documentation
- **Database Integration**: Async SQLAlchemy with proper session management
- **Error Handling**: Custom exception classes with detailed error responses

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       └── audio.py        # Audio processing endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration and settings
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   └── errors.py           # Custom error handlers
│   ├── models/
│   │   ├── __init__.py
│   │   ├── db.py               # SQLAlchemy models
│   │   └── pydantic.py         # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audio_buffer.py     # Audio buffer management
│   │   ├── audio_manager.py    # File management with AVL tree
│   │   └── audio_processor/
│   │       ├── __init__.py
│   │       ├── base.py         # Base processor interface
│   │       └── reverb.py       # Reverb effect (Pedalboard)
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py          # Database session management
│   └── utils/
│       └── __init__.py
├── tests/                      # Unit and integration tests
├── uploads/                    # Audio file storage
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   # The database will be automatically created on first run
   ```

## 🚀 Running the Application

### Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker
```bash
docker build -t audio-backend .
docker run -p 8000:8000 audio-backend
```

## 📚 API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🎵 Audio Effects

### Currently Supported Effects

1. **Reverb** (using Pedalboard)
   - Room size control
   - Damping control
   - Wet/dry mix
   - Stereo width

### Adding New Effects

To add a new audio effect:

1. Create a new processor class in `app/services/audio_processor/`
2. Inherit from `AudioEffectProcessor`
3. Implement the `apply()` method
4. Register the effect in `app/services/audio_processor/__init__.py`

Example:
```python
from .base import AudioEffectProcessor

class DelayProcessor(AudioEffectProcessor):
    def apply(self, samples: List[float], parameters: Dict[str, Any]) -> List[float]:
        # Implement delay effect
        return processed_samples
```

## 🔧 Configuration

The application uses environment variables for configuration. Key settings:

```env
# Application
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./audio_processing.db

# Audio Processing
DEFAULT_SAMPLE_RATE=44100
DEFAULT_BUFFER_SIZE=44100
MAX_FILE_SIZE_MB=100

# Storage
UPLOADS_DIR=uploads
PROCESSED_DIR=uploads/processed

# Audio Effects
REVERB_BACKEND=pedalboard
SUPPORTED_AUDIO_FORMATS=.wav,.mp3,.flac,.ogg,.m4a

# Logging
LOG_LEVEL=INFO
```

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## 📊 Monitoring

The application provides several monitoring endpoints:

- `/health` - Basic health check
- `/api/audio/health` - Detailed audio system health
- `/api/audio/statistics` - System statistics
- `/api/audio/buffers` - Buffer status for all sessions

## 🔒 Security

- Input validation with Pydantic schemas
- File type validation for uploads
- Size limits on file uploads
- CORS configuration
- Error handling without information leakage

## 🚀 Performance

- **AVL Tree**: O(log n) file operations
- **LRU Cache**: Fast file access for frequently used files
- **Circular Buffers**: Efficient memory usage for real-time processing
- **Async Operations**: Non-blocking I/O for better concurrency
- **Connection Pooling**: Database connection reuse

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting: `black . && isort . && flake8`
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the logs for error details
3. Open an issue on GitHub

## 🔄 Migration from Old Backend

If migrating from the old backend:

1. **Backup your data**
2. **Install new dependencies**: `pip install -r requirements.txt`
3. **Update your frontend** to use the new API endpoints
4. **Test thoroughly** before deploying to production

The new backend maintains API compatibility where possible, but some endpoints may have changed. 