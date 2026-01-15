#!/usr/bin/env python3
"""
Getting Started Checklist for Gemini Shopping Assistant

This file documents the steps to get up and running with the
Gemini Shopping Assistant implementation.
"""

# ============================================================================
# GETTING STARTED CHECKLIST
# ============================================================================

STEPS = {
    "1_prerequisites": {
        "description": "Prerequisites & Setup",
        "steps": [
            "✓ Python 3.8+ installed",
            "✓ pip package manager available",
            "✓ Google Gemini API key obtained from https://ai.google.dev/",
            "✓ Internet connection available",
            "✓ Current directory is /home/nkse/mirsci/projects/assistants_api"
        ],
        "status": "READY"
    },
    
    "2_installation": {
        "description": "Installation (1 minute)",
        "steps": [
            "Run: pip install -r requirements.txt",
            "Wait for completion (installs google-generativeai, openai, etc.)",
            "Verify: python -c 'import google.generativeai; print(\"OK\")'",
        ],
        "estimated_time": "1 minute",
        "difficulty": "Easy"
    },
    
    "3_configuration": {
        "description": "Configuration (1 minute)",
        "steps": [
            "Get API key from: https://ai.google.dev/",
            "Set environment variable:",
            "  Linux/Mac: export GEMINI_API_KEY='your-api-key'",
            "  Windows: set GEMINI_API_KEY=your-api-key",
            "Verify: python -c 'import os; print(os.getenv(\"GEMINI_API_KEY\")[:10]...)'",
        ],
        "estimated_time": "1 minute",
        "difficulty": "Very Easy"
    },
    
    "4_first_demo": {
        "description": "Run Interactive Demo (5 minutes)",
        "steps": [
            "Run: python gemini_demo.py",
            "Select option 1 (Basic Assistant)",
            "Watch example conversation with Gemini",
            "See product extraction in action",
            "Exit demo (press 0)",
        ],
        "estimated_time": "5 minutes",
        "difficulty": "Easy"
    },
    
    "5_documentation": {
        "description": "Read Documentation (30 minutes)",
        "steps": [
            "Read: IMPLEMENTATION_SUMMARY.md (overview)",
            "Read: QUICK_REFERENCE.md (common tasks)",
            "Skim: GEMINI_SHOPPING_ASSISTANT.md (API reference)",
            "Review: ARCHITECTURE.md (if needed)",
        ],
        "estimated_time": "30 minutes",
        "difficulty": "Easy"
    },
    
    "6_first_code": {
        "description": "Write Your First Code (5 minutes)",
        "example": """
from gemini_shopping_assistant import GeminiShoppingAssistant

# Initialize
assistant = GeminiShoppingAssistant()

# Start conversation
conv_id = assistant.start_conversation(user_id="myuser")

# Ask a question
response = assistant.ask(
    "Find gaming laptops under $1500",
    conversation_id=conv_id
)

# Print response
print(response['response'])

# Print products found
for product in response['products']:
    print(f"- {product['name']}: ${product['price']}")
""",
        "steps": [
            "Create file: test_gemini.py",
            "Copy the example code above",
            "Run: python test_gemini.py",
            "See real Gemini API response with products",
        ],
        "estimated_time": "5 minutes",
        "difficulty": "Easy"
    },
    
    "7_multi_turn": {
        "description": "Try Multi-Turn Conversations (10 minutes)",
        "example": """
from gemini_integrated_system import IntegratedGeminiShoppingSystem

system = IntegratedGeminiShoppingSystem()

# Start session
conv_id = system.start_shopping_session(
    user_id="shopper",
    partner_id="mystore"
)

# Question 1
resp1 = system.ask_product_question(
    "Find noise-canceling headphones under $200",
    conv_id, "shopper"
)
print("Turn 1:", resp1['response'][:200])

# Question 2 (maintains context from Turn 1)
resp2 = system.ask_product_question(
    "Which one is best for travel?",
    conv_id, "shopper"
)
print("Turn 2:", resp2['response'][:200])

# View conversation
history = system.assistant.get_conversation_history(conv_id)
print(f"Messages: {len(history)}")
""",
        "steps": [
            "Create file: test_multiturn.py",
            "Copy the example code above",
            "Run: python test_multiturn.py",
            "Observe context maintained across questions",
        ],
        "estimated_time": "10 minutes",
        "difficulty": "Easy"
    },
    
    "8_exploration": {
        "description": "Explore the System (30 minutes)",
        "steps": [
            "Try different questions and observe responses",
            "Check what products are extracted",
            "Review the source code in gemini_shopping_assistant.py",
            "Understand ConversationContext and Product classes",
            "Try with different models (gemini-1.5-pro, etc)",
            "Experiment with temperature parameter",
        ],
        "estimated_time": "30 minutes",
        "difficulty": "Medium"
    },
    
    "9_integration": {
        "description": "Plan Integration (30 minutes)",
        "steps": [
            "Decide where to use this (web app, chatbot, API, etc)",
            "Review integration examples in GEMINI_SHOPPING_ASSISTANT.md",
            "Check if you need persistent storage (Redis/PostgreSQL)",
            "Plan multi-tenant setup if needed",
            "Review security section in documentation",
        ],
        "estimated_time": "30 minutes",
        "difficulty": "Medium"
    },
    
    "10_production": {
        "description": "Prepare for Production (1 hour+)",
        "steps": [
            "Set up Redis for caching (optional but recommended)",
            "Set up PostgreSQL for persistence (optional but recommended)",
            "Review ARCHITECTURE.md for production setup",
            "Implement logging and monitoring",
            "Add rate limiting and error handling",
            "Set up Docker containers",
            "Configure environment variables",
            "Test with multiple concurrent users",
        ],
        "estimated_time": "1+ hour",
        "difficulty": "Hard"
    },
}


