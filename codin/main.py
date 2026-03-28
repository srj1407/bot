"""Main entry point for the agent."""
import os
from agent.loop import GraphAgent
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.markdown import Markdown
from agent import config

console = Console()

def show(response):
    """Display response in a formatted panel."""
    console.print(
        Panel(
            Pretty(response),
            title="🤖 LLM Response",
            border_style="green",
            expand=False
        )
    )


def show_markdown(response):
    """Display markdown response."""
    Console().print(Markdown(response))

def main():
    """Run the agent from terminal."""
    print("🤖 Agent Started")
    print("-" * 50)

    agent = GraphAgent()
    try:
        # Interactive loop
        while True:
            try:
                user_input = input("\n📝 You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['exit', 'quit']:
                    print("👋 Goodbye!")
                    break

                print("\n⏳ Agent thinking...")
                response = agent.run(user_input)
                show(response)

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
    finally:
        agent.close()

if __name__ == "__main__":
    main()