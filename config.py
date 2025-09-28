"""
Configuration file for Traffic Coordination System
Centralized parameters for easy testing and experimentation
"""

# ==========================================
# LLM CONFIGURATION
# ==========================================
LLM_CONFIG = {
    "model": "llama3.2:latest",
    "temperature": 0.7,
    "base_url": "http://localhost:11434",
    "timeout": 120,  # seconds
    "max_retries": 3
}

# ==========================================
# NEGOTIATION PARAMETERS
# ==========================================
NEGOTIATION_CONFIG = {
    "risk_threshold": 0.7,  # Threshold for triggering negotiations (0.0-2.0+)
    "max_negotiation_rounds": 3,
    "agents_per_negotiation": 2,  # Number of top agents selected for negotiation
    "default_adjustment_minutes": 2,  # Default adjustment amount
    "max_adjustment_minutes": 8,  # Maximum allowed adjustment
    "negotiation_timeout": 300  # seconds
}

# ==========================================
# RISK AND CONGESTION THRESHOLDS
# ==========================================
RISK_THRESHOLDS = {
    "normal": 0.7,      # Below this is normal traffic
    "moderate": 1.0,    # 0.7-1.0 is moderate congestion
    "high": 1.5,        # 1.0-1.5 is high congestion
    "critical": 1.5     # Above this is critical congestion
}

# ==========================================
# FEASIBILITY CALCULATION PARAMETERS
# ==========================================
FEASIBILITY_CONFIG = {
    "high_flexibility_threshold": 0.3,      # Professor flexibility > 0.3 is high
    "low_flexibility_threshold": -0.3,      # Professor flexibility < -0.3 is low
    "base_feasibility_score": 0.6,          # Starting feasibility score
    "flexibility_bonus": 0.2,               # Bonus for high flexibility
    "flexibility_penalty": 0.3,             # Penalty for opposing preferences
    "adjustment_penalty_per_minute": 0.05,  # Penalty per minute of adjustment
    "constraint_violation_penalty": 0.7     # Penalty for exceeding max adjustment
}

# ==========================================
# REPUTATION AND COMMITMENT PARAMETERS
# ==========================================
REPUTATION_CONFIG = {
    "initial_reputation": 1.0,         # Starting reputation score
    "fulfillment_bonus": 0.1,          # Bonus for fulfilling commitments
    "violation_penalty": 0.2,          # Penalty for violating commitments
    "violation_threshold": 3,          # Number of violations before flagging
    "min_reputation": 0.0,             # Minimum reputation score
    "max_reputation": 1.0              # Maximum reputation score
}

# ==========================================
# SIMULATION SCENARIOS
# ==========================================
SCENARIOS = {
    "demo": {
        "name": "Demo Scenario",
        "description": "Basic demonstration with 3 classrooms",
        "classrooms": [
            {
                "id": "C101",
                "students": 80,
                "professor_flexibility": 0.3,
                "base_end_time": "12:30",
                "subject": "Mathematics",
                "professor_name": "Dr. Smith"
            },
            {
                "id": "C102", 
                "students": 95,
                "professor_flexibility": -0.2,
                "base_end_time": "12:30",
                "subject": "Chemistry",
                "professor_name": "Prof. Johnson"
            },
            {
                "id": "C103",
                "students": 60,
                "professor_flexibility": 0.5,
                "base_end_time": "12:30",
                "subject": "Literature",
                "professor_name": "Dr. Davis"
            }
        ],
        "bottleneck_capacity": 150
    },
    
    "stress": {
        "name": "Stress Test Scenario",
        "description": "High congestion scenario with 4 large classrooms",
        "classrooms": [
            {
                "id": "C201",
                "students": 120,
                "professor_flexibility": -0.7,
                "base_end_time": "12:30",
                "subject": "Engineering",
                "professor_name": "Dr. Wilson"
            },
            {
                "id": "C202",
                "students": 110,
                "professor_flexibility": 0.8,
                "base_end_time": "12:30",
                "subject": "Philosophy",
                "professor_name": "Prof. Martinez"
            },
            {
                "id": "C203",
                "students": 95,
                "professor_flexibility": 0.2,
                "base_end_time": "12:30",
                "subject": "Biology",
                "professor_name": "Dr. Chen"
            },
            {
                "id": "C204",
                "students": 85,
                "professor_flexibility": -0.5,
                "base_end_time": "12:30",
                "subject": "History",
                "professor_name": "Prof. Thompson"
            }
        ],
        "bottleneck_capacity": 100
    },
    
    "balanced": {
        "name": "Balanced Load Scenario",
        "description": "Well-distributed load with mixed flexibility",
        "classrooms": [
            {
                "id": "C301",
                "students": 70,
                "professor_flexibility": 0.4,
                "base_end_time": "12:30",
                "subject": "Computer Science",
                "professor_name": "Dr. Lee"
            },
            {
                "id": "C302",
                "students": 75,
                "professor_flexibility": -0.1,
                "base_end_time": "12:30",
                "subject": "Psychology",
                "professor_name": "Prof. Garcia"
            },
            {
                "id": "C303",
                "students": 65,
                "professor_flexibility": 0.6,
                "base_end_time": "12:30",
                "subject": "Art History",
                "professor_name": "Dr. Brown"
            },
            {
                "id": "C304",
                "students": 80,
                "professor_flexibility": -0.3,
                "base_end_time": "12:30",
                "subject": "Economics",
                "professor_name": "Prof. Taylor"
            }
        ],
        "bottleneck_capacity": 120
    },
    
    "extreme": {
        "name": "Extreme Congestion Scenario",
        "description": "Maximum stress test with very high congestion",
        "classrooms": [
            {
                "id": "C401",
                "students": 150,
                "professor_flexibility": -0.9,
                "base_end_time": "12:30",
                "subject": "Lecture Hall A",
                "professor_name": "Dr. Anderson"
            },
            {
                "id": "C402",
                "students": 140,
                "professor_flexibility": 0.9,
                "base_end_time": "12:30",
                "subject": "Lecture Hall B", 
                "professor_name": "Prof. White"
            },
            {
                "id": "C403",
                "students": 130,
                "professor_flexibility": 0.1,
                "base_end_time": "12:30",
                "subject": "Lecture Hall C",
                "professor_name": "Dr. Miller"
            }
        ],
        "bottleneck_capacity": 80
    }
}