def print_checklist():
    """Print getting started checklist"""
    print("\n" + "=" * 70)
    print("GEMINI SHOPPING ASSISTANT - GETTING STARTED CHECKLIST")
    print("=" * 70)
    
    total_time = 0
    
    for key, section in STEPS.items():
        print(f"\n{key.replace('_', ' ').upper()}")
        print("-" * 70)
        print(f"Description: {section['description']}")
        
        if 'estimated_time' in section:
            print(f"Time: {section['estimated_time']}")
            # Add to total for basic setup
            if key in ['2_installation', '3_configuration', '4_first_demo']:
                time_str = section['estimated_time'].split()[0]
                total_time += int(time_str)
        
        if 'difficulty' in section:
            print(f"Difficulty: {section['difficulty']}")
        
        if 'status' in section:
            print(f"Status: {section['status']}")
        
        print("\nSteps:")
        for step in section['steps']:
            print(f"  {step}")
        
        if 'example' in section:
            print("\nExample code:")
            for line in section['example'].split('\n'):
                if line.strip():
                    print(f"  {line}")
    
    print("\n" + "=" * 70)
    print(f"QUICK START TIME: {total_time} minutes (steps 1-4)")
    print("FULL ONBOARDING TIME: 2-3 hours (steps 1-9)")
    print("PRODUCTION READY: 4-5 hours (steps 1-10)")
    print("=" * 70)


def print_quick_start():
    """Print just the quick start (first 5 minutes)"""
    print("\n" + "=" * 70)
    print("QUICK START - 5 MINUTES")
    print("=" * 70)
    
    print("\n1. INSTALL (1 minute)")
    print("   pip install -r requirements.txt")
    
    print("\n2. SET API KEY (1 minute)")
    print("   export GEMINI_API_KEY='your-api-key'")
    print("   (Get key from https://ai.google.dev/)")
    
    print("\n3. RUN DEMO (3 minutes)")
    print("   python gemini_demo.py")
    
    print("\n✓ Done! You now have a working shopping assistant.")
    print("=" * 70)


def print_learning_path():
    """Print learning path"""
    print("\n" + "=" * 70)
    print("LEARNING PATH")
    print("=" * 70)
    
    print("\nBEGINNER (30 minutes)")
    print("  1. Quick start (5 min)")
    print("  2. Read IMPLEMENTATION_SUMMARY.md (10 min)")
    print("  3. Run gemini_demo.py (5 min)")
    print("  4. Try first code example (10 min)")
    
    print("\nINTERMEDIATE (1.5 hours)")
    print("  1. Read QUICK_REFERENCE.md (15 min)")
    print("  2. Read GEMINI_SHOPPING_ASSISTANT.md (30 min)")
    print("  3. Try multi-turn conversation (10 min)")
    print("  4. Review source code (20 min)")
    print("  5. Experiment with different settings (15 min)")
    
    print("\nADVANCED (2+ hours)")
    print("  1. Read ARCHITECTURE.md (30 min)")
    print("  2. Review all implementation files (60 min)")
    print("  3. Set up production storage (30 min)")
    print("  4. Plan integration (30 min)")
    
    print("=" * 70)


def print_file_guide():
    """Print what each file does"""
    print("\n" + "=" * 70)
    print("FILE GUIDE")
    print("=" * 70)
    
    files = {
        "IMPLEMENTATION_SUMMARY.md": "Quick overview - START HERE",
        "QUICK_REFERENCE.md": "Common patterns and troubleshooting",
        "GEMINI_SHOPPING_ASSISTANT.md": "Complete API reference",
        "ARCHITECTURE.md": "System design and technical details",
        "VISUAL_GUIDES.md": "Diagrams and visual explanations",
        "INDEX.md": "Complete project index",
        "gemini_shopping_assistant.py": "Core assistant implementation",
        "gemini_session_storage.py": "Session storage layer",
        "gemini_integrated_system.py": "Complete orchestration system",
        "gemini_demo.py": "Interactive demo and examples",
        "requirements.txt": "Python dependencies",
    }
    
    print("\nDocumentation Files:")
    for filename, description in sorted(files.items()):
        if filename.endswith('.md'):
            print(f"  ✓ {filename:40} {description}")
    
    print("\nImplementation Files:")
    for filename, description in sorted(files.items()):
        if filename.endswith('.py') and not filename == 'gemini_demo.py':
            print(f"  ✓ {filename:40} {description}")
    
    print("\nExample Files:")
    for filename, description in sorted(files.items()):
        if filename == 'gemini_demo.py':
            print(f"  ✓ {filename:40} {description}")
    
    print("\nConfiguration Files:")
    for filename, description in sorted(files.items()):
        if filename == 'requirements.txt':
            print(f"  ✓ {filename:40} {description}")
    
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'quick':
            print_quick_start()
        elif sys.argv[1] == 'path':
            print_learning_path()
        elif sys.argv[1] == 'files':
            print_file_guide()
        elif sys.argv[1] == 'full':
            print_checklist()
        else:
            print("Usage: python GETTING_STARTED.py [quick|path|files|full]")
    else:
        # Default: show quick start
        print_quick_start()
        print("\nFor more options:")
        print("  python GETTING_STARTED.py quick    (5-minute quick start)")
        print("  python GETTING_STARTED.py path     (learning path)")
        print("  python GETTING_STARTED.py files    (file guide)")
        print("  python GETTING_STARTED.py full     (complete checklist)")
