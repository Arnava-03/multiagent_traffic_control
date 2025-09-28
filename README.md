# Multiagent Traffic Control System

An autonomous multiagent system using LangGraph and Ollama for intelligent traffic flow coordination in educational environments.

## Overview

This system demonstrates sophisticated autonomous agent reasoning for coordinating classroom dismissals to minimize hallway congestion. The agents use LLM-based decision making to negotiate optimal schedules.

## Quick Start

1. **Activate Environment**:
   ```powershell
   .\agentenv\Scripts\Activate.ps1
   ```

2. **Ensure Ollama is Running**:
   ```powershell
   ollama serve
   ollama pull llama3.2:latest
   ```

3. **Run Basic Demo**:
   ```powershell
   python simple_langgraph_coordination.py
   ```

4. **Run Quick Test**:
   ```powershell
   python simple_langgraph_coordination.py quick_test
   ```

## Configuration System

The system uses a centralized `config.py` file for all parameters, making it easy to test different scenarios and adjust behavior.

### Key Configuration Sections

#### 1. LLM Configuration (`LLM_CONFIG`)
- **model**: Ollama model to use (default: "llama3.2:latest")
- **temperature**: Response randomness (0.0-1.0)
- **timeout**: Request timeout in seconds

#### 2. Negotiation Parameters (`NEGOTIATION_CONFIG`)
- **max_rounds**: Maximum negotiation rounds
- **risk_threshold**: Minimum risk level to trigger coordination
- **coordination_window**: Time window for schedule adjustments (minutes)

#### 3. Risk Thresholds (`RISK_THRESHOLDS`)
Critical levels for different risk categories:
- **low_risk**: Below 0.7
- **medium_risk**: 0.7-1.2  
- **high_risk**: Above 1.2

#### 4. Scenarios (`SCENARIOS`)
Pre-configured test scenarios:
- **demo**: Simple 3-classroom scenario
- **stress**: High-congestion 5-classroom scenario
- **balanced**: Moderate 4-classroom scenario
- **extreme**: Maximum 6-classroom scenario

#### 5. Agent Prompts (`AGENT_PROMPTS`)
Customizable prompts for different agent roles and negotiation phases.

## Testing Different Configurations

### Method 1: Command Line Arguments
```powershell
# Quick test configuration
python simple_langgraph_coordination.py quick_test

# Default configuration  
python simple_langgraph_coordination.py
```

### Method 2: Test Runner Script
```powershell
# Quick demo
python test_runner.py quick

# Stress test with challenging scenarios
python test_runner.py stress

# Parameter sensitivity analysis
python test_runner.py sensitivity

# Ablation study comparing configurations
python test_runner.py ablation

# Demonstrate all scenarios
python test_runner.py scenarios

# Run all tests
python test_runner.py all
```

### Method 3: Modify config.py Directly
Edit `config.py` to adjust any parameters:

```python
# Example: Make agents more flexible
NEGOTIATION_CONFIG = {
    "max_rounds": 5,  # Increased from 3
    "risk_threshold": 0.5,  # Lowered from 0.8
    "coordination_window": 15  # Increased from 10
}

# Example: Create custom scenario
SCENARIOS["custom"] = {
    "description": "My custom test scenario",
    "bottleneck_capacity": 120,
    "classrooms": [
        {
            "id": "ROOM101",
            "students": 30,
            "professor_name": "Dr. Smith",
            "subject": "Math",
            "professor_flexibility": 0.7,
            "scheduled_dismissal": "14:45"
        }
        # Add more classrooms...
    ]
}
```

## Understanding Output

The system provides detailed output including:

### Coordination Metrics
- **Initial Risk**: Congestion level before coordination
- **Final Risk**: Congestion level after coordination  
- **Risk Reduction**: Improvement achieved
- **Coordination Success**: Whether meaningful improvement was achieved
- **Agents Participated**: Number of agents involved in negotiations

### Example Output
```
🎯 COORDINATION EPISODE: demo
📊 Initial Risk Assessment: 1.57

🤝 AGENT NEGOTIATION:
Agent ROOM301 proposes: 14:35 (10 min earlier)
Agent ROOM302 proposes: 14:50 (5 min later)  
Agent ROOM303 proposes: 14:55 (10 min later)

✅ COORDINATION SUCCESS!
📈 Performance Metrics:
  Risk Reduction: 0.54 (1.57 → 1.03)
  Agents Participated: 3
  Coordination Success: True
```

## Configuration Parameters Reference

### Experimentation Parameters

| Parameter | Purpose | Default | Range |
|-----------|---------|---------|-------|
| `professor_flexibility` | How willing professors are to change schedules | 0.6 | 0.0-1.0 |
| `max_schedule_change` | Maximum minutes a class can be moved | 15 | 5-30 |
| `risk_threshold` | Minimum risk to trigger coordination | 0.8 | 0.3-1.5 |
| `coordination_window` | Time window for adjustments | 10 | 5-20 |
| `temperature` | LLM response randomness | 0.1 | 0.0-1.0 |

### Test Configurations

The system includes pre-configured test settings:

- **quick_test**: Minimal scenario for rapid testing
- **ablation_study**: Compare different parameter combinations
- **stress_test**: High-load scenarios
- **sensitivity_analysis**: Parameter sensitivity testing

## Advanced Usage

### Creating Custom Scenarios

1. **Define in config.py**:
```python
SCENARIOS["my_scenario"] = {
    "description": "Custom scenario description",
    "bottleneck_capacity": 100,  # students/minute
    "classrooms": [
        # Classroom definitions...
    ]
}
```

2. **Run the scenario**:
```powershell
# Modify simple_langgraph_coordination.py to use your scenario
python simple_langgraph_coordination.py
```

### Debugging and Analysis

Enable detailed logging by modifying the main script:
```python
# Add at the top of simple_langgraph_coordination.py
import logging
logging.basicConfig(level=logging.INFO)
```

### Performance Tuning

For better performance:
- Reduce `max_rounds` for faster negotiations
- Increase `risk_threshold` to coordinate less frequently
- Adjust `temperature` for more/less deterministic behavior

## System Architecture

- **simple_langgraph_coordination.py**: Main coordination system
- **config.py**: Centralized configuration
- **tools.py**: Agent capabilities and tools
- **test_runner.py**: Automated testing framework
- **requirements_clean.txt**: Dependencies

## Troubleshooting

### Common Issues

1. **Ollama not responding**:
   ```powershell
   ollama serve
   ollama pull llama3.2:latest
   ```

2. **Import errors**:
   ```powershell
   pip install -r requirements_clean.txt
   ```

3. **Configuration not taking effect**:
   - Restart Python interpreter
   - Check for syntax errors in config.py

### Performance Issues

- Reduce `max_rounds` in `NEGOTIATION_CONFIG`
- Increase `timeout` in `LLM_CONFIG`
- Use simpler scenarios for testing

## Contributing

To add new features:

1. **New agent capabilities**: Add to `tools.py`
2. **New scenarios**: Add to `SCENARIOS` in `config.py`
3. **New metrics**: Modify coordination metrics calculation
4. **New test configurations**: Add to `TEST_CONFIGS` in `config.py`

## License

This project demonstrates autonomous multiagent coordination for educational purposes.
