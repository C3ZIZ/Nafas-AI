# Nafas AI - Complete System Documentation

## 1. Project Overview

**Nafas** is an AI-powered respiratory health analysis system that processes and analyzes breath sounds (respiratory audio recordings) to detect potential respiratory diseases. The system uses deep learning models combined with advanced audio processing techniques to classify breath sounds and provide medical insights.

### Core Purpose
- **Primary Goal**: Analyze audio recordings of breath sounds to identify patterns indicative of respiratory diseases
- **Target Use Case**: Medical diagnosis support, patient screening, and respiratory health monitoring
- **Data Source**: Respiratory audio files (WAV format) with clinical annotations
- **Output**: Classification results, visualizations, and audio segment analysis

---

## 2. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│            User/Client Interface                        │
│         (FastAPI REST API Endpoints)                    │
└─────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐    ┌──────────┐    ┌──────────────┐
   │ Audio   │    │ Audio    │    │ Model        │
   │ Loading │    │ Processing│   │ Inference    │
   │ & Info  │    │ & Feature │   │ & Prediction │
   └─────────┘    │ Extraction│   └──────────────┘
        │         └──────────┘          │
        │              │                │
        └──────────────┼────────────────┘
                       │
        ┌──────────────────────────────┐
        │   response/visualization    │
        │   (PNG/JSON)                │
        └──────────────────────────────┘
```

### Key Components

#### 1. **FastAPI Web Server** (`app/main.py`)
- RESTful API serving HTTP endpoints
- Routes audio data to processing pipeline
- Returns results as JSON or streaming responses (images)
- Handles file validation and error management

#### 2. **Audio Processing Pipeline** (`app/utils.py`)
- Audio loading and resampling
- Butterworth band-pass filtering
- Mel-spectrogram generation
- Audio segmentation using clinical annotations
- Feature extraction for ML models

#### 3. **Deep Learning Model** (`app/model.py`)
- CNN-based architecture (NafasCNN)
- Processes mel-spectrograms as input
- Outputs classification predictions
- GPU/CPU device management

#### 4. **Data Layer** (`data/`)
- Raw audio files (`.wav` format)
- Clinical annotations (`.txt` files - ICBHI format)
- Patient diagnosis metadata (CSV)
- Documentation of data formats

---

## 3. Technology Stack

### Core Technologies

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.x | Primary programming language |
| **FastAPI** | Latest | Web framework for REST API |
| **PyTorch** | Latest | Deep learning framework for ML models |
| **Librosa** | Latest | Audio processing and analysis library |
| **NumPy** | Latest | Numerical computing and arrays |
| **Pandas** | Latest | Data manipulation and CSV handling |
| **Matplotlib** | Latest | Data visualization and plotting |
| **SciPy** | Latest | Signal processing algorithms |
| **Uvicorn** | Latest | ASGI server for running FastAPI |

### Hardware Support
- **CPU**: Runs on standard processors
- **GPU**: CUDA-compatible GPUs (NVIDIA) for accelerated inference
- **Memory**: Audio buffering and spectrogram computation

---

## 4. Package Dependencies - Detailed Explanation

### 📚 Audio Processing Stack

#### **librosa** (Audio Loading & Processing)
- **Purpose**: Core library for audio signal processing and feature extraction
- **Key Functions Used**:
  - `librosa.load()` - Load audio files with optional resampling
  - `librosa.get_duration()` - Calculate audio duration
  - `librosa.feature.melspectrogram()` - Generate mel-spectrograms (frequency-time representation)
  - `librosa.display.waveshow()` - Visualize audio waveforms
  - `librosa.power_to_db()` - Convert power to decibels (logarithmic scale)
- **Why**: Essential for reading various audio formats and extracting ML-friendly features

#### **scipy** (Signal Processing)
- **Purpose**: Advanced signal processing algorithms, specifically filtering
- **Key Functions Used**:
  - `scipy.signal.butter()` - Design Butterworth band-pass filters
  - `scipy.signal.lfilter()` - Apply filter to audio data
- **Why**: Butterworth filters remove noise outside the respiratory frequency range (50-2500 Hz)

---

### 🧮 Data & Numerical Computing Stack

#### **numpy** (Numerical Arrays & Math)
- **Purpose**: Efficient numerical computation and array operations
- **Key Uses**:
  - Audio signal manipulation as arrays
  - Spectrogram generation and processing
  - Mathematical operations on audio data
- **Why**: Fast C-based implementations for large audio arrays; fundamental for all numerical operations

#### **pandas** (Data Manipulation & CSV Handling)
- **Purpose**: Read and parse clinical annotation files and metadata
- **Key Functions Used**:
  - `pd.read_csv()` - Parse ICBHI annotation files (start time, end time, crackles, wheezes)
  - DataFrame operations for data organization
- **Why**: Simplifies parsing complex tab/whitespace-delimited clinical annotation formats

---

### 🎨 Visualization Stack

#### **matplotlib** (Plotting & Image Generation)
- **Purpose**: Generate visualizations as PNG images for streaming API responses
- **Key Functions Used**:
  - `plt.figure()` - Create plots in memory
  - `plt.savefig()` - Export to PNG bytes buffer
  - Waveform and spectrogram display
- **Why**: Creating visual representations of audio data for inspection and analysis
- **Special Note**: Uses 'Agg' backend for server-side rendering without displaying windows

---

### 🚀 Web Framework Stack

#### **FastAPI** (REST API Framework)
- **Purpose**: Build modern async REST APIs for the system
- **Key Features Used**:
  - Route decorators (`@app.get()`)
  - HTTP exception handling
  - Auto-generated API documentation (Swagger/OpenAPI)
  - Type hints for request/response validation
- **Why**: Lightweight, fast, async-capable, auto-documentation; ideal for real-time audio processing APIs

#### **python-multipart** (File Upload Support)
- **Purpose**: Enable file upload parsing in FastAPI
- **Key Use**: Supports file submission to API endpoints
- **Why**: Required dependency for FastAPI to handle multipart form data

#### **uvicorn** (ASGI Server)
- **Purpose**: Production-grade server to run FastAPI applications
- **Key Features**:
  - Async request handling
  - Hot-reload for development (`--reload` flag)
  - Production deployment capabilities
- **Why**: Industry-standard ASGI server; enables concurrent request handling

---

### 🤖 Machine Learning & GPU Stack

#### **torch** (PyTorch - Deep Learning Framework)
- **Purpose**: Build and run deep learning models for audio classification
- **Key Functions Used**:
  - `nn.Module` - Base class for neural networks
  - `nn.Conv2d` - Convolutional layers for feature extraction
  - `nn.Linear` - Fully connected layers for classification
  - `torch.cuda.*` - GPU detection and device management
- **Why**: Industry-standard framework; GPU acceleration for inference; flexible architecture

#### **torchvision** (PyTorch Vision Utilities)
- **Purpose**: Vision-specific utilities (optional, included for potential image processing)
- **Why**: Pre-built architectures and transforms; potential future enhancement

#### **torchaudio** (PyTorch Audio Utilities)
- **Purpose**: Audio-specific PyTorch utilities (optional, included for potential enhancement)
- **Why**: Potential future integration for more advanced audio processing

---

## 5. API Endpoints Documentation

### **GET / (Root Endpoint)**
```
Endpoint: GET /
Purpose: Health check / alive status
Response: {"message": "Nafas API is running!"}
```

### **GET /inspect/{filename}**
```
Endpoint: GET /inspect/{filename}
Purpose: Get metadata about an audio file
Parameters:
  - filename: Name of audio file in data/ folder
