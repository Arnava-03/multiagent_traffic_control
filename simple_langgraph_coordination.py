"""
Simplified LangGraph-based Traffic Coordination System with Ollama
Autonomous agent reasoning for classroom traffic coordination - Working Version
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from tools import (
    ClassroomState, ClassroomCommitment, BottleneckTools, 
    ClassroomTools, CommitmentTracker
)
import config

class SimpleTrafficCoordinationSystem:
    """Simplified LangGraph-based traffic coordination system with Ollama"""
    
    def __init__(self, test_config_name: str = None):
        # Load configuration from config.py
        self.config = config
        
        # Apply test configuration if specified
        if test_config_name:
            test_config = config.get_test_config(test_config_name)
            self._apply_test_config(test_config)
        
        # Initialize LLM with config parameters
        self.llm = ChatOllama(
            model=config.LLM_CONFIG["model"],
            temperature=config.LLM_CONFIG["temperature"],
            base_url=config.LLM_CONFIG["base_url"]
        )
        self.commitment_tracker = CommitmentTracker()
        self.logger = self._setup_logging()
    
    def _apply_test_config(self, test_config: dict):
        """Apply test-specific configuration overrides"""
        if "llm_temperature" in test_config:
            config.LLM_CONFIG["temperature"] = test_config["llm_temperature"]
        if "negotiation_timeout" in test_config:
            config.NEGOTIATION_CONFIG["negotiation_timeout"] = test_config["negotiation_timeout"]
        if "detailed_logging" in test_config:
            config.LOGGING_CONFIG["detailed_decisions"] = test_config["detailed_logging"]
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        handlers = [
            logging.FileHandler(config.LOGGING_CONFIG["file"])
        ]
        
        if config.LOGGING_CONFIG["console_output"]:
            handlers.append(logging.StreamHandler())
        
        logging.basicConfig(
            level=getattr(logging, config.LOGGING_CONFIG["level"]),
            format=config.LOGGING_CONFIG["format"],
            handlers=handlers
        )
        return logging.getLogger(__name__)
    
    async def run_coordination_episode(self, scenario_name: str, episode_date: str = None) -> Dict[str, Any]:
        """Run a complete coordination episode"""
        if episode_date is None:
            episode_date = datetime.now().strftime("%Y-%m-%d")
        
        scenario = config.get_scenario_config(scenario_name)
        
        # Initialize classroom states
        classroom_states = []
        for classroom_config in scenario["classrooms"]:
            classroom_state = ClassroomState(
                classroom_id=classroom_config["id"],
                current_students=classroom_config["students"],
                professor_flexibility=classroom_config["professor_flexibility"],
                base_end_time=classroom_config["base_end_time"]
            )
            classroom_states.append(classroom_state)
        
        self.logger.info(f"Starting coordination episode: {scenario_name} on {episode_date}")
        
        # Phase 1: Bottleneck Analysis
        analysis = await self._bottleneck_analysis_phase(classroom_states, scenario["bottleneck_capacity"])
        
        # Phase 2: Autonomous Agent Negotiations  
        negotiation_results = await self._negotiation_phase(classroom_states, analysis, episode_date)
        
        # Phase 3: Final Coordination
        final_results = await self._final_coordination_phase(classroom_states, analysis, negotiation_results, episode_date)
        
        return final_results
    
    async def _bottleneck_analysis_phase(self, classroom_states: List[ClassroomState], capacity: int) -> Dict[str, Any]:
        """Phase 1: Bottleneck agent analyzes traffic and generates recommendations"""
        self.logger.info("Phase 1: Bottleneck Analysis")
        
        # Analyze current traffic situation using tools
        analysis = BottleneckTools.analyze_traffic_flow(classroom_states, capacity)
        
        # Use LLM for intelligent analysis and recommendation generation
        bottleneck_prompt = ChatPromptTemplate.from_messages([
            ("system", config.AGENT_PROMPTS["bottleneck_system"]),
            ("human", config.AGENT_PROMPTS["bottleneck_human"])
        ])
        
        messages = bottleneck_prompt.format_messages(
            total_students=analysis["total_students"],
            capacity=capacity,
            risk=analysis["max_congestion_ratio"],
            critical_times=analysis["critical_time_slots"]
        )
        
        try:
            response = await self.llm.ainvoke(messages)
            llm_recommendations = self._parse_llm_response(response.content)
            self.logger.info(f"Bottleneck Agent: Generated LLM-based recommendations")
            
            # Merge with tool-based recommendations
            analysis["llm_recommendations"] = llm_recommendations
            
        except Exception as e:
            self.logger.error(f"Bottleneck Agent LLM error: {e}")
            analysis["llm_recommendations"] = {"error": str(e)}
        
        return analysis
    
    async def _negotiation_phase(self, classroom_states: List[ClassroomState], 
                                analysis: Dict[str, Any], episode_date: str) -> List[Dict[str, Any]]:
        """Phase 2: Classroom agents negotiate autonomously using LLM reasoning"""
        self.logger.info("Phase 2: Autonomous Agent Negotiations")
        
        negotiation_results = []
        
        # Identify agents that need to negotiate based on analysis
        agents_needing_negotiation = []
        if analysis["max_congestion_ratio"] > config.NEGOTIATION_CONFIG["risk_threshold"]:
            # Get the top agents contributing to congestion
            agents_needing_negotiation = sorted(
                classroom_states, 
                key=lambda cs: cs.current_students, 
                reverse=True
            )[:config.NEGOTIATION_CONFIG["agents_per_negotiation"]]
        
        if not agents_needing_negotiation:
            self.logger.info("No negotiations needed - congestion risk is manageable")
            return negotiation_results
        
        # Each agent makes autonomous decisions
        for classroom_state in agents_needing_negotiation:
            negotiation_result = await self._autonomous_agent_decision(
                classroom_state, analysis, episode_date
            )
            negotiation_results.append(negotiation_result)
        
        return negotiation_results
    
    async def _autonomous_agent_decision(self, classroom_state: ClassroomState, 
                                       analysis: Dict[str, Any], episode_date: str) -> Dict[str, Any]:
        """Individual classroom agent makes autonomous decision using LLM"""
        
        # Evaluate feasibility using tools
        suggested_adjustment = config.calculate_suggested_adjustment(classroom_state.professor_flexibility)
        feasibility = ClassroomTools.evaluate_adjustment_feasibility(
            classroom_state, suggested_adjustment
        )
        
        # Get classroom details from scenario
        classroom_details = self._get_classroom_details(classroom_state.classroom_id)
        
        # Use LLM for autonomous decision making
        classroom_prompt = ChatPromptTemplate.from_messages([
            ("system", config.AGENT_PROMPTS["classroom_system"].format(
                classroom_id=classroom_state.classroom_id,
                students=classroom_state.current_students,
                professor_name=classroom_details.get("professor_name", "Unknown"),
                subject=classroom_details.get("subject", "Unknown"),
                flexibility=classroom_state.professor_flexibility,
                base_end_time=classroom_state.base_end_time,
                reputation=classroom_state.reputation_score
            )),
            ("human", config.AGENT_PROMPTS["classroom_human"])
        ])
        
        messages = classroom_prompt.format_messages(
            risk=analysis["max_congestion_ratio"],
            students=classroom_state.current_students,
            capacity=analysis["capacity_per_minute"],
            adjustment=suggested_adjustment,
            feasibility_score=feasibility["feasibility_score"],
            is_feasible=feasibility["is_feasible"],
            preference_alignment=feasibility["professor_preference_alignment"]
        )
        
        try:
            response = await self.llm.ainvoke(messages)
            decision_data = self._parse_llm_response(response.content)
            
            self.logger.info(f"Classroom {classroom_state.classroom_id}: Autonomous decision - {decision_data.get('decision', 'no_decision')}")
            
            # Apply the decision
            if decision_data.get("decision") == "accept" or decision_data.get("proposed_adjustment", 0) != 0:
                adjustment = decision_data.get("proposed_adjustment", suggested_adjustment)
                # Ensure adjustment is an integer
                if isinstance(adjustment, dict) or adjustment is None:
                    adjustment = suggested_adjustment
                classroom_state.current_adjustment = int(adjustment)
                
            return {
                "classroom_id": classroom_state.classroom_id,
                "decision": decision_data.get("decision", "no_decision"),
                "proposed_adjustment": decision_data.get("proposed_adjustment", 0),
                "reasoning": decision_data.get("reasoning", "Autonomous LLM decision"),
                "feasibility_score": feasibility["feasibility_score"],
                "applied_adjustment": classroom_state.current_adjustment
            }
            
        except Exception as e:
            self.logger.error(f"Classroom {classroom_state.classroom_id} LLM error: {e}")
            
            # Fallback to tool-based decision
            if feasibility["is_feasible"]:
                classroom_state.current_adjustment = int(suggested_adjustment)
                
            return {
                "classroom_id": classroom_state.classroom_id,
                "decision": "accept" if feasibility["is_feasible"] else "reject",
                "proposed_adjustment": suggested_adjustment if feasibility["is_feasible"] else 0,
                "reasoning": f"Tool-based fallback decision: feasibility={feasibility['feasibility_score']:.2f}",
                "feasibility_score": feasibility["feasibility_score"],
                "applied_adjustment": classroom_state.current_adjustment,
                "error": str(e)
            }
    
    async def _final_coordination_phase(self, classroom_states: List[ClassroomState], 
                                      analysis: Dict[str, Any], negotiation_results: List[Dict[str, Any]], 
                                      episode_date: str) -> Dict[str, Any]:
        """Phase 3: Final coordination and result compilation"""
        self.logger.info("Phase 3: Final Coordination")
        
        # Calculate final exit times
        final_schedule = {}
        for classroom_state in classroom_states:
            final_time = BottleneckTools.calculate_exit_time(
                classroom_state.base_end_time,
                classroom_state.current_adjustment
            )
            final_schedule[classroom_state.classroom_id] = {
                "base_time": classroom_state.base_end_time,
                "adjustment": classroom_state.current_adjustment,
                "final_time": final_time,
                "students": classroom_state.current_students
            }
        
        # Analyze final traffic distribution
        final_analysis = BottleneckTools.analyze_traffic_flow(
            classroom_states,
            analysis["capacity_per_minute"]
        )
        
        # Calculate coordination effectiveness
        initial_risk = analysis["max_congestion_ratio"]
        final_risk = final_analysis["max_congestion_ratio"]
        risk_reduction = max(0, initial_risk - final_risk)
        
        coordination_success = (final_analysis["overall_status"] in ["normal", "moderate"] and 
                               final_risk <= config.PERFORMANCE_METRICS["max_acceptable_final_risk"])
        
        # Log results
        self.logger.info("=== COORDINATION RESULTS ===")
        self.logger.info(f"Episode: {episode_date}")
        self.logger.info(f"Initial Risk: {initial_risk:.2f} -> Final Risk: {final_risk:.2f}")
        self.logger.info(f"Risk Reduction: {risk_reduction:.2f}")
        self.logger.info(f"Coordination Success: {coordination_success}")
        
        for classroom_id, schedule in final_schedule.items():
            self.logger.info(f"{classroom_id}: {schedule['base_time']} -> {schedule['final_time']} ({schedule['adjustment']:+d}min)")
        
        # Compile comprehensive results
        results = {
            "episode_date": episode_date,
            "initial_analysis": analysis,
            "final_analysis": final_analysis,
            "negotiation_results": negotiation_results,
            "final_schedule": final_schedule,
            "coordination_metrics": {
                "initial_risk": initial_risk,
                "final_risk": final_risk,
                "risk_reduction": risk_reduction,
                "coordination_success": coordination_success,
                "agents_participated": len([r for r in negotiation_results if r.get("applied_adjustment", 0) != 0])
            }
        }
        
        return results
    
    def _get_classroom_details(self, classroom_id: str) -> dict:
        """Get detailed classroom information from scenario config"""
        for scenario in config.SCENARIOS.values():
            for classroom in scenario["classrooms"]:
                if classroom["id"] == classroom_id:
                    return classroom
        return {"professor_name": "Unknown", "subject": "Unknown"}
    
    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response, handling both JSON and natural language"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: create structured response from text
                return {
                    "raw_response": response_content,
                    "decision": "accept" if "accept" in response_content.lower() else "reject",
                    "reasoning": response_content[:200] + "..." if len(response_content) > 200 else response_content
                }
        except json.JSONDecodeError:
            return {
                "raw_response": response_content[:200] + "..." if len(response_content) > 200 else response_content,
                "decision": "reject",
                "reasoning": "Could not parse LLM response"
            }

async def main(test_config_name: str = None):
    """Main execution function"""
    # Initialize the coordination system with optional test configuration
    system = SimpleTrafficCoordinationSystem(test_config_name)
    
    # Get scenarios to run based on test config
    if test_config_name:
        test_config = config.get_test_config(test_config_name)
        scenarios = test_config.get("scenarios", ["demo"])
    else:
        scenarios = ["demo", "stress", "balanced"]
    
    print(f"\n🚀 Traffic Coordination System")
    print(f"Configuration: {test_config_name or 'default'}")
    print(f"LLM Model: {config.LLM_CONFIG['model']}")
    print(f"Risk Threshold: {config.NEGOTIATION_CONFIG['risk_threshold']}")
    print("=" * 60)
    
    for scenario in scenarios:
        scenario_config = config.get_scenario_config(scenario)
        print(f"\n=== Running {scenario.upper()} Scenario ===")
        print(f"Description: {scenario_config['description']}")
        print(f"Classrooms: {len(scenario_config['classrooms'])}, Capacity: {scenario_config['bottleneck_capacity']}/min")
        
        results = await system.run_coordination_episode(scenario)
        
        # Performance evaluation
        metrics = results['coordination_metrics']
        risk_reduction = metrics['risk_reduction']
        
        print(f"\n📊 RESULTS:")
        print(f"Coordination Success: {'✅' if metrics['coordination_success'] else '❌'}")
        print(f"Risk Reduction: {risk_reduction:.2f} ({_get_performance_level(risk_reduction)})")
        print(f"Final Risk: {metrics['final_risk']:.2f}")
        print(f"Agents Participated: {metrics['agents_participated']}")
        
        # Print final schedule
        print(f"\n📅 Final Schedule:")
        for classroom_id, schedule in results['final_schedule'].items():
            details = system._get_classroom_details(classroom_id)
            print(f"  {classroom_id} ({details.get('subject', 'Unknown')}): "
                  f"{schedule['base_time']} -> {schedule['final_time']} ({schedule['adjustment']:+d}min)")
        
        # Print autonomous decisions if detailed logging is enabled
        if config.LOGGING_CONFIG["detailed_decisions"] and results['negotiation_results']:
            print(f"\n🧠 Autonomous Agent Decisions:")
            for negotiation in results['negotiation_results']:
                decision_icon = "✅" if negotiation['decision'] == "accept" else "❌"
                print(f"  {decision_icon} {negotiation['classroom_id']}: {negotiation['decision']} "
                      f"({negotiation['applied_adjustment']:+d}min)")
                if len(negotiation['reasoning']) > 50:
                    print(f"     Reasoning: {negotiation['reasoning'][:100]}...")

def _get_performance_level(risk_reduction: float) -> str:
    """Get performance level description"""
    if risk_reduction >= config.PERFORMANCE_METRICS["excellent_risk_reduction"]:
        return "🌟 Excellent"
    elif risk_reduction >= config.PERFORMANCE_METRICS["good_risk_reduction"]:
        return "👍 Good"
    elif risk_reduction >= config.PERFORMANCE_METRICS["acceptable_risk_reduction"]:
        return "⚡ Acceptable"
    else:
        return "⚠️ Poor"

if __name__ == "__main__":
    import sys
    
    # Allow command line argument for test configuration
    test_config = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run the system
    asyncio.run(main(test_config))