# ==========================================
# LOGGING CONFIGURATION
# ==========================================
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "output.log",
    "console_output": True,
    "detailed_decisions": True,  # Log detailed agent decision reasoning
    "performance_metrics": True  # Log performance timing
}

# ==========================================
# AGENT DECISION PROMPTS
# ==========================================
AGENT_PROMPTS = {
    "bottleneck_system": """You are a Traffic Bottleneck Agent responsible for analyzing classroom exit patterns and preventing congestion.

Your role:
- Analyze traffic flow data and identify congestion points
- Generate intelligent recommendations for traffic management
- Consider both immediate needs and long-term coordination patterns

Provide specific, actionable recommendations for classroom timing adjustments.
Focus on practical solutions that balance efficiency with fairness.""",

    "bottleneck_human": """Current traffic analysis shows:
- Total students: {total_students}
- Bottleneck capacity: {capacity} students/minute
- Congestion risk: {risk}
- Critical time slots: {critical_times}

Based on this analysis, provide 2-3 specific recommendations for classroom timing adjustments.
Format your response as a JSON object with recommendations.""",

    "classroom_system": """You are Classroom Agent {classroom_id}, representing a classroom in a traffic coordination system.

Your characteristics:
- Students: {students}
- Professor: {professor_name} ({subject})
- Professor flexibility: {flexibility} (-1.0 to 1.0, negative means prefers shorter classes)
- Base end time: {base_end_time}
- Reputation score: {reputation}

Your goal is to balance:
1. Professor preferences and constraints
2. Student flow efficiency 
3. Cooperative behavior with other classrooms
4. Long-term reputation maintenance

Make autonomous decisions about timing adjustments.""",

    "classroom_human": """Traffic situation analysis:
Congestion risk: {risk}
Your class size: {students} students
Bottleneck capacity: {capacity} students/minute

Feasibility analysis for {adjustment} minute adjustment:
- Feasibility score: {feasibility_score}
- Is feasible: {is_feasible}
- Professor preference alignment: {preference_alignment}

Based on your classroom's constraints and the traffic situation, decide:
1. Will you accept a timing adjustment?
2. What adjustment amount makes sense?
3. What are your autonomous reasoning steps?

Provide your response as JSON with: decision, proposed_adjustment, reasoning"""
}

# ==========================================
# EXPERIMENTAL PARAMETERS
# ==========================================
EXPERIMENTAL_CONFIG = {
    "enable_commitment_tracking": True,   # Enable multi-episode commitments
    "enable_reputation_system": True,    # Enable reputation-based decisions
    "enable_llm_reasoning": True,        # Use LLM for decisions vs rule-based
    "enable_detailed_logging": True,     # Log detailed decision processes
    "simulation_speed": "normal",        # "fast", "normal", "slow"
    "random_seed": 42,                   # For reproducible experiments
    "max_episodes": 10,                  # Maximum episodes in multi-episode runs
    "episode_interval_days": 7           # Days between episodes
}

