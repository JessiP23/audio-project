# Audio Processing Studio

A full-stack real-time audio processing application with advanced effects, waveform visualization, and WebSocket communication.

## 🎵 Features

### Audio Processing
- **Real-time Audio Buffer**: Thread-safe circular buffer implementation
- **Advanced Effects**: Reverb, Delay, Distortion, Filtering, Compression, Chorus, Flanger, Phaser
- **Audio Analysis**: RMS, Peak, Dynamic Range, Spectral Analysis
- **File Support**: WAV, MP3, FLAC, OGG, AAC, M4A

### Modern UI
- **Real-time Visualizer**: Frequency spectrum and level meters
- **Waveform Display**: Interactive waveform with playhead
- **Effects Panel**: Intuitive controls for all audio effects
- **Drag & Drop**: Easy file upload with validation
- **Responsive Design**: Works on desktop and mobile

### Technical Stack
- **Backend**: Python FastAPI with WebSocket support
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Audio**: Web Audio API, Tone.js, WaveSurfer.js
- **Database**: SQLite (development) / PostgreSQL (production)
- **Real-time**: WebSocket communication

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Git

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the backend:**
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:3000`

## 📁 Project Structure

```
project/
├── backend/
│   ├── audio_buffer.py      # Circular buffer implementation
│   ├── audio_processor.py   # Audio effects and processing
│   ├── main.py             # FastAPI application
│   ├── database.py         # Database configuration
│   ├── models.py           # SQLAlchemy models
│   ├── requirements.txt    # Python dependencies
│   └── venv/              # Python virtual environment
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   ├── components/    # React components
│   │   ├── store/         # Zustand state management
│   │   └── hooks/         # Custom React hooks
│   ├── package.json       # Node.js dependencies
│   └── node_modules/      # Node.js modules
└── README.md
```

## 🔧 API Endpoints

### Audio Processing
- `POST /api/audio/session` - Create new audio session
- `POST /api/audio/{session_id}/write` - Write audio samples
- `POST /api/audio/{session_id}/read` - Read audio samples
- `POST /api/audio/{session_id}/process` - Apply audio effects
- `POST /api/audio/upload` - Upload audio file

### WebSocket
- `ws://localhost:8000/ws/audio/{session_id}` - Real-time audio streaming

## 🎛️ Audio Effects

### Reverb
- Room size, damping, dry/wet mix
- Convolution-based reverb implementation

### Delay
- Delay time, feedback, mix control
- Real-time delay with feedback

### Distortion
- Drive and threshold parameters
- Soft clipping and hard limiting

### Filter
- Low-pass, high-pass, band-pass
- Configurable cutoff frequency

### Compression
- Threshold, ratio, attack, release
- Dynamic range compression

### Modulation Effects
- Chorus, Flanger, Phaser
- LFO-based modulation

## 🧪 Testing

### Backend Tests
```bash
cd backend
python audio_buffer.py  # Test the AudioBuffer implementation
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🛠️ Development

### Code Quality
```bash
# Backend linting
cd backend
flake8 .
black .

# Frontend linting
cd frontend
npm run lint
```

### Database Setup
The application uses SQLite by default for development. For production, you can configure PostgreSQL by setting the `DATABASE_URL` environment variable.

## 🚀 Deployment

### Backend Deployment
1. Set up PostgreSQL database (optional)
2. Configure environment variables
3. Deploy to your preferred platform (Heroku, AWS, etc.)

### Frontend Deployment
1. Build the application: `npm run build`
2. Deploy to Vercel, Netlify, or your preferred platform

## 📈 Next Steps & Features to Add

### Immediate Enhancements
- [ ] User Authentication & Authorization
- [ ] Project Management & Saving
- [ ] Effect Presets & Templates
- [ ] Batch Processing
- [ ] Export Options (WAV, MP3, etc.)
- [ ] Real-time Collaboration

### Advanced Features
- [ ] MIDI Support
- [ ] VST Plugin Support
- [ ] Cloud Storage Integration
- [ ] Mobile App
- [ ] AI-powered Audio Enhancement

### Performance Optimizations
- [ ] Web Workers for Audio Processing
- [ ] WebAssembly for Heavy Computations
- [ ] GPU Acceleration
- [ ] Caching (Redis)
- [ ] CDN for Static Assets

### UI/UX Features
- [ ] Dark/Light Theme Toggle
- [ ] Smooth Animations & Transitions
- [ ] Real-time Feedback
- [ ] Intuitive Controls
- [ ] Responsive Layout Improvements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For questions or issues, please open a GitHub issue or contact the development team.

## 🎯 Current Status

✅ **Completed:**
- AudioBuffer implementation with thread safety
- Basic FastAPI backend with WebSocket support
- Next.js frontend with TypeScript
- Audio effects processor
- Database models and configuration
- Real-time audio streaming
- Modern UI with Tailwind CSS

🔄 **In Progress:**
- Advanced audio visualizer
- Effect parameter controls
- File upload and processing

📋 **Planned:**
- User authentication
- Project management
- Advanced effects
- Performance optimizations
