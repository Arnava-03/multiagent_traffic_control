import asyncio
import sys
import time
from simple_langgraph_coordination import SimpleTrafficCoordinationSystem
import config
from datetime import datetime, timedelta

async def run_quick_test():
    print("🚀 Running Quick Test Configuration")
    system = SimpleTrafficCoordinationSystem("quick_test")
    
    results = await system.run_coordination_episode("demo")
    metrics = results['coordination_metrics']
    
    print(f"✅ Quick Test Complete:")
    print(f"   Risk Reduction: {metrics['risk_reduction']:.2f}")
    print(f"   Success: {metrics['coordination_success']}")
    return results

async def run_stress_test():
    print("🔥 Running Stress Test Configuration")
    system = SimpleTrafficCoordinationSystem("stress_test")
    
    for scenario in ["stress", "extreme"]:
        print(f"\n--- {scenario.upper()} Scenario ---")
        results = await system.run_coordination_episode(scenario)
        metrics = results['coordination_metrics']
        
        print(f"Risk: {metrics['initial_risk']:.2f} -> {metrics['final_risk']:.2f}")
        print(f"Reduction: {metrics['risk_reduction']:.2f}")
        print(f"Success: {'✅' if metrics['coordination_success'] else '❌'}")

async def run_ablation_study():
    print("🔬 Running Ablation Study")
    
    base_scenario = "balanced"
    test_variations = config.TEST_CONFIGS["ablation_study"]["test_variations"]
    results_comparison = []
    
    for variation in test_variations:
        print(f"\n--- Testing: {variation['name']} ---")
        
        original_values = {}
        for key, value in variation.items():
            if key != "name" and hasattr(config, key.upper() + "_CONFIG"):
                config_dict = getattr(config, key.upper() + "_CONFIG", {})
                if key.split('_')[-1] in config_dict:
                    original_values[key] = config_dict[key.split('_')[-1]]
                    config_dict[key.split('_')[-1]] = value
        
        system = SimpleTrafficCoordinationSystem()
        results = await system.run_coordination_episode(base_scenario)
        metrics = results['coordination_metrics']
        
        results_comparison.append({
            "name": variation['name'],
            "risk_reduction": metrics['risk_reduction'],
            "success": metrics['coordination_success'],
            "final_risk": metrics['final_risk']
        })
        
        for key, value in original_values.items():
            config_dict = getattr(config, key.upper() + "_CONFIG", {})
            config_dict[key.split('_')[-1]] = value
    
    print(f"\n📊 ABLATION STUDY RESULTS:")
    print(f"{'Variation':<15} {'Risk Reduction':<15} {'Final Risk':<12} {'Success'}")
    print("-" * 60)
    for result in results_comparison:
        success_icon = "✅" if result['success'] else "❌"
        print(f"{result['name']:<15} {result['risk_reduction']:<15.2f} {result['final_risk']:<12.2f} {success_icon}")

async def run_parameter_sensitivity():
    print("📈 Running Parameter Sensitivity Analysis")
    
    risk_thresholds = [0.5, 0.7, 0.9, 1.1]
    scenario = "demo"
    
    print(f"\n🎯 Risk Threshold Sensitivity:")
    print(f"{'Threshold':<12} {'Agents Selected':<15} {'Risk Reduction':<15} {'Success'}")
    print("-" * 60)
    
    for threshold in risk_thresholds:
        original_threshold = config.NEGOTIATION_CONFIG["risk_threshold"]
        config.NEGOTIATION_CONFIG["risk_threshold"] = threshold
        
        system = SimpleTrafficCoordinationSystem()
        results = await system.run_coordination_episode(scenario)
        metrics = results['coordination_metrics']
        
        success_icon = "✅" if metrics['coordination_success'] else "❌"
        print(f"{threshold:<12.1f} {metrics['agents_participated']:<15} {metrics['risk_reduction']:<15.2f} {success_icon}")
        
        config.NEGOTIATION_CONFIG["risk_threshold"] = original_threshold

