# Multiagent Traffic Control System - Setup & Execution Guide

## Prerequisites

-   Python 3.8+ installed
-   PowerShell (Windows) or Terminal (Mac/Linux)
-   Ollama installed on your system

## Initial Setup

### 1. Virtual Environment Setup

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (Mac/Linux)
source venv/bin/activate
```

### 2. Install Dependencies

```powershell
# Install all required libraries
pip install -r requirements.txt

# If requirements.txt fails, install manually:
pip install langgraph==0.2.34
pip install langchain-ollama==0.2.0
pip install langchain-core==0.3.15
pip install langchain-community==0.3.5
pip install pydantic==2.9.2
pip install asyncio-mqtt==0.16.2
pip install python-dotenv==1.0.1
pip install typing-extensions==4.12.2
```

### 3. Ollama Setup

```powershell
# Start Ollama server (keep this terminal open)
ollama serve

# In a new terminal, pull the required model
ollama pull llama3.1:8b

# Verify model is available
ollama list
```

## Execution Commands

### Main Coordination System

#### Single Episode Runs

```powershell
# Default scenarios (demo, stress, balanced)
python simple_langgraph_coordination.py

# Quick test configuration
python simple_langgraph_coordination.py quick_test

# Full test configuration
python simple_langgraph_coordination.py full_test

# Stress test configuration
python simple_langgraph_coordination.py stress_test

# Assignment demo scenario
python simple_langgraph_coordination.py assignment_demo
```

### Test Runner Scripts

#### Basic Test Modes

```powershell
# Quick test with demo scenario
python test_runner.py quick

# Stress test with challenging scenarios
python test_runner.py stress

# Ablation study comparing configurations
python test_runner.py ablation

# Parameter sensitivity analysis
python test_runner.py sensitivity

# Demonstrate all available scenarios
python test_runner.py scenarios

# Run all tests sequentially
python test_runner.py all
```

#### Multi-Episode Simulation

```powershell
# Run 4-week commitment tracking simulation
python test_runner.py episodes
```

## Configuration Options

### Available Test Configurations

-   `quick_test` - Minimal scenario for rapid testing
-   `full_test` - Comprehensive test with multiple scenarios
-   `stress_test` - High-load scenarios with extreme congestion
-   `assignment_demo` - Custom scenario for assignment demonstration

### Available Scenarios

-   `demo` - 3 classrooms, basic demonstration
-   `stress` - 4 large classrooms, high congestion
-   `balanced` - 4 classrooms, well-distributed load
-   `extreme` - 3 lecture halls, maximum stress test
-   `assignment_demo` - 5 classrooms, Monday 11:00 slot

## Expected Output

### Single Episode Output

```
🚀 Traffic Coordination System
Configuration: default
LLM Model: llama3.1:8b
Risk Threshold: 0.7

=== Running DEMO Scenario ===
📊 RESULTS:
Coordination Success: ✅/❌
Risk Reduction: X.XX (Performance Level)
Final Risk: X.XX
Agents Participated: X

📅 Final Schedule:
  C101 (Mathematics): 12:30 -> 12:28 (-2min)
  ...

🧠 Autonomous Agent Decisions:
  ✅ C101: accept (-2min)
  ...
```

### Multi-Episode Output

```
🗓️ Running Multi-Episode Commitment Test
Scenario: assignment_demo
Episodes: 4, Interval: 7 days

=== EPISODE 1 — Date: 2025-09-28 ===
Risk: 3.65 -> 2.04 (Δ1.62) | Success: ❌
Offers accepted this episode: 2
  • Slot 11:00: C501 -2min (from C502), reciprocal next: +2min
Due commitments processed: 0

=== EPISODE 2 — Date: 2025-10-05 ===
...
Due commitments processed: 2
  • C502 +2min — fulfilled
```

## Troubleshooting

### Common Issues

1. **Import Errors**

    ```powershell
    # Ensure virtual environment is activated
    .\venv\Scripts\Activate.ps1
    # Reinstall dependencies
    pip install -r requirements.txt
    ```

2. **Ollama Connection Issues**

    ```powershell
    # Verify Ollama is running
    ollama list
    # Restart Ollama service
    ollama serve
    ```

3. **Model Not Found**

    ```powershell
    # Pull the required model
    ollama pull llama3.1:8b
    ```

4. **Permission Issues (Windows)**
    ```powershell
    # If activation script fails, try:
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```

## File Structure

```
multiagent_traffic_control/
├── simple_langgraph_coordination.py  # Main coordination system
├── test_runner.py                    # Test execution framework
├── config.py                         # Configuration parameters
├── tools.py                          # Agent tools and utilities
├── requirements.txt                  # Python dependencies
├── output.log                        # Execution logs
└── venv/                             # Virtual environment
```

## Quick Start Commands

```powershell
# Complete setup and run
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama serve  # (in separate terminal)
ollama pull llama3.1:8b
python test_runner.py episodes
```