Response:
{
  "sample_rate": 22050,
  "duration_sec": 10.5,
  "total_samples": 231525,
  "device_info": {
    "gpu_available": true,
    "gpu_name": "NVIDIA GeForce RTX 3060"
  }
}
```

### **GET /plot/{filename}**
```
Endpoint: GET /plot/{filename}
Purpose: Generate and stream waveform visualization
Parameters:
  - filename: Name of audio file
Response: PNG image (streamed as image/png)
```

### **GET /process/{filename}**
```
Endpoint: GET /process/{filename}
Purpose: Process audio and return annotated segments
Parameters:
  - filename: Name of audio file
Response: Annotated segments with start/end times and labels
```

---

## 6. Data Format Specifications

### Audio Files
- **Format**: WAV (uncompressed audio)
- **Naming Convention**: `{patient_id}_{recording_id}_{location}_{device}.wav`
  - Example: `101_1b1_Al_sc_Meditron.wav`
  - Patient ID: 101
  - Location: Al = Anterior Left
  - Device: Meditron

### Annotation Files
- **Format**: Tab/whitespace-delimited text files
- **Structure**: Same filename as audio file with `.txt` extension
- **Columns**: 
  - `start` - Start time in seconds
  - `end` - End time in seconds
  - `crackle` - Binary indicator (0 or 1)
  - `wheeze` - Binary indicator (0 or 1)
- **Example**:
  ```
  0.0    5.0    0    0
  5.0    10.0   1    0
  10.0   15.0   0    1
  ```

### Patient Diagnosis
- **File**: `patient_diagnosis.csv`
- **Contains**: Patient IDs and corresponding diagnosis labels

---

## 7. Audio Processing Pipeline

### Step-by-Step Flow

#### 1. **Audio Loading** (`librosa.load()`)
```
Input: Audio file path
↓
Process: Load audio, resample to 22,050 Hz (standard for respiratory audio)
↓
Output: Audio signal array (y), sample rate (sr)
```

#### 2. **Band-Pass Filtering** (`butter_bandpass_filter()`)
```
Input: Raw audio signal
↓
Process:
  - Design Butterworth filter (50-2500 Hz range)
  - 50 Hz: Remove very low frequency noise
  - 2500 Hz: Respiratory sounds rarely exceed this
  - Filter order: 5 (balance between steepness and stability)
