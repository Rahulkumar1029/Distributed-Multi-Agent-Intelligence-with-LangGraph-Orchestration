import os
import sys
import asyncio
from typing_extensions import Annotated, TypedDict
from dotenv import load_dotenv

# Correct modules and missing imports
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import aevaluate, Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot3_rag.rag_engine import build_graph

load_dotenv()

dataset_name = "first_dataset"

# 1. FIX: The `target` function MUST be async to utilize `graph.ainvoke` natively.
#    Langsmith supports async target functions directly, preventing "Event loop is closed" errors.
async def target(inputs: dict) -> dict:
    graph = await build_graph()
    question = inputs["question"]

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": "eval_" + str(hash(question))}}
    )

    messages = result["messages"]

    # ✅ OUTPUT
    output = messages[-1].content
    # Fix for Gemini structured output dictionary response
    if isinstance(output, list):  
        output = "".join([x["text"] for x in output if "text" in x])

    # ✅ CONTEXT
    context = [
        msg.content
        for msg in messages
        if getattr(msg, "type", "") == "tool"
    ]

    if not context:
        context = ["No context retrieved"]

    # 4. FIX: Returning "context" (a list of strings) instead of "documents" (a list of objects).
    return {
        "answer": output,
        "context": context
    }


# ----------------- Evaluators Setup -----------------
# 2. FIX: Evaluator LLMs MUST use ChatGoogleGenerativeAI, since GoogleGenerativeAI lacks
#         native integration with Langchain's method="json_schema" strict structured outputs!

def get_grader_llm(output_schema):
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        api_key=os.getenv("GOOGLE_API_KEY") # Safe to use the main API key for quick parsing
    ).with_structured_output(output_schema, method="json_schema", strict=True)


# -------------- Correctness --------------
class CorrectnessGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    correct: Annotated[bool, ..., "True if the answer is correct, False otherwise."]

correctness_instructions = """You are a teacher grading a quiz. You will be given a QUESTION, the GROUND TRUTH (correct) ANSWER, and the STUDENT ANSWER. Here is the grade criteria to follow:
(1) Grade the student answers based ONLY on their factual accuracy relative to the ground truth answer. (2) Ensure that the student answer does not contain any conflicting statements.
(3) It is OK if the student answer contains more information than the ground truth answer, as long as it is factually accurate relative to the ground truth answer.

Correctness:
A correctness value of True means that the student's answer meets all of the criteria.
A correctness value of False means that the student's answer does not meet all of the criteria.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. Avoid simply stating the correct answer at the outset."""

correctness_llm = get_grader_llm(CorrectnessGrade)

def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> bool:
    """An evaluator for RAG answer accuracy"""
    answers = f"QUESTION: {inputs['question']}\nGROUND TRUTH ANSWER: {reference_outputs.get('answer', '')}\nSTUDENT ANSWER: {outputs['answer']}"
    grade = correctness_llm.invoke([
        {"role": "system", "content": correctness_instructions},
        {"role": "user", "content": answers}
    ])
    return grade["correct"]


# -------------- Relevance --------------
class RelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    relevant: Annotated[bool, ..., "Provide the score on whether the answer addresses the question"]

relevance_instructions = """You are a teacher grading a quiz. You will be given a QUESTION and a STUDENT ANSWER. Here is the grade criteria to follow:
(1) Ensure the STUDENT ANSWER is concise and relevant to the QUESTION
(2) Ensure the STUDENT ANSWER helps to answer the QUESTION

Relevance:
A relevance value of True means that the student's answer meets all of the criteria.
A relevance value of False means that the student's answer does not meet all of the criteria."""

relevance_llm = get_grader_llm(RelevanceGrade)

def relevance(inputs: dict, outputs: dict) -> bool:
    """A simple evaluator for RAG answer helpfulness."""
    answer = f"QUESTION: {inputs['question']}\nSTUDENT ANSWER: {outputs['answer']}"
    grade = relevance_llm.invoke([
        {"role": "system", "content": relevance_instructions},
        {"role": "user", "content": answer}
    ])
    return grade["relevant"]


# -------------- Groundedness --------------
class GroundedGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    grounded: Annotated[bool, ..., "Provide the score on if the answer hallucinates from the documents"]

grounded_instructions = """You are a teacher grading a quiz. You will be given FACTS and a STUDENT ANSWER. Here is the grade criteria to follow:
(1) Ensure the STUDENT ANSWER is grounded in the FACTS. (2) Ensure the STUDENT ANSWER does not contain "hallucinated" information outside the scope of the FACTS.

Grounded:
A grounded value of True means that the student's answer meets all of the criteria."""

grounded_llm = get_grader_llm(GroundedGrade)

def groundedness(inputs: dict, outputs: dict) -> bool:
    """A simple evaluator for RAG answer groundedness."""
    # 4. FIX: Use `outputs["context"]` safely since target returns a list of strings
    doc_string = "\n\n".join(outputs["context"])
    answer = f"FACTS: {doc_string}\nSTUDENT ANSWER: {outputs['answer']}"
    grade = grounded_llm.invoke([
        {"role": "system", "content": grounded_instructions},
        {"role": "user", "content": answer}
    ])
    return grade["grounded"]


# -------------- Retrieval Relevance --------------
class RetrievalRelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    relevant: Annotated[bool, ..., "True if the retrieved documents are relevant to the question, False otherwise"]

retrieval_relevance_instructions = """You are a teacher grading a quiz. You will be given a QUESTION and a set of FACTS provided by the student. Here is the grade criteria to follow:
(1) You goal is to identify FACTS that are completely unrelated to the QUESTION
(2) If the facts contain ANY keywords or semantic meaning related to the question, consider them relevant
(3) It is OK if the facts have SOME information that is unrelated to the question as long as (2) is met"""

retrieval_relevance_llm = get_grader_llm(RetrievalRelevanceGrade)

def retrieval_relevance(inputs: dict, outputs: dict) -> bool:
    """An evaluator for document relevance"""
    # 4. FIX: Use `outputs["context"]` safely since target returns a list of strings
    doc_string = "\n\n".join(outputs["context"])
    answer = f"FACTS: {doc_string}\nQUESTION: {inputs['question']}"
    grade = retrieval_relevance_llm.invoke([
        {"role": "system", "content": retrieval_relevance_instructions},
        {"role": "user", "content": answer}
    ])
    return grade["relevant"]

if __name__ == "__main__":
    client = Client()

    experiment_results = asyncio.run(
    aevaluate(
        target,
        data=dataset_name,
        evaluators=[correctness, groundedness, relevance, retrieval_relevance],
        experiment_prefix="rag-bot-eval",
        max_concurrency=2,
        metadata={"version": "bot 3 langsmith evaluation"},
    )
  )
    print("Sucessfully evaluated bot3 against dataset!")