async def demonstrate_all_scenarios():
    print("🎭 Demonstrating All Scenarios")
    system = SimpleTrafficCoordinationSystem()
    
    for scenario_name, scenario_config in config.SCENARIOS.items():
        print(f"\n=== {scenario_name.upper()} SCENARIO ===")
        print(f"📝 {scenario_config['description']}")
        print(f"🏫 {len(scenario_config['classrooms'])} classrooms")
        print(f"🚦 {scenario_config['bottleneck_capacity']} capacity/min")
        
        print("Classrooms:")
        for classroom in scenario_config['classrooms']:
            flexibility_desc = config.get_flexibility_description(classroom['professor_flexibility'])
            print(f"  • {classroom['id']}: {classroom['students']} students, "
                  f"{classroom['professor_name']} ({classroom['subject']}) - {flexibility_desc}")
        
        start_time = time.time()
        results = await system.run_coordination_episode(scenario_name)
        end_time = time.time()
        
        metrics = results['coordination_metrics']
        print(f"\n📊 Results:")
        print(f"  Risk: {metrics['initial_risk']:.2f} -> {metrics['final_risk']:.2f} (Δ{metrics['risk_reduction']:.2f})")
        print(f"  Success: {'✅' if metrics['coordination_success'] else '❌'}")
        print(f"  Time: {end_time - start_time:.1f}s")

async def run_multi_episode_commitments():
    print("🗓️  Running Multi-Episode Commitment Test")
    scenario = "assignment_demo" if "assignment_demo" in config.SCENARIOS else "demo"
    episodes = 4
    interval_days = config.EXPERIMENTAL_CONFIG.get("episode_interval_days", 7)
    start_date = datetime.now().strftime("%Y-%m-%d")

    print(f"Scenario: {scenario}")
    print(f"Episodes: {episodes}, Interval: {interval_days} days")

    system = SimpleTrafficCoordinationSystem()
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    for i in range(episodes):
        ep_date = (start_dt + timedelta(days=i * interval_days)).strftime("%Y-%m-%d")
        print(f"\n=== EPISODE {i+1} — Date: {ep_date} ===")
        results = await system.run_coordination_episode(scenario, ep_date)
        metrics = results["coordination_metrics"]
        print(f"Risk: {metrics['initial_risk']:.2f} -> {metrics['final_risk']:.2f} (Δ{metrics['risk_reduction']:.2f}) | Success: {'✅' if metrics['coordination_success'] else '❌'}")

        broadcasts = results.get("broadcasts", [])
        offers = [b for b in broadcasts if b.get("type") == "commitment_offer_accepted"]
        due_results = [b for b in broadcasts if b.get("type") == "commitment_due_result"]
        flagged = [b for b in due_results if b.get("flag", {}) and b["flag"].get("flagged")]

        print(f"Offers accepted this episode: {len(offers)}")
        for ev in offers:
            print(f"  • Slot {ev.get('time_slot')}: {ev.get('to')} {ev.get('adjustment'):+d}min (from {ev.get('from')}), reciprocal next: {ev.get('reciprocal', {}).get('adjustment_minutes', 0):+d}min")

        print(f"Due commitments processed: {len(due_results)}")
        for ev in due_results:
            status = ev.get('status')
            print(f"  • {ev.get('to')} {ev.get('adjustment'):+d}min — {status}")

        if flagged:
            print(f"Violations flagged: {len(flagged)}")
            for ev in flagged:
                f = ev.get('flag', {})
                print(f"  ⚠️  {f.get('classroom')} flagged (violations={f.get('violation_count')})")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py <test_type>")
        print("Available tests:")
        print("  quick       - Quick test with demo scenario")
        print("  stress      - Stress test with challenging scenarios")
        print("  ablation    - Ablation study comparing configurations")
        print("  sensitivity - Parameter sensitivity analysis")
        print("  scenarios   - Demonstrate all available scenarios")
        print("  episodes    - Run multi-episode commitment test (4 weeks)")
        print("  all         - Run all tests")
        return
    
    test_type = sys.argv[1].lower()
    
    if test_type == "quick":
        await run_quick_test()
    elif test_type == "stress":
        await run_stress_test()
    elif test_type == "ablation":
        await run_ablation_study()
    elif test_type == "sensitivity":
        await run_parameter_sensitivity()
    elif test_type == "scenarios":
        await demonstrate_all_scenarios()
    elif test_type == "episodes":
        await run_multi_episode_commitments()
    elif test_type == "all":
        await run_quick_test()
        await run_stress_test()
        await run_parameter_sensitivity()
        await demonstrate_all_scenarios()
    else:
        print(f"Unknown test type: {test_type}")

if __name__ == "__main__":
    asyncio.run(main())