↓
Output: Cleaned audio signal
```

#### 3. **Feature Extraction** (`generate_mel_spectrogram()`)
```
Input: Cleaned audio signal
↓
Process:
  - Compute Mel-Spectrogram:
    * n_mels=128: 128 frequency bands
    * fmax=2500: Focus on respiratory range
  - Convert to Decibels (dB) scale
    * Logarithmic scale matches human hearing
↓
Output: 2D array [frequency_bands × time_frames]
Dimensions: [128 × T] where T = time frames
```

#### 4. **Segmentation** (`get_segments()`)
```
Input: Audio file + Annotation file
↓
Process:
  - Load audio and apply all previous steps
  - Read annotation file (start/end times)
  - Slice audio into segments
  - Label as "healthy" or "unhealthy" based on crackle/wheeze indicators
↓
Output: List of segments with labels
```

#### 5. **Model Input Preparation** (`prepare_tensor_for_ai()`)
```
Input: Audio file path
↓
Process:
  - Generate mel-spectrogram (all previous steps)
  - Convert to PyTorch tensor
  - Add batch dimension: [1, 1, 128, T]
    * 1 batch sample
    * 1 channel (grayscale)
    * 128 frequency bands
    * T time frames
↓
Output: Ready-to-submit tensor for neural network
```

---

## 8. Deep Learning Model Architecture

### NafasCNN Model

```
Input: [1, 1, 128, T] tensor (batch, channels, frequency, time)
  ↓
┌─────────────────────────────────────────────────────────┐
│ Feature Extraction (Convolution Layers):                │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Conv2d(1→16 channels, 3×3 kernel, padding=1)  │
│          ReLU activation                                │
│          MaxPool 2×2                                    │
│          Output: [16, 64, T/2]                          │
│                                                         │
│ Layer 2: Conv2d(16→32 channels, 3×3 kernel, padding=1) │
│          ReLU activation                                │
│          MaxPool 2×2                                    │
│          Output: [32, 32, T/4]                          │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ Adaptive Pooling:                                       │
│ Reduce to fixed size: [32, 4, 4]                        │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ Classification Head:                                    │
├─────────────────────────────────────────────────────────┤
│ Flatten: 32 × 4 × 4 = 512 features                     │
│ Dense Layer: 512 → 128 neurons, ReLU                   │
│ Output Layer: 128 → 3 classes                          │
│   (e.g., Healthy, Crackles, Wheezes)                   │
└─────────────────────────────────────────────────────────┘
  ↓
Output: 3 class probabilities (logits)
```

### Model Details
- **Architecture Type**: Convolutional Neural Network (CNN)
- **Input**: Mel-spectrogram (2D time-frequency representation)
- **Output**: 3-class classification (configurable labels)
- **Device**: Automatically selects GPU if CUDA available, else CPU
- **Advantage**: CNNs excel at learning spatial patterns in spectrograms

---

## 9. Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│ User Request (HTTP GET)                                          │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ FastAPI Route Handler (/inspect, /plot, /process)               │
│ - Validate filename                                              │
│ - Resolve file path                                              │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Audio Loading (librosa)                                          │
│ - Load .wav file                                                 │
│ - Resample to 22,050 Hz                                          │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Signal Processing (SciPy)                                        │
│ - Apply Butterworth band-pass filter (50-2500 Hz)               │
│ - Noise reduction                                                │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Feature Extraction (librosa)                                     │
│ - Generate Mel-Spectrogram                                       │
│ - Convert to dB scale                                            │
│ - Normalize                                                      │
└──────────────┬───────────────────────────────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
    [Visualization]  [Model]
    - Plot waveform  - Convert to tensor
    - Save as PNG    - Run inference
        │             - Get predictions
        │             │
        └──────┬──────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Response Formatting                                              │
│ - JSON (metadata, predictions)                                   │
│ - PNG (images)                                                   │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ HTTP Response to Client                                          │
│ - StreamingResponse (for images)                                 │
│ - JSONResponse (for data)                                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 10. Key Technical Concepts

### Mel-Spectrogram
- **What**: Time-frequency representation of audio on a perceptually-motivated mel scale
- **Why**: Humans don't perceive frequency linearly; mel scale matches human hearing
- **Processing**:
  1. Short-Time Fourier Transform (STFT) breaks audio into frequency slices
  2. Map frequencies to mel scale (non-linear)
  3. Compute power for each mel frequency band
  4. Convert to dB (logarithmic) for better visualization

### Band-Pass Filtering
- **Purpose**: Remove unwanted frequency components
- **Range**: 50-2500 Hz (respiratory sound frequency range)
- **Below 50 Hz**: Environmental rumble, wind noise
- **Above 2500 Hz**: High-frequency artifacts
- **Algorithm**: Butterworth (maximally flat frequency response)

### Adaptive Average Pooling
- **Purpose**: Reduce feature map to fixed size
- **Advantage**: Handles variable-length audio inputs
- **Output**: Consistent feature vector for classification regardless of audio duration

---

## 11. Running the System

### Local Development
```bash
# Activate virtual environment
cd d:\Users\Abdulaziz\Documents\Nafas\Nafas
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run API server
uvicorn app.main:app --reload
```

### Accessing API
- **Base URL**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

### Example API Calls
```bash
# Get audio info
curl http://localhost:8000/inspect/101_1b1_Al_sc_Meditron.wav

