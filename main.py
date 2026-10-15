"""Mission controller, output writer, and command-line entry point."""

import argparse
import json
import time
from pathlib import Path

from agent import WallEAgent
from environment import GridEnvironment
from ui import MissionUI


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"


def save_json(path, data):
    """Write readable JSON and create the parent directory if necessary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def make_report(env, agent, status):
    """Build a final report using public state and the agent's beliefs."""
    estimate = agent.confidence_summary()

    if status == "found":
        next_step = (
            "Mission successful. Review the collected evidence and "
            "the action trace."
        )
    elif env.energy == 0:
        next_step = (
            "Energy depleted. Adjust the energy configuration and "
            "run the mission again."
        )
    else:
        next_step = (
            "EVE was not confirmed. Review the trace, recharge strategy, "
            "and signal radius before another attempt."
        )

    return {
        "project": "WALL-E and EVE's Signal",
        "mission_status": status,
        "eve_found": env.found,
        "steps": env.step_count,
        "final_position": list(env.position),
        "remaining_energy": env.energy,
        "maximum_energy": env.max_energy,
        "visited_cells": len(env.visited),
        "evidence": env.evidence,
        "estimated_eve_location": estimate["estimated_location"],
        "confidence": estimate["confidence"],
        "recommended_next_step": next_step,
    }


def run_mission(config_path, headless=False, max_actions=None):
    """Run the mission and save a trace and final report."""
    env = GridEnvironment(config_path)

    agent = WallEAgent(env.config)
    observation = env.observe()
    agent.update_beliefs(observation)

    limit = max_actions or int(env.config.get("max_actions", 200))
    delay = int(env.config.get("gui_delay_ms", 150))

    ui = None
    if not headless:
        try:
            ui = MissionUI(env.grid_size, delay)
        except Exception as exc:
            print(f"Could not open the GUI: {exc}")
            print("Continuing in headless mode.")
            headless = True

    trace = []
    status = "found" if env.found else "running"

    if ui is not None:
        ui._station = env.recharge_station
        ui.refresh(
            observation,
            {"mode": "initializing"},
            agent,
            env.recharge_station,
        )

    while not env.found and len(trace) < limit:
        # 1. The observation from the preceding action is already available.
        # 2. Update beliefs before making the next decision.
        agent.update_beliefs(observation)

        # 3. Choose an action and explain why.
        decision = agent.decide(observation)
        action = decision["action"]

        if action == "stop":
            break

        # 4. Execute the action and get a fresh observation.
        observation = env.step(action)

        # 5. Update beliefs from the new observation.
        agent.update_beliefs(observation)
        confidence = agent.confidence_summary()

        record = {
            "action_number": len(trace) + 1,
            "action": action,
            "reason": decision["reason"],
            "mode": decision["mode"],
            "observation": observation,
            "estimated_eve_location": confidence["estimated_location"],
            "confidence": confidence["confidence"],
        }
        trace.append(record)

        # Save incrementally so partial progress survives an interruption.
        save_json(OUTPUT_DIR / "action_trace.json", trace)

        # 6. Update the dashboard after the action.
        if ui is not None:
            try:
                ui.refresh(
                    observation,
                    decision,
                    agent,
                    env.recharge_station,
                )
                ui.log_event(
                    f"Step {record['action_number']}: "
                    f"{action} | {decision['reason']}"
                )
                if delay > 0:
                    time.sleep(delay / 1000)
            except Exception:
                # The user may close the GUI while the mission is running.
                ui = None
                headless = True

        # 7. Stop as soon as direct confirmation is received.
        if env.found:
            status = "found"
            break

    if not env.found:
        status = "action_limit" if len(trace) >= limit else "not_found"

    # 8. Preserve the final outputs even if EVE was not found.
    report = make_report(env, agent, status)
    save_json(OUTPUT_DIR / "action_trace.json", trace)
    save_json(OUTPUT_DIR / "mission_report.json", report)

    print("\n=== WALL-E AND EVE'S SIGNAL ===")
    print(f"Mission status : {report['mission_status']}")
    print(f"Actions        : {report['steps']}")
    print(f"Final position : {tuple(report['final_position'])}")
    print(f"Energy left    : {report['remaining_energy']}")
    print(f"Estimated EVE  : {tuple(report['estimated_eve_location'])}")
    print(f"Confidence     : {report['confidence']:.1%}")
    print(f"Trace          : {OUTPUT_DIR / 'action_trace.json'}")
    print(f"Report         : {OUTPUT_DIR / 'mission_report.json'}")

    # Keep the finished dashboard open until the user closes it.
    if ui is not None and not ui.closed:
        ui.show_final(report)

    return report, trace


def main():
    parser = argparse.ArgumentParser(
        description="Run the WALL-E and EVE's Signal mission."
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without the Tkinter GUI.",
    )
    parser.add_argument(
        "--config",
        default=str(BASE_DIR / "config.json"),
        help="Path to the JSON configuration file.",
    )
    parser.add_argument(
        "--max-actions",
        type=int,
        default=None,
        help="Override the maximum number of actions.",
    )
    args = parser.parse_args()

    if args.max_actions is not None and args.max_actions < 1:
        parser.error("--max-actions must be at least 1.")

    run_mission(
        args.config,
        headless=args.headless,
        max_actions=args.max_actions,
    )


if __name__ == "__main__":
    main()