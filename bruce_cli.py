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
  /voice       — Start voice chat mode
  /plugins     — List/manage plugins (load, unload, reload)
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
            elif command == "/plugins":
                from modules.plugin_system import get_plugin_manager
                pm = get_plugin_manager(bruce=bruce)
                # Sub-commands: /plugins, /plugins load [name], /plugins unload <name>, /plugins reload <name>
                parts = arg.strip().split(maxsplit=1)
                sub = parts[0].lower() if parts else ""
                sub_arg = parts[1].strip() if len(parts) > 1 else ""

                if sub == "load":
                    if sub_arg:
                        import os as _os
                        plugin_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "plugins", f"{sub_arg}.py")
                        p = pm.load_plugin(plugin_path)
                        if p:
                            print(f"\033[36m  Loaded: {p.name} v{p.version}\033[0m")
                        else:
                            print(f"\033[31m  Failed to load plugin: {sub_arg}\033[0m")
                    else:
                        results = pm.load_all()
                        for pname, success in results.items():
                            status_icon = "\033[32mOK\033[0m" if success else "\033[31mFAIL\033[0m"
                            print(f"  {pname}: {status_icon}")
                elif sub == "unload":
                    if not sub_arg:
                        print("\033[90m  Usage: /plugins unload <name>\033[0m")
                    elif pm.unload_plugin(sub_arg):
                        print(f"\033[36m  Unloaded: {sub_arg}\033[0m")
                    else:
                        print(f"\033[31m  Plugin '{sub_arg}' not found or not loaded.\033[0m")
                elif sub == "reload":
                    if not sub_arg:
                        print("\033[90m  Usage: /plugins reload <name>\033[0m")
                    else:
                        p = pm.reload_plugin(sub_arg)
                        if p:
                            print(f"\033[36m  Reloaded: {p.name} v{p.version}\033[0m")
                        else:
                            print(f"\033[31m  Failed to reload plugin: {sub_arg}\033[0m")
                else:
                    # List plugins
                    plugins = pm.list_plugins()
                    if not plugins:
                        print("\033[90m  No plugins loaded. Use /plugins load to load all.\033[0m")
                    else:
                        print(f"\033[33m  Loaded Plugins ({len(plugins)}):\033[0m")
                        for p in plugins:
                            status_str = "\033[32mloaded\033[0m" if p["loaded"] else "\033[31merror\033[0m"
                            tools_str = ", ".join(p["tools"]) if p["tools"] else "none"
                            cmds_str = ", ".join(f"/{c}" for c in p["commands"]) if p["commands"] else "none"
                            print(f"  \033[36m{p['name']}\033[0m v{p['version']} [{status_str}]")
                            print(f"    {p['description']}")
                            print(f"    Tools: {tools_str} | Commands: {cmds_str}")
            elif command == "/voice":
                from modules.voice_engine import start_voice_chat
                start_voice_chat(bruce_agent=bruce, require_wake_word=("wake" in arg.lower()))
            else:
                # Check plugin commands before giving up
                handled = False
                try:
                    from modules.plugin_system import get_plugin_manager
                    pm = get_plugin_manager()
                    plugin_cmds = pm.get_all_commands()
                    cmd_name = command.lstrip("/")
                    if cmd_name in plugin_cmds:
                        plugin_cmds[cmd_name]["fn"](arg)
                        handled = True
                except Exception:
                    pass
                if not handled:
                    print(f"\033[90m  Unknown command: {command}. Type /help\033[0m")
            continue

        # Fire plugin on_message hook
        try:
            from modules.plugin_system import get_plugin_manager
            get_plugin_manager().fire_on_message(user_input)
        except Exception:
            pass

        # Regular chat
        response = bruce.chat(user_input)
        print(f"\033[36mBruce:\033[0m {response}\n")


if __name__ == "__main__":
    main()