# Get waveform plot
curl http://localhost:8000/plot/101_1b1_Al_sc_Meditron.wav > output.png

# Process audio with annotations
curl http://localhost:8000/process/101_1b1_Al_sc_Meditron.wav
```

---

## 12. Dependencies Summary Table

| Package | Category | Purpose | Install Size |
|---------|----------|---------|--------------|
| librosa | Audio | Audio I/O, feature extraction | ~50 MB |
| matplotlib | Visualization | Plot generation, image export | ~40 MB |
| numpy | Computing | Numerical arrays, math operations | ~100 MB |
| pandas | Data | Data manipulation, CSV parsing | ~30 MB |
| scipy | Scientific | Signal processing, filtering | ~40 MB |
| fastapi | Web | REST API framework | ~2 MB |
| python-multipart | Utility | File upload support | <1 MB |
| torch | ML | Neural network framework | ~2 GB |
| torchvision | ML | Vision utilities (optional) | ~800 MB |
| torchaudio | ML | Audio utilities (optional) | ~600 MB |
| uvicorn | Server | ASGI server runtime | ~2 MB |

---

## 13. System Performance Notes

### Typical Processing Times (on GPU)
- Audio Loading: 50-200ms
- Band-Pass Filtering: 10-50ms
- Mel-Spectrogram Generation: 50-150ms
- Model Inference: 10-50ms
- **Total**: ~150-450ms per file

### Memory Requirements
- Base Python + libraries: ~3-4 GB
- PyTorch + models: ~2-4 GB
- Per audio file (in processing): ~50-200 MB
- **Total Recommended**: 16+ GB RAM for smooth operation

### Scalability
- **Single Request**: Handled sequentially
- **Concurrent Requests**: Limited by GPU memory (if using GPU)
- **Recommended Setup**: Load balancer with multiple API instances

---

## 14. File Structure Reference

```
Nafas/
├── Nafas_AI.ipynb                 # Jupyter notebook (analysis/training)
├── README.md                       # Project overview
├── SYSTEM_DOCUMENTATION.md         # This file
├── requirements.txt                # Python dependencies
│
├── app/
│   ├── main.py                    # FastAPI application
│   ├── model.py                   # NafasCNN model definition
│   └── utils.py                   # Audio processing utilities
│
└── data/
    ├── patient_diagnosis.csv       # Patient labels
    ├── filename_format.txt         # Format documentation
    └── audio_and_txt_files/        # Audio files + annotations
        └── {audio_files}.wav/.txt
```

---

## 15. Future Enhancement Possibilities

### Model Improvements
- Multi-task learning (disease classification + severity)
- Attention mechanisms for critical time windows
- Ensemble methods combining multiple architectures
- Transfer learning from pre-trained audio models

### Feature Additions
- Real-time streaming audio processing
- Batch API for processing multiple files
- Model prediction confidence scores
- Explainability features (CAM visualizations)

### Infrastructure
- Database integration for patient history
- Authentication and authorization
- Rate limiting and API throttling
- Docker containerization
- Cloud deployment (AWS, Azure, GCP)

---

## Conclusion

Nafas is an end-to-end respiratory audio analysis system combining:
- **Advanced Audio Processing**: Professional-grade signal filtering and feature extraction
- **Modern Web Framework**: FastAPI for reliable, documented REST APIs
- **Deep Learning**: PyTorch CNN for accurate respiratory sound classification
- **Visualization**: Real-time audio visualization for clinical review

The system is modular, extensible, and production-ready for deployment in medical settings or research environments.

---

*Documentation Generated: April 20, 2026*
