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
    
    def __init__(self, test_config_name: str = None):
        self.config = config
        
        if test_config_name:
            test_config = config.get_test_config(test_config_name)
            self._apply_test_config(test_config)
        
        self.llm = ChatOllama(
            model=config.LLM_CONFIG["model"],
            temperature=config.LLM_CONFIG["temperature"],
            base_url=config.LLM_CONFIG["base_url"]
        )
        self.commitment_tracker = CommitmentTracker()
        self.logger = self._setup_logging()
        self.broadcasts: List[Dict[str, Any]] = []
    
    def _apply_test_config(self, test_config: dict):
        if "llm_temperature" in test_config:
            config.LLM_CONFIG["temperature"] = test_config["llm_temperature"]
        if "negotiation_timeout" in test_config:
            config.NEGOTIATION_CONFIG["negotiation_timeout"] = test_config["negotiation_timeout"]
        if "detailed_logging" in test_config:
            config.LOGGING_CONFIG["detailed_decisions"] = test_config["detailed_logging"]
    
    def _setup_logging(self) -> logging.Logger:
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
        if episode_date is None:
            episode_date = datetime.now().strftime("%Y-%m-%d")
        
        scenario = config.get_scenario_config(scenario_name)
        self.broadcasts = []
        
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
        
        analysis = await self._bottleneck_analysis_phase(classroom_states, scenario["bottleneck_capacity"])
        negotiation_results = await self._negotiation_phase(classroom_states, analysis, episode_date)
        final_results = await self._final_coordination_phase(classroom_states, analysis, negotiation_results, episode_date)
        
        return final_results
    
    async def _bottleneck_analysis_phase(self, classroom_states: List[ClassroomState], capacity: int) -> Dict[str, Any]:
        self.logger.info("Phase 1: Bottleneck Analysis")
        
        analysis = BottleneckTools.analyze_traffic_flow(classroom_states, capacity)
        
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
            analysis["llm_recommendations"] = llm_recommendations
        except Exception as e:
            self.logger.error(f"Bottleneck Agent LLM error: {e}")
            analysis["llm_recommendations"] = {"error": str(e)}
        
        return analysis
    
    async def _negotiation_phase(self, classroom_states: List[ClassroomState], 
                                analysis: Dict[str, Any], episode_date: str) -> List[Dict[str, Any]]:
        self.logger.info("Phase 2: Autonomous Agent Negotiations")
        
        negotiation_results = []
        self._apply_due_commitments(classroom_states, episode_date)
        self._propose_commitments(classroom_states, analysis, episode_date)
        
        agents_needing_negotiation = []
        if analysis["max_congestion_ratio"] > config.NEGOTIATION_CONFIG["risk_threshold"]:
            agents_needing_negotiation = list(classroom_states)
        
        if not agents_needing_negotiation:
            self.logger.info("No negotiations needed - congestion risk is manageable")
            return negotiation_results
        
        for classroom_state in agents_needing_negotiation:
            negotiation_result = await self._autonomous_agent_decision(
                classroom_state, analysis, episode_date
            )
            negotiation_results.append(negotiation_result)
        
        return negotiation_results

    def _apply_due_commitments(self, classroom_states: List[ClassroomState], episode_date: str) -> None:
        id_to_state = {cs.classroom_id: cs for cs in classroom_states}
        due = self.commitment_tracker.get_commitments_for_episode(episode_date)
        for c in due:
            target = id_to_state.get(c.to_classroom)
            fulfilled = False
            if target is not None:
                eval_result = ClassroomTools.evaluate_adjustment_feasibility(target, c.adjustment_minutes)
                if eval_result.get("is_feasible") and eval_result.get("constraints", {}).get("within_limits", True):
                    try:
                        target.current_adjustment = int(target.current_adjustment + c.adjustment_minutes)
                        fulfilled = True
                    except Exception:
                        fulfilled = False
            flag = self.commitment_tracker.fulfill_commitment(c, fulfilled)
            self.broadcasts.append({
                "type": "commitment_due_result",
                "from": c.from_classroom,
                "to": c.to_classroom,
                "episode_date": c.episode_date,
                "adjustment": c.adjustment_minutes,
                "status": "fulfilled" if fulfilled else "violated",
                "flag": flag if flag.get("flagged") else None
            })

    def _propose_commitments(self, classroom_states: List[ClassroomState], analysis: Dict[str, Any], episode_date: str) -> None:
        id_to_state = {cs.classroom_id: cs for cs in classroom_states}
        time_slot_analysis = analysis.get("time_slot_analysis", {})
        critical_slots: List[str] = analysis.get("critical_time_slots", [])
        for slot in critical_slots:
            info = time_slot_analysis.get(slot, {})
            classrooms = info.get("classrooms", [])
            if not classrooms:
                continue
            capacity = info.get("capacity", analysis.get("capacity_per_minute", 0))
            slot_students = info.get("students", 0)
            over = max(0, slot_students - capacity)
            if over <= 0:
                continue
            classrooms_sorted = sorted(classrooms, key=lambda x: x.get("students", 0), reverse=True)
            moves = 0
            for i, cand in enumerate(classrooms_sorted):
                if over <= 0 or moves >= 2:
                    break
                cand_id = cand.get("classroom")
                cand_state = id_to_state.get(cand_id)
                if cand_state is None:
                    continue
                for delta in (-config.NEGOTIATION_CONFIG["default_adjustment_minutes"], config.NEGOTIATION_CONFIG["default_adjustment_minutes"]):
                    feas = ClassroomTools.evaluate_adjustment_feasibility(cand_state, delta)
                    if not (feas.get("is_feasible") and feas.get("constraints", {}).get("within_limits", True)):
                        continue
                    if classrooms_sorted[0].get("classroom") != cand_id:
                        from_id = classrooms_sorted[0].get("classroom")
                    elif len(classrooms_sorted) > 1:
                        from_id = classrooms_sorted[1].get("classroom")
                    else:
                        from_id = cand_id
                    from_state = id_to_state.get(from_id, cand_state)
                    offer = ClassroomTools.create_commitment_offer(from_state, cand_id, delta, episode_date)
                    acceptance = ClassroomTools.evaluate_commitment_offer(cand_state, offer)
                    if acceptance.get("should_accept"):
                        cand_state.current_adjustment = int(cand_state.current_adjustment + delta)
                        self.commitment_tracker.add_commitment(offer)
                        self.broadcasts.append({
                            "type": "commitment_offer_accepted",
                            "time_slot": slot,
                            "from": from_id,
                            "to": cand_id,
                            "adjustment": delta,
                            "students": cand.get("students", 0),
                            "reciprocal": offer.reciprocal_commitment
                        })
                        try:
                            reciprocal = offer.reciprocal_commitment or {}
                            reciprocal_ep = reciprocal.get("episode_date")
                            reciprocal_adj = reciprocal.get("adjustment_minutes", 0)
                            reciprocal_type = reciprocal.get("commitment_type", "extend" if reciprocal_adj > 0 else "shorten")
                            if reciprocal_ep is not None and reciprocal_adj != 0:
                                future_commitment = ClassroomCommitment(
                                    from_classroom=cand_id,
                                    to_classroom=from_id,
                                    episode_date=reciprocal_ep,
                                    commitment_type=reciprocal_type,
                                    adjustment_minutes=reciprocal_adj
                                )
                                self.commitment_tracker.add_commitment(future_commitment)
                                self.broadcasts.append({
                                    "type": "commitment_reciprocal_recorded",
                                    "from": future_commitment.from_classroom,
                                    "to": future_commitment.to_classroom,
                                    "episode_date": future_commitment.episode_date,
                                    "adjustment": future_commitment.adjustment_minutes
                                })
                        except Exception:
                            pass
                        over = max(0, over - cand.get("students", 0))
                        moves += 1
                        break
    
    async def _autonomous_agent_decision(self, classroom_state: ClassroomState, 
                                       analysis: Dict[str, Any], episode_date: str) -> Dict[str, Any]:
        
        suggested_adjustment = config.calculate_suggested_adjustment(classroom_state.professor_flexibility)
        feasibility = ClassroomTools.evaluate_adjustment_feasibility(
            classroom_state, suggested_adjustment
        )
        
        classroom_details = self._get_classroom_details(classroom_state.classroom_id)
        
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
            
            if decision_data.get("decision") == "accept" or decision_data.get("proposed_adjustment", 0) != 0:
                adjustment = decision_data.get("proposed_adjustment", suggested_adjustment)
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
        self.logger.info("Phase 3: Final Coordination")
        
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
        
        final_analysis = BottleneckTools.analyze_traffic_flow(
            classroom_states,
            analysis["capacity_per_minute"]
        )
        
        initial_risk = analysis["max_congestion_ratio"]
        final_risk = final_analysis["max_congestion_ratio"]
        risk_reduction = max(0, initial_risk - final_risk)
        
        coordination_success = (final_analysis["overall_status"] in ["normal", "moderate"] and 
                               final_risk <= config.PERFORMANCE_METRICS["max_acceptable_final_risk"])
        
        self.logger.info("=== COORDINATION RESULTS ===")
        self.logger.info(f"Episode: {episode_date}")
        self.logger.info(f"Initial Risk: {initial_risk:.2f} -> Final Risk: {final_risk:.2f}")
        self.logger.info(f"Risk Reduction: {risk_reduction:.2f}")
        self.logger.info(f"Coordination Success: {coordination_success}")
        
        for classroom_id, schedule in final_schedule.items():
            self.logger.info(f"{classroom_id}: {schedule['base_time']} -> {schedule['final_time']} ({schedule['adjustment']:+d}min)")
        
        results = {
            "episode_date": episode_date,
            "initial_analysis": analysis,
            "final_analysis": final_analysis,
            "negotiation_results": negotiation_results,
            "final_schedule": final_schedule,
            "broadcasts": self.broadcasts,
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
        for scenario in config.SCENARIOS.values():
            for classroom in scenario["classrooms"]:
                if classroom["id"] == classroom_id:
                    return classroom
        return {"professor_name": "Unknown", "subject": "Unknown"}
    
    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        try:
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
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
    system = SimpleTrafficCoordinationSystem(test_config_name)
    
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
        
        metrics = results['coordination_metrics']
        risk_reduction = metrics['risk_reduction']
        
        print(f"\n📊 RESULTS:")
        print(f"Coordination Success: {'✅' if metrics['coordination_success'] else '❌'}")
        print(f"Risk Reduction: {risk_reduction:.2f} ({_get_performance_level(risk_reduction)})")
        print(f"Final Risk: {metrics['final_risk']:.2f}")
        print(f"Agents Participated: {metrics['agents_participated']}")
        
        print(f"\n📅 Final Schedule:")
        for classroom_id, schedule in results['final_schedule'].items():
            details = system._get_classroom_details(classroom_id)
            print(f"  {classroom_id} ({details.get('subject', 'Unknown')}): "
                  f"{schedule['base_time']} -> {schedule['final_time']} ({schedule['adjustment']:+d}min)")
        
        if config.LOGGING_CONFIG["detailed_decisions"] and results['negotiation_results']:
            print(f"\n🧠 Autonomous Agent Decisions:")
            for negotiation in results['negotiation_results']:
                decision_icon = "✅" if negotiation['decision'] == "accept" else "❌"
                print(f"  {decision_icon} {negotiation['classroom_id']}: {negotiation['decision']} "
                      f"({negotiation['applied_adjustment']:+d}min)")
                if len(negotiation['reasoning']) > 50:
                    print(f"     Reasoning: {negotiation['reasoning'][:100]}...")

def _get_performance_level(risk_reduction: float) -> str:
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
    test_config = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(test_config))