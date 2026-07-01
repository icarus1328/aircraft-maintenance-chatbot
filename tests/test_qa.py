import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retrieval.context_assembler import ContextAssembler
from llm.client import GroqClient
from llm.prompts import QA_SYSTEM_PROMPT

def run_qa_tests():
    assembler = ContextAssembler()
    client = GroqClient()
    
    questions = [
        "What are the personal protective equipment (PPE) requirements for handling Skydrol?",
        "What is the dry and lubricated torque in in-lbf for a #10-32 threaded fastener?",
        "What are the safety steps and warnings for replacing the Engine-Driven Pump (EDP)?",
        "What is the required operator action for a CPCP Level 3 corrosion finding?",
        "Explain the lockout/tagout LOTO procedure for flight controls maintenance."
    ]
    
    for idx, q in enumerate(questions):
        print(f"\n==========================================")
        print(f"QUESTION {idx+1}: {q}")
        
        # Assemble context
        assembly = assembler.assemble(q, top_k_rag=3)
        user_prompt = assembly["user_prompt"]
        
        print(f"\n[Retrieved Context Summary]")
        print(f"- SQL query generated: {assembly['sql_query']}")
        print(f"- Number of SQL records found: {len(assembly['sql_results'])}")
        print(f"- Number of RAG chunks retrieved: {len(assembly['rag_chunks'])}")
        
        # Generate Answer
        print(f"\nGenerating Answer...")
        try:
            answer = client.generate(
                system_prompt=QA_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.0
            )
            print(f"\nANSWER:\n{answer}")
        except Exception as e:
            print(f"Failed to generate answer: {str(e)}")

if __name__ == "__main__":
    run_qa_tests()
