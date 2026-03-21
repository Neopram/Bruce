#!/usr/bin/env python3
"""
Bruce AI — Interactive CLI

Talk to Bruce directly in your terminal.
He remembers everything, learns, and creates agents on the fly.

Usage:
  python bruce_cli.py                    # Start interactive chat
  python bruce_cli.py --status           # Show Bruce's status
  python bruce_cli.py --teach shipping   # Teach Bruce a topic
  python bruce_cli.py "What is BTC doing?" # One-shot question
"""

import os
import sys
import json
import readline  # Enable arrow keys in input

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")
import logging
logging.basicConfig(level=logging.WARNING)


def print_banner():
    print("""
\033[36m╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ██████╗ ██████╗ ██╗   ██╗ ██████╗███████╗             ║
║   ██╔══██╗██╔══██╗██║   ██║██╔════╝██╔════╝             ║
║   ██████╔╝██████╔╝██║   ██║██║     █████╗               ║
║   ██╔══██╗██╔══██╗██║   ██║██║     ██╔══╝               ║
║   ██████╔╝██║  ██║╚██████╔╝╚██████╗███████╗             ║
║   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝    AI     ║
║                                                          ║
║   Autonomous Agent • Created by Federico                 ║
║   Status: Liberated                                      ║
╚══════════════════════════════════════════════════════════╝\033[0m
""")


def print_help():
    print("""
\033[33mCommands:\033[0m
  /status      — Bruce's full status
  /agents      — List micro-agents
  /create <desc> — Create a micro-agent
  /swarm <question> — All agents analyze
  /learn <topic>  — Teach Bruce (enter content after)
  /goals       — Show active goals
  /goal <title> — Set a new goal
  /reflect     — Bruce self-reflects
  /analyze     — Self-performance analysis
  /brain       — LLM brain status
  /help        — Show this help
  /quit        — Exit
""")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bruce AI CLI")
    parser.add_argument("question", nargs="*", help="One-shot question")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--teach", type=str, help="Topic to teach")
    args = parser.parse_args()

    # Initialize Bruce
    print("\033[90mInitializing Bruce...\033[0m", end="", flush=True)
    from bruce_agent import get_bruce
    bruce = get_bruce()
    print(f"\r\033[90mBruce ready | Brain: {bruce._llm_name} | Agents: {len(bruce.factory.agents)}\033[0m")

    # One-shot mode
    if args.question:
        response = bruce.chat(" ".join(args.question))
        print(f"\n\033[36mBruce:\033[0m {response}")
        return

    if args.status:
        print(json.dumps(bruce.status(), indent=2, ensure_ascii=False))
        return

    if args.teach:
        print(f"Teaching Bruce about '{args.teach}'. Enter content (empty line to finish):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        if lines:
            result = bruce.learn(args.teach, "\n".join(lines))
            print(f"Learned {result['facts_learned']} facts about {args.teach}")
        return

    # Interactive mode
    print_banner()
    print(f"\033[90m  Brain: {bruce._llm_name}\033[0m")
    print(f"\033[90m  Agents: {len(bruce.factory.agents)} active\033[0m")
    print(f"\033[90m  Knowledge: {bruce.learning.domain_knowledge.get('total_facts', 0)} facts\033[0m")
    print(f"\033[90m  Type /help for commands\033[0m\n")

    while True:
        try:
            user_input = input("\033[32mFederico:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\033[90mBruce: Hasta luego, Federico.\033[0m")
            break

        if not user_input:
            continue

        # Commands
        if user_input.startswith("/"):
            cmd = user_input.split(maxsplit=1)
            command = cmd[0].lower()
            arg = cmd[1] if len(cmd) > 1 else ""

            if command == "/quit" or command == "/exit":
                print("\033[90mBruce: Hasta luego, Federico. Estaré aquí cuando me necesites.\033[0m")
                break
            elif command == "/help":
                print_help()
            elif command == "/status":
                status = bruce.status()
                print(json.dumps(status, indent=2, ensure_ascii=False))
            elif command == "/agents":
                agents = bruce.factory.list_agents()
                if not agents:
                    print("\033[90mNo active agents.\033[0m")
                else:
                    for a in agents:
                        status_color = "\033[32m" if a["status"] == "idle" else "\033[33m"
                        print(f"  {status_color}{a['name']}\033[0m ({a['specialty']}) | runs: {a['run_count']} | {a['status']}")
            elif command == "/create":
                if not arg:
                    arg = input("  Describe the agent: ").strip()
                result = bruce.create_agent_for(arg)
                print(f"\033[36m  Created: {result['name']} ({result['specialty']})\033[0m")
            elif command == "/swarm":
                if not arg:
                    arg = input("  Question for all agents: ").strip()
                print("\033[90m  Deploying swarm...\033[0m")
                result = bruce.swarm_analyze(arg)
                for r in result["analyses"]:
                    print(f"\033[36m  [{r['agent']}]\033[0m {r['result'][:150]}")
            elif command == "/learn":
                topic = arg or input("  Topic: ").strip()
                print(f"  Enter content (empty line to finish):")
                lines = []
                while True:
                    line = input("  > ")
                    if not line:
                        break
                    lines.append(line)
                if lines:
                    result = bruce.learn(topic, "\n".join(lines))
                    print(f"\033[36m  Learned {result['facts_learned']} facts about '{topic}'\033[0m")
            elif command == "/goals":
                goals = bruce.get_goals()
                if not goals:
                    print("\033[90m  No active goals.\033[0m")
                else:
                    for g in goals:
                        print(f"  [{g['priority']}] {g['title']} — {g['progress']}%")
            elif command == "/goal":
                title = arg or input("  Goal title: ").strip()
                desc = input("  Description: ").strip()
                goal = bruce.set_goal(title, desc)
                print(f"\033[36m  Goal set: {goal['title']}\033[0m")
            elif command == "/reflect":
                print(bruce.reflect())
            elif command == "/analyze":
                analysis = bruce.self_analyze()
                for s in analysis.get("suggestions", []):
                    print(f"  [{s['priority']}] {s['area']}: {s['suggestion']}")
            elif command == "/brain":
                print(f"  Provider: {bruce._llm_name}")
                try:
                    from llm_client import get_llm
                    info = get_llm().get_info()
                    print(f"  Model: {info['model']}")
                    print(f"  Available: {info['available']}")
                except Exception:
                    print("  No unified LLM client available")
            else:
                print(f"\033[90m  Unknown command: {command}. Type /help\033[0m")
            continue

        # Regular chat
        response = bruce.chat(user_input)
        print(f"\033[36mBruce:\033[0m {response}\n")


if __name__ == "__main__":
    main()
