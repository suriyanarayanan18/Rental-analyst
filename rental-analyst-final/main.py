"""
rental-analyst V2: Multi-agent Airbnb analytics with anti-hallucination safeguards
Built with CrewAI + Claude API

V2 Changes:
- Added Validation Agent (Agent 6) that fact-checks all claims
- Anti-hallucination constraints in every agent's instructions
- Confidence tagging: [FROM DATA] vs [HYPOTHESIS] vs [HALLUCINATED]
- Data availability summary injected into every task

Usage:
    python main.py
    python main.py "Why are prices dropping in Venice Beach?"
"""

import sys
import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


def check_setup():
    """Verify everything is configured before running."""
    errors = []

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-anthropic-api-key-here":
        errors.append(
            "ANTHROPIC_API_KEY not set. Run:\n"
            '  set ANTHROPIC_API_KEY=your-key-here  (Windows CMD)\n'
            '  $env:ANTHROPIC_API_KEY="your-key-here"  (PowerShell)'
        )

    # Check data files
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    required_files = ["listings.csv", "reviews.csv", "calendar.csv"]
    for f in required_files:
        path = os.path.join(data_dir, f)
        if not os.path.exists(path):
            errors.append(
                f"Missing data/{f}. Download from:\n"
                f"  https://insideairbnb.com/get-the-data/"
            )

    if errors:
        print("\n*** SETUP ERRORS ***\n")
        for e in errors:
            print(f"  - {e}\n")
        print("Fix these issues and try again.")
        sys.exit(1)

    print("Setup check passed.")


def main():
    check_setup()

    from crewai import Crew, Process
    from agents import create_agents
    from tasks import create_tasks

    # Default question or use command line argument
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = (
            "Why are occupancy rates declining in certain LA neighborhoods, "
            "and what pricing or guest experience factors are driving it?"
        )

    print(f"\n{'='*60}")
    print(f"RENTAL ANALYST V2 (with anti-hallucination safeguards)")
    print(f"{'='*60}")
    print(f"\nQuestion: {question}\n")

    # Create agents with Claude Sonnet
    llm = "anthropic/claude-sonnet-4-20250514"
    print(f"LLM: {llm}")
    print(f"Agents: 6 (Data Profiler, Pricing Analyst, Sentiment Analyst,")
    print(f"         Root Cause Investigator, Validation Agent, Report Writer)")
    agents = create_agents(llm)

    # Create tasks with data context
    tasks = create_tasks(agents, question)

    # Assemble the crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    # Run it
    print(f"\n{'='*60}")
    print("STARTING CREW EXECUTION (6 agents)")
    print(f"{'='*60}\n")

    result = crew.kickoff()

    # Save full output
    os.makedirs("outputs", exist_ok=True)

    with open("outputs/full_analysis_v2.md", "w", encoding="utf-8") as f:
        f.write(f"# Rental Analyst Report V2\n\n")
        f.write(f"**Question:** {question}\n\n")
        f.write(f"**Version:** V2 with anti-hallucination safeguards\n\n")
        f.write(f"**Agents:** 6 (including Validation Agent)\n\n")
        f.write(f"---\n\n")
        f.write(str(result))

    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE (V2)")
    print(f"{'='*60}")
    print(f"\nOutputs saved to:")
    print(f"  outputs/full_analysis_v2.md")
    print(f"  outputs/executive_report_v2.md")
    print(f"\n{result}")


if __name__ == "__main__":
    main()