# ==========================================
# TESTING CONFIGURATIONS
# ==========================================
TEST_CONFIGS = {
    "quick_test": {
        "scenarios": ["demo"],
        "llm_temperature": 0.3,
        "negotiation_timeout": 60,
        "detailed_logging": False
    },
    
    "full_test": {
        "scenarios": ["demo", "stress", "balanced"],
        "llm_temperature": 0.7,
        "negotiation_timeout": 300,
        "detailed_logging": True
    },
    
    "stress_test": {
        "scenarios": ["stress", "extreme"],
        "llm_temperature": 0.8,
        "negotiation_timeout": 600,
        "detailed_logging": True,
        "max_episodes": 5
    },
    
    "ablation_study": {
        "scenarios": ["balanced"],
        "test_variations": [
            {"enable_llm_reasoning": False, "name": "rule_based"},
            {"enable_llm_reasoning": True, "llm_temperature": 0.1, "name": "low_temp"},
            {"enable_llm_reasoning": True, "llm_temperature": 0.9, "name": "high_temp"},
            {"risk_threshold": 0.5, "name": "low_threshold"},
            {"risk_threshold": 1.0, "name": "high_threshold"}
        ]
    }
}

# ==========================================
# PERFORMANCE THRESHOLDS
# ==========================================
PERFORMANCE_METRICS = {
    "excellent_risk_reduction": 0.5,     # Risk reduction > 0.5 is excellent
    "good_risk_reduction": 0.3,          # Risk reduction > 0.3 is good
    "acceptable_risk_reduction": 0.1,    # Risk reduction > 0.1 is acceptable
    "max_acceptable_final_risk": 1.0,    # Final risk should be <= 1.0
    "min_agent_participation": 0.5,      # At least 50% of agents should participate
    "max_negotiation_time": 300          # Max time for negotiations (seconds)
}

# ==========================================
# UTILITY FUNCTIONS
# ==========================================
def get_scenario_config(scenario_name: str) -> dict:
    """Get configuration for a specific scenario"""
    return SCENARIOS.get(scenario_name, SCENARIOS["demo"])

def get_test_config(test_name: str) -> dict:
    """Get configuration for a specific test"""
    return TEST_CONFIGS.get(test_name, TEST_CONFIGS["quick_test"])

def get_flexibility_description(flexibility: float) -> str:
    """Convert numerical flexibility to human-readable description"""
    if flexibility <= -0.5:
        return "strongly prefers shorter lectures"
    elif flexibility <= -0.2:
        return "prefers shorter lectures"
    elif flexibility >= 0.5:
        return "strongly prefers longer lectures"
    elif flexibility >= 0.2:
        return "prefers longer lectures"
    else:
        return "flexible with lecture timing"

def calculate_suggested_adjustment(professor_flexibility: float) -> int:
    """Calculate suggested adjustment based on professor flexibility"""
    if professor_flexibility < -FEASIBILITY_CONFIG["low_flexibility_threshold"]:
        return -NEGOTIATION_CONFIG["default_adjustment_minutes"]
    elif professor_flexibility > FEASIBILITY_CONFIG["high_flexibility_threshold"]:
        return NEGOTIATION_CONFIG["default_adjustment_minutes"]
    else:
        return NEGOTIATION_CONFIG["default_adjustment_minutes"] if professor_flexibility >= 0 else -NEGOTIATION_CONFIG["default_adjustment_minutes"]

# ==========================================
# VALIDATION FUNCTIONS
# ==========================================
def validate_config():
    """Validate configuration parameters"""
    errors = []
    
    # Validate risk thresholds
    if not (0 <= RISK_THRESHOLDS["normal"] <= RISK_THRESHOLDS["moderate"] <= RISK_THRESHOLDS["high"]):
        errors.append("Risk thresholds must be in ascending order")
    
    # Validate feasibility thresholds
    if FEASIBILITY_CONFIG["low_flexibility_threshold"] >= FEASIBILITY_CONFIG["high_flexibility_threshold"]:
        errors.append("Low flexibility threshold must be less than high flexibility threshold")
    
    # Validate reputation bounds
    if REPUTATION_CONFIG["min_reputation"] >= REPUTATION_CONFIG["max_reputation"]:
        errors.append("Min reputation must be less than max reputation")
    
    # Validate scenarios
    for scenario_name, scenario in SCENARIOS.items():
        if scenario["bottleneck_capacity"] <= 0:
            errors.append(f"Scenario {scenario_name}: bottleneck capacity must be positive")
        
        for classroom in scenario["classrooms"]:
            if not (-1.0 <= classroom["professor_flexibility"] <= 1.0):
                errors.append(f"Scenario {scenario_name}, {classroom['id']}: flexibility must be between -1.0 and 1.0")
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))
    
    return True

# Validate configuration on import
if __name__ == "__main__":
    validate_config()
    print("Configuration validation passed!")
else:
    validate_config()
