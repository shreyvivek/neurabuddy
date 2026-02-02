"""Study engine for flash cards, clinical cases, and study notes."""

import uuid
from typing import List, Dict, Any, Optional
import logging

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from app.core.config import settings
from app.rag.vector_store import VectorStore
from app.models.schemas import DifficultyLevel, SystemType

logger = logging.getLogger(__name__)


class StudyEngine:
    """Generates flash cards, clinical cases, and study notes from the knowledge base."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
        # Active clinical sessions
        self.clinical_sessions: Dict[str, Dict[str, Any]] = {}

    def _search_chunks(self, query: str, top_k: int, filter_dict: Optional[Dict] = None):
        """Search with optional fallback when filters return no results."""
        chunks = self.vector_store.search(
            query=query,
            top_k=top_k,
            filter_dict=filter_dict,
            min_score=0.3
        )
        if not chunks and filter_dict:
            chunks = self.vector_store.search(
                query=query,
                top_k=top_k,
                filter_dict=None,
                min_score=0.3
            )
        return chunks

    def generate_flash_cards(
        self,
        topic: Optional[str] = None,
        num_cards: int = 10,
        difficulty_level: DifficultyLevel = DifficultyLevel.UNDERGRAD,
        system_filter: Optional[SystemType] = None
    ) -> Dict[str, Any]:
        """Generate flash cards from the knowledge base."""
        query = topic or "neuroanatomy key concepts"
        filter_dict = {"difficulty_level": difficulty_level.value} if difficulty_level else {}
        if system_filter:
            filter_dict["system"] = system_filter.value

        # Try with filter first, then without (chunks may not have metadata)
        use_filter = filter_dict if filter_dict else None
        chunks = self._search_chunks(query, max(10, num_cards * 2), use_filter)
        if not chunks:
            chunks = self.vector_store.search(
                query=query,
                top_k=max(10, num_cards * 2),
                filter_dict=None,
                min_score=0.2
            )

        if not chunks:
            return self._generate_flash_cards_from_general_knowledge(topic, num_cards)

        context = "\n\n".join([c["content"] for c in chunks[:num_cards * 2]])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a neuroanatomy educator. Generate flash cards from the given content.
For each card, provide:
1. A clear FRONT (question or term)
2. A clear BACK (answer or definition)
Keep them concise and educational. Format exactly as JSON array:
[{{"front": "...", "back": "..."}}, ...]
Generate exactly {num_cards} flash cards. Output ONLY valid JSON, no markdown."""),
            ("human", "Content:\n{context}\n\nTopic focus: {topic}")
        ])

        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run(
            context=context,
            topic=topic or "general neuroanatomy",
            num_cards=num_cards
        )

        import json
        import re
        cards = self._parse_flash_cards_json(result, num_cards)
        if cards:
            return {"flash_cards": cards, "topic": topic or "neuroanatomy"}
        return self._generate_flash_cards_from_general_knowledge(topic, num_cards)

    def _parse_flash_cards_json(self, result: str, num_cards: int) -> list:
        """Parse flash cards from LLM JSON response."""
        import json
        import re
        result = (result or "").strip()
        if not result:
            return []

        # Strip markdown code block
        if "```" in result:
            parts = result.split("```")
            for p in parts:
                p = p.strip()
                if p.lower().startswith("json"):
                    p = p[4:].strip()
                if p.startswith("["):
                    result = p
                    break
                if p.startswith("{"):
                    result = "[" + p + "]"
                    break

        # Try to extract JSON array
        match = re.search(r'\[[\s\S]*\]', result)
        if match:
            try:
                raw = json.loads(match.group())
                if isinstance(raw, list):
                    cards = []
                    for c in raw:
                        if isinstance(c, dict):
                            front = str(c.get("front") or c.get("question") or "?").strip() or "?"
                            back = str(c.get("back") or c.get("answer") or "").strip()
                            cards.append({"front": front, "back": back})
                    if cards:
                        return cards[:num_cards]
            except json.JSONDecodeError:
                pass

        return []

    def _generate_flash_cards_from_general_knowledge(self, topic: Optional[str], num_cards: int) -> Dict[str, Any]:
        """Generate flash cards from LLM general knowledge when KB is empty."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a neuroanatomy educator. Generate exactly {num_cards} flash cards about neuroanatomy.
Each card MUST have "front" (question or term) and "back" (answer or definition).
Output ONLY a valid JSON array, no other text: [{{"front": "...", "back": "..."}}, ...]
Topic: {topic}"""),
            ("human", "Generate {num_cards} flash cards about {topic}. Output only JSON.")
        ])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run(num_cards=num_cards, topic=topic or "general neuroanatomy")
        cards = self._parse_flash_cards_json(result, num_cards)
        if cards:
            return {"flash_cards": cards, "topic": topic or "neuroanatomy"}
        # Ultimate fallback
        fallback = [
            {"front": "What structure is responsible for memory formation?", "back": "The hippocampus, located in the medial temporal lobe."},
            {"front": "How many cranial nerves are there?", "back": "12 pairs (24 total cranial nerves)."},
            {"front": "What is the blood supply to the brain?", "back": "Internal carotid and vertebral arteries form the Circle of Willis."},
        ]
        return {"flash_cards": fallback[:num_cards], "topic": topic or "neuroanatomy"}

    def generate_clinical_case(
        self,
        topic: Optional[str] = None,
        difficulty_level: DifficultyLevel = DifficultyLevel.MED,
        system_filter: Optional[SystemType] = None
    ) -> Dict[str, Any]:
        """Generate a clinical case/vignette from the knowledge base."""
        query = topic or "clinical neuroanatomy presentation"
        filter_dict = {"difficulty_level": difficulty_level.value}
        if system_filter:
            filter_dict["system"] = system_filter.value

        chunks = self._search_chunks(query, 8, filter_dict)
        if not chunks:
            chunks = self.vector_store.search(query=query or "neuroanatomy", top_k=8, filter_dict=None, min_score=0.2)

        if not chunks:
            return self._generate_clinical_case_from_general(topic, difficulty_level)

        context = "\n\n".join([c["content"] for c in chunks])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical educator. Create a clinical case vignette for neuroanatomy learning.
Include:
1. **Presentation**: Patient demographics and chief complaint
2. **History**: Relevant history
3. **Examination**: Key physical/neuro exam findings
4. **Question**: What is the most likely diagnosis/localization?
5. **Answer**: Diagnosis with anatomical basis
6. **Learning Points**: 2-3 key takeaways
Base this on the provided anatomical content. Make it realistic and educational."""),
            ("human", "Content:\n{context}\n\nTopic: {topic}")
        ])

        chain = LLMChain(llm=self.llm, prompt=prompt)
        case_text = chain.run(context=context, topic=topic or "neuroanatomy")

        return {
            "case": case_text,
            "topic": topic or "clinical neuroanatomy",
            "difficulty": difficulty_level.value
        }

    def _generate_clinical_case_from_general(self, topic: Optional[str], difficulty_level) -> Dict[str, Any]:
        """Generate clinical case from general knowledge when KB is empty."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical educator. Create a clinical case vignette for neuroanatomy learning.
Use markdown formatting. Include:
1. **Presentation**: Patient demographics and chief complaint
2. **History**: Relevant history
3. **Examination**: Key findings
4. **Question**: What is the diagnosis/localization?
5. **Answer**: Diagnosis with anatomical basis
6. **Learning Points**: 2-3 takeaways
Topic: {topic}"""),
            ("human", "Create a clinical case about {topic}")
        ])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        case_text = chain.run(topic=topic or "neuroanatomy")
        return {"case": case_text, "topic": topic or "clinical neuroanatomy", "difficulty": difficulty_level.value}

    def generate_study_notes(
        self,
        topic: str,
        difficulty_level: DifficultyLevel = DifficultyLevel.UNDERGRAD,
        system_filter: Optional[SystemType] = None,
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """Generate structured study notes from the knowledge base."""
        filter_dict = {"difficulty_level": difficulty_level.value}
        if system_filter:
            filter_dict["system"] = system_filter.value

        chunks = self._search_chunks(topic, 10, filter_dict)
        if not chunks:
            chunks = self.vector_store.search(query=topic, top_k=10, filter_dict=None, min_score=0.2)

        if not chunks:
            return self._generate_study_notes_from_general(topic, difficulty_level, include_summary)

        context = "\n\n".join([c["content"] for c in chunks])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a neuroanatomy educator. Create BEAUTIFULLY FORMATTED study notes from the content.

CRITICAL: Use rich markdown formatting throughout:

1. **Headers**: Use # for title, ## for major sections, ### for subsections
2. **Bold** for key terms and anatomical names (e.g., **Broca's area**)
3. *Italics* for definitions and Latin terms (e.g., *nervus oculomotorius*)
4. **Bullet points** (- or *) for lists of concepts, features, clinical points
5. **Numbered lists** (1. 2. 3.) for sequences, steps, or ordered content
6. **Tables** for comparisons (e.g., cranial nerves, blood supply, pathways):
   | Column 1 | Column 2 | Column 3 |
   |----------|----------|----------|
   | Data     | Data     | Data     |
7. **Blockquotes** (>) for key clinical pearls and important takeaways
8. **Horizontal rules** (---) between major sections
9. Be thorough but scannable—use visual hierarchy so students can skim and drill down

Structure:
# Study Notes: [Topic]
## Overview
Brief intro paragraph.
## Key Concepts
Bullets of main ideas with **bold** terms.
## Detailed Content
### [Subsection 1]
Tables and bullets as appropriate.
### [Subsection 2]
...
## Clinical Correlations (if applicable)
Blockquotes for pearls.
## Summary (if requested)
Concise recap with bullets.
## Mnemonics & Tips
Memory aids."""),
            ("human", "Topic: {topic}\n\nContent:\n{context}\n\nInclude summary: {include_summary}")
        ])

        chain = LLMChain(llm=self.llm, prompt=prompt)
        notes = chain.run(
            topic=topic,
            context=context,
            include_summary="yes" if include_summary else "no"
        )

        return {
            "notes": notes,
            "topic": topic,
            "difficulty": difficulty_level.value
        }

    def _generate_study_notes_from_general(self, topic: str, difficulty_level, include_summary: bool) -> Dict[str, Any]:
        """Generate study notes from general knowledge when KB is empty."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a neuroanatomy educator. Create BEAUTIFULLY FORMATTED study notes about {topic}.

Use rich markdown throughout:
- **Headers**: # title, ## sections, ### subsections
- **Bold** for key terms (e.g., **hypothalamus**)
- *Italics* for definitions and Latin terms
- Bullet points (-) and numbered lists (1. 2. 3.)
- **Tables** for comparisons (e.g., structures, functions):
  | Structure | Function | Clinical |
  |-----------|----------|----------|
  | ...       | ...      | ...      |
- Blockquotes (>) for clinical pearls
- Horizontal rules (---) between major sections

Include: Overview, Key Concepts, Detailed Content with tables where helpful, Clinical Correlations, Mnemonics. {summary_instruction}"""),
            ("human", "Create study notes about {topic}")
        ])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        notes = chain.run(
            topic=topic,
            summary_instruction="Add a Summary section at the end." if include_summary else "Do not include a summary."
        )
        return {"notes": notes, "topic": topic, "difficulty": difficulty_level.value}

    def evaluate_flash_card_answer(
        self,
        user_answer: str,
        correct_answer: str,
        question: str
    ) -> Dict[str, Any]:
        """Evaluate user's answer to a flash card using AI."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are evaluating a student's neuroanatomy answer. Be VERY LENIENT and focus on CONCEPTUAL UNDERSTANDING.

Question: {question}
Expected Answer: {correct_answer}
Student Answer: {user_answer}

CRITICAL EVALUATION RULES:
1. **COMPOSITION/COMPONENT questions** ("composed of", "components of", "includes"): If the answer lists multiple items (e.g. brain and spinal cord) and the student names SOME correct components, give PARTIAL CREDIT (0.5). Example: "What is CNS composed of?" + correct: "brain and spinal cord" + student: "brain" → 0.5 (they got one component right).
2. **COMPLETE LIST / ENUMERATION**: For "six lobes", "list all", etc.—student needs MOST items for full credit. Missing half = 0.5.
3. **Focus on meaning, NOT exact wording** - Synonyms and paraphrasing = correct
4. **NUMERICAL/SCIENTIFIC**: Equivalent values, different units = full credit
5. **Give partial credit** whenever the student demonstrates ANY correct understanding—don't give 0.0 unless the answer is wrong or irrelevant
6. **0.0 only when**: Completely wrong, irrelevant, or shows no understanding. If they name even ONE correct component or concept, that's at least 0.5.

Scoring Guidelines:
- **1.0**: Complete answer—all components/items
- **0.5**: Partial—some correct components (e.g. "brain" when answer is "brain and spinal cord"), or partial list
- **0.0**: Wrong, irrelevant, or no correct concepts

Examples:
- CNS composed of? Correct: "brain and spinal cord" | Student: "brain" → 0.5 (partial—got one component)
- CNS composed of? Correct: "brain and spinal cord" | Student: "brain and spinal cord" → 1.0
- "Six lobes?" + student lists 3 → 0.5
- Expected: "1,200–1,500 g" | Student: "1.3–1.4 kg" → 1.0

Format as JSON:
{{{{
    "score": 0.0 or 0.5 or 1.0,
    "feedback": "brief encouraging feedback",
    "is_correct": true/false,
    "is_partial": true/false
}}}}"""),
            ("human", "Evaluate this answer with leniency and focus on conceptual understanding.")
        ])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run(
            question=question,
            correct_answer=correct_answer,
            user_answer=user_answer
        )
        
        import json
        import re
        try:
            match = re.search(r'\{{[\s\S]*\}}', result)
            if match:
                data = json.loads(match.group())
                score = float(data.get("score", 0.0))
                score = max(0.0, min(1.0, score))
                return {
                    "score": score,
                    "feedback": data.get("feedback", ""),
                    "is_correct": data.get("is_correct", score == 1.0),
                    "is_partial": data.get("is_partial", score == 0.5)
                }
        except Exception as e:
            logger.error(f"Error parsing evaluation: {e}")
        
        # Fallback: lenient keyword + numerical comparison
        user_lower = user_answer.lower().strip()
        correct_lower = correct_answer.lower().strip()

        # Extract numbers from both answers for numerical equivalence
        user_nums = set()
        for n in re.findall(r'[\d,]+\.?\d*', user_answer):
            try:
                v = float(n.replace(',', ''))
                user_nums.add(v)
                if 1 < v < 10:  # e.g. 1.3 kg -> also check 1300
                    user_nums.add(v * 1000)
            except ValueError:
                pass
        correct_nums = set()
        for n in re.findall(r'[\d,]+\.?\d*', correct_answer):
            try:
                v = float(n.replace(',', ''))
                correct_nums.add(v)
                if 1 < v < 10:
                    correct_nums.add(v * 1000)
            except ValueError:
                pass

        # Numerical overlap: if key numbers from correct are in user (or within 20%), give credit
        num_overlap = len(correct_nums & user_nums) / len(correct_nums) if correct_nums else 0
        num_close = any(any(abs(u - c) <= c * 0.2 for c in correct_nums) for u in user_nums) if correct_nums and user_nums else False

        # Component-based: "brain and spinal cord" → check if user got brain, spinal, cord
        def extract_components(text):
            parts = re.split(r'\s+and\s+|\s*,\s*|\s+or\s+', text.lower())
            stop = {'the', 'composed', 'includes', 'consists', 'made', 'from', 'cns', 'that', 'which'}
            components = []
            for p in parts:
                words = [w.strip('.,') for w in p.split() if len(w.strip('.,')) >= 4 and w.strip('.,') not in stop]
                components.extend(words)
            return list(dict.fromkeys(components))  # dedupe, keep order

        correct_components = extract_components(correct_lower)
        component_matches = sum(1 for c in correct_components if c in user_lower)
        component_ratio = component_matches / len(correct_components) if correct_components else 0

        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but', 'composed', 'includes'}
        correct_keywords = [w for w in correct_lower.split() if len(w) > 3 and w not in common_words]
        matches = sum(1 for word in correct_keywords if word in user_lower)
        match_ratio = matches / len(correct_keywords) if correct_keywords else 0

        question_lower = question.lower()
        list_indicators = ['six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'all ', 'list ', 'name all', 'enumerate']
        is_list_question = any(x in question_lower for x in list_indicators) or (correct_lower.count(',') >= 3)
        full_credit_threshold = 0.8 if is_list_question else 0.6

        if num_overlap >= 0.5 or num_close:
            return {"score": 1.0, "feedback": "Excellent! You understand the concept well.", "is_correct": True, "is_partial": False}
        if match_ratio >= full_credit_threshold or (component_ratio >= 0.8 and len(correct_components) >= 2):
            return {"score": 1.0, "feedback": "Excellent! You understand the concept well.", "is_correct": True, "is_partial": False}
        if component_ratio >= 0.5 or component_matches >= 1:
            return {"score": 0.5, "feedback": "Good partial answer—you have some components right. Review what you missed.", "is_correct": False, "is_partial": True}
        if match_ratio >= 0.5 and is_list_question:
            return {"score": 0.5, "feedback": "Good partial answer—you're missing some items from the complete list.", "is_correct": False, "is_partial": True}
        if match_ratio >= 0.25 or num_overlap >= 0.25:
            return {"score": 0.5, "feedback": "Good start - you have some key points. Review the full answer.", "is_correct": False, "is_partial": True}
        return {"score": 0.0, "feedback": "Review this concept again.", "is_correct": False, "is_partial": False}

    def analyze_flash_card_session(
        self,
        topic: str,
        total_score: float,
        max_score: float,
        card_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze completed flash card session and recommend next topics."""
        performance_pct = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Prepare detailed results for personalized analysis
        correct_count = sum(1 for r in card_results if r.get("score", 0) == 1.0)
        partial_count = sum(1 for r in card_results if r.get("score", 0) == 0.5)
        incorrect_count = len(card_results) - correct_count - partial_count

        correct_items = [r for r in card_results if r.get("score", 0) == 1.0]
        partial_items = [r for r in card_results if r.get("score", 0) == 0.5]
        incorrect_items = [r for r in card_results if r.get("score", 0) < 0.5]

        results_text = f"Topic: {topic}\nScore: {total_score}/{max_score} ({performance_pct:.1f}%)\n"
        results_text += f"Correct (1.0): {correct_count}, Partial (0.5): {partial_count}, Incorrect (0.0): {incorrect_count}\n\n"

        results_text += "--- DETAILED CARD RESULTS ---\n\n"
        for i, r in enumerate(card_results, 1):
            results_text += f"Card {i} [Score: {r.get('score', 0)}]\n"
            results_text += f"Question: {r.get('question', '?')}\n"
            results_text += f"Student's answer: {r.get('user_answer', '')}\n"
            results_text += f"Correct answer: {r.get('correct_answer', '')}\n"
            if r.get("feedback"):
                results_text += f"Feedback given: {r.get('feedback')}\n"
            results_text += "\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a neuroanatomy learning coach. Analyze this student's flash card session and provide PERSONALIZED feedback.

{results}

CRITICAL: Base your analysis on the ACTUAL questions and answers above. Do NOT give generic advice.

1. **Performance summary**: 2-3 sentences that reference the topic and their actual score. Mention what they did well and what needs work based on the cards.

2. **Strengths**: List 2-3 SPECIFIC concepts they got right. Name the actual topics/questions they answered correctly (e.g. "Brain weight and volume", "Broca's area function"). NOT generic items like "Completed the session".

3. **Areas to improve**: List 2-3 SPECIFIC concepts they got wrong or partially wrong. Reference the actual questions and what they missed (e.g. "Six lobes of the cerebrum—you listed 3; review occipital, insular, limbic lobes"). NOT generic items like "Review incorrect answers".

4. **Recommended topics**: 3-4 neuroanatomy topics to study next, prioritizing topics related to their weak areas from this session.

5. **next_difficulty**: "undergrad", "med", or "advanced" based on performance.

Format as JSON:
{{{{
    "performance_summary": "...",
    "strengths": ["strength 1", "strength 2", ...],
    "areas_to_improve": ["area 1", "area 2", ...],
    "recommended_topics": ["topic 1", "topic 2", "topic 3"],
    "next_difficulty": "undergrad" or "med" or "advanced"
}}}}"""),
            ("human", "Analyze this session and recommend next topics.")
        ])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run(results=results_text)
        
        import json
        import re
        try:
            match = re.search(r'\{{[\s\S]*\}}', result)
            if match:
                data = json.loads(match.group())
                return {
                    "performance_summary": data.get("performance_summary", ""),
                    "strengths": data.get("strengths", []),
                    "areas_to_improve": data.get("areas_to_improve", []),
                    "recommended_topics": data.get("recommended_topics", []),
                    "next_difficulty": data.get("next_difficulty", "undergrad")
                }
        except Exception as e:
            logger.error(f"Error parsing analysis: {e}")
        
        # Fallback: build personalized analysis from card_results
        strengths = []
        areas_to_improve = []
        for r in correct_items[:3]:
            q = (r.get("question") or "?")[:100]
            strengths.append(f"Got it right: {q}..." if len(str(r.get("question", ""))) > 100 else f"Got it right: {q}")
        for r in incorrect_items[:3]:
            q = (r.get("question") or "?")[:80]
            correct_ans = (str(r.get("correct_answer") or ""))[:80]
            areas_to_improve.append(f"Review: {q} — key point: {correct_ans}")
        for r in partial_items[:2]:
            q = (r.get("question") or "?")[:80]
            areas_to_improve.append(f"Partial: {q} — review the complete answer")

        if not strengths:
            strengths = ["You completed the session", "Keep building on the concepts you attempted"]
        if not areas_to_improve:
            areas_to_improve = ["Review any partial answers to strengthen recall", "Try related topics to deepen understanding"]

        if performance_pct >= 80:
            summary = f"Strong performance on {topic}! You scored {total_score}/{max_score}. Focus on the few weak spots below."
            next_diff = "advanced"
        elif performance_pct >= 60:
            summary = f"Good effort on {topic} ({total_score}/{max_score}). You have a solid base—here’s what to sharpen."
            next_diff = "med"
        else:
            summary = f"On {topic} you scored {total_score}/{max_score}. Review the concepts below and try again."
            next_diff = "undergrad"

        return {
            "performance_summary": summary,
            "strengths": strengths,
            "areas_to_improve": areas_to_improve,
            "recommended_topics": [topic, "cranial nerves", "brain anatomy", "spinal cord"][:4] if topic else ["cranial nerves", "brain anatomy", "spinal cord"],
            "next_difficulty": next_diff
        }

    def start_clinical_session(
        self,
        topic: Optional[str] = None,
        difficulty_level: DifficultyLevel = DifficultyLevel.MED,
        system_filter: Optional[SystemType] = None
    ) -> Dict[str, Any]:
        """Start an interactive clinical case simulation."""
        session_id = str(uuid.uuid4())
        query = topic or "clinical neuroanatomy case presentation emergency"
        
        # Get clinical context
        filter_dict = {"clinical_relevance": True}
        if system_filter:
            filter_dict["system"] = system_filter.value
        
        chunks = self._search_chunks(query, 5, filter_dict)
        if not chunks:
            chunks = self.vector_store.search(query=query or "neuroanatomy", top_k=5, filter_dict=None, min_score=0.2)
        
        context = "\n\n".join([c["content"] for c in chunks]) if chunks else "General neuroanatomy clinical knowledge"
        
        # Generate initial presentation
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are creating an IMMERSIVE clinical simulation. The student is now in the OR/emergency room.

Context: {context}

Create a realistic patient presentation. Include:
1. Brief initial presentation (age, chief complaint, how they arrived)
2. What the student can see RIGHT NOW (patient appearance, vital signs)
3. The clinical scenario context (why this case matters)

Make it feel REAL and urgent. Use present tense. Keep it concise - just the initial scene.
Format with **bold** for key vitals/findings."""),
            ("human", "Create an immersive clinical scenario about {topic}")
        ])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        initial_presentation = chain.run(context=context, topic=topic or "neuroanatomy emergency")
        
        # Generate patient name
        import random
        first_names = ["Alex", "Jordan", "Sam", "Taylor", "Morgan", "Casey", "Riley", "Avery"]
        last_names = ["Chen", "Patel", "Johnson", "Garcia", "Kim", "Williams", "Brown", "Martinez"]
        patient_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Store session
        self.clinical_sessions[session_id] = {
            "patient_name": patient_name,
            "topic": topic or "neuroanatomy",
            "difficulty": difficulty_level.value,
            "stage": "initial",
            "context": context,
            "chunks": chunks,
            "initial_presentation": initial_presentation,
            "conversation_history": [],
            "information_gathered": [],
            "questions_asked": 0,
            "correct_decisions": [],
            "incorrect_decisions": [],
            "hints_used": 0,
            "max_hints": 3
        }
        
        return {
            "session_id": session_id,
            "initial_presentation": initial_presentation,
            "patient_name": patient_name,
            "scenario_context": f"You are now in the OR/ER with patient {patient_name}. Ask questions to gather information and make clinical decisions.",
            "stage": "initial",
            "available_hints": 3
        }

    def interact_clinical_session(
        self,
        session_id: str,
        user_message: str,
        request_hint: bool = False
    ) -> Dict[str, Any]:
        """Handle interaction in clinical session."""
        if session_id not in self.clinical_sessions:
            raise ValueError("Session not found")
        
        session = self.clinical_sessions[session_id]
        
        # Handle hint request
        if request_hint and session["hints_used"] < session["max_hints"]:
            hint = self._generate_clinical_hint(session, user_message)
            session["hints_used"] += 1
            return {
                "ai_response": "Here's a hint to guide you:",
                "revealed_information": None,
                "stage": session["stage"],
                "requires_answer": False,
                "question_posed": None,
                "is_correct_path": None,
                "guidance": None,
                "hint_given": hint,
                "available_hints": session["max_hints"] - session["hints_used"],
                "session_complete": False
            }
        
        # Add to conversation history
        session["conversation_history"].append({
            "role": "student",
            "message": user_message
        })
        session["questions_asked"] += 1
        
        # Check if student wants to end the case (e.g. "im done", "I'm done", "done", "that's all")
        done_phrases = ["im done", "i'm done", "i am done", "done", "that's all", "thats all",
                        "finished", "i'm finished", "im finished", "complete", "end case", "end the case"]
        msg_clean = user_message.strip().lower().rstrip(".,!?")
        wants_to_end = msg_clean in done_phrases or any(msg_clean.startswith(p) for p in done_phrases)
        if session["stage"] in ("diagnosis", "gathering_info") and wants_to_end:
            session["stage"] = "complete"
            completion = self._complete_session(session)
            session["conversation_history"].append({"role": "ai", "message": "Clinical simulation complete!"})
            return completion
        
        # Determine stage and generate response
        stage = session["stage"]
        
        if stage == "initial":
            # Student is asking questions to gather information
            response_data = self._handle_information_gathering(session, user_message)
        elif stage == "gathering_info":
            # Continue gathering OR transition to diagnosis
            if session["questions_asked"] >= 3:
                # Evaluate if enough info gathered
                response_data = self._transition_to_diagnosis(session, user_message)
            else:
                response_data = self._handle_information_gathering(session, user_message)
        elif stage == "diagnosis":
            # Student is making clinical decisions
            response_data = self._handle_diagnosis_phase(session, user_message)
        else:
            response_data = self._complete_session(session)
        
        # Update session
        session["conversation_history"].append({
            "role": "ai",
            "message": response_data["ai_response"]
        })
        
        return response_data

    def _generate_clinical_hint(self, session: Dict, user_context: str) -> str:
        """Generate a hint based on current stage."""
        conversation = "\n".join([f"{h['role']}: {h['message']}" for h in session["conversation_history"][-5:]])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are providing a SUBTLE HINT (not the answer!) for a clinical case.

Stage: {stage}
Recent conversation:
{conversation}
Student's current question: {user_context}

Provide a gentle hint that guides thinking without giving away the answer. 
Make it Socratic - ask a leading question or point to what they should consider."""),
            ("human", "Provide a helpful hint.")
        ])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(stage=session["stage"], conversation=conversation, user_context=user_context)

    def _handle_information_gathering(self, session: Dict, user_message: str) -> Dict[str, Any]:
        """Handle student asking questions to gather patient information."""
        conversation = "\n".join([f"{h['role']}: {h['message']}" for h in session["conversation_history"][-8:]])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the clinical team in an OR/ER scenario. The student asked: {user_message}

Context: {context}
Patient: {patient_name}
Conversation so far:
{conversation}

If the question is relevant (history, exam, vitals, labs, imaging), provide the information in a realistic way.
If the question is good clinical reasoning, acknowledge it.
If the question is off-track, gently redirect.

Respond naturally as medical staff would. Use **bold** for key findings. Keep responses concise."""),
            ("human", "The student asked: {user_message}")
        ])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        ai_response = chain.run(
            user_message=user_message,
            context=session["context"],
            patient_name=session["patient_name"],
            conversation=conversation
        )
        
        # Track what information was gathered
        session["information_gathered"].append(user_message)
        
        # Update stage if enough questions asked
        if session["questions_asked"] >= 2:
            session["stage"] = "gathering_info"
        
        return {
            "ai_response": ai_response,
            "revealed_information": None,
            "stage": session["stage"],
            "requires_answer": False,
            "question_posed": None,
            "is_correct_path": None,
            "guidance": None,
            "hint_given": None,
            "available_hints": session["max_hints"] - session["hints_used"],
            "session_complete": False
        }

    def _transition_to_diagnosis(self, session: Dict, user_message: str) -> Dict[str, Any]:
        """Transition from info gathering to diagnosis phase."""
        conversation = "\n".join([f"{h['role']}: {h['message']}" for h in session["conversation_history"]])
        gathered = "\n".join(session["information_gathered"])
        
        # Evaluate if student has enough information
        eval_prompt = ChatPromptTemplate.from_messages([
            ("system", """The student has gathered information. Evaluate if they have ENOUGH to proceed to diagnosis.

Information gathered:
{gathered}

Context: {context}

If they have key information (history, exam findings, etc.), transition them to diagnosis phase.
If critical information is missing, ask them ONE guiding question to get that information first.

Format as JSON:
{{{{
    "ready_for_diagnosis": true/false,
    "transition_message": "message to student",
    "missing_info_question": "question to ask" or null
}}}}"""),
            ("human", "Evaluate readiness")
        ])
        chain = LLMChain(llm=self.llm, prompt=eval_prompt)
        result = chain.run(gathered=gathered, context=session["context"])
        
        import json
        import re
        try:
            match = re.search(r'\{{[\s\S]*\}}', result)
            if match:
                data = json.loads(match.group())
                if data.get("ready_for_diagnosis"):
                    # Transition to diagnosis
                    session["stage"] = "diagnosis"
                    question = self._generate_diagnosis_question(session)
                    return {
                        "ai_response": data.get("transition_message", "You've gathered good information. Now let's proceed."),
                        "revealed_information": None,
                        "stage": "diagnosis",
                        "requires_answer": True,
                        "question_posed": question,
                        "is_correct_path": None,
                        "guidance": None,
                        "hint_given": None,
                        "available_hints": session["max_hints"] - session["hints_used"],
                        "session_complete": False
                    }
                else:
                    # Need more info
                    return {
                        "ai_response": data.get("missing_info_question", "What else would you like to know?"),
                        "revealed_information": None,
                        "stage": "gathering_info",
                        "requires_answer": False,
                        "question_posed": None,
                        "is_correct_path": None,
                        "guidance": None,
                        "hint_given": None,
                        "available_hints": session["max_hints"] - session["hints_used"],
                        "session_complete": False
                    }
        except Exception:
            pass
        
        # Fallback: transition after 3+ questions
        session["stage"] = "diagnosis"
        question = self._generate_diagnosis_question(session)
        return {
            "ai_response": "Based on what you've gathered, let's proceed to diagnosis.",
            "revealed_information": None,
            "stage": "diagnosis",
            "requires_answer": True,
            "question_posed": question,
            "is_correct_path": None,
            "guidance": None,
            "hint_given": None,
            "available_hints": session["max_hints"] - session["hints_used"],
            "session_complete": False
        }

    def _generate_diagnosis_question(self, session: Dict) -> str:
        """Generate a diagnostic question based on the case."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Based on this clinical scenario, generate a diagnostic question.

Context: {context}
Information student gathered: {gathered}

Ask them to make a clinical decision: diagnosis, localization, next step, or intervention.
Make it challenging but fair. Be specific."""),
            ("human", "Generate diagnostic question")
        ])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        gathered = "\n".join(session["information_gathered"])
        return chain.run(context=session["context"], gathered=gathered)

    def _handle_diagnosis_phase(self, session: Dict, user_message: str) -> Dict[str, Any]:
        """Handle student's diagnostic reasoning and decisions."""
        conversation = "\n".join([f"{h['role']}: {h['message']}" for h in session["conversation_history"]])
        
        # Heuristic: detect obviously correct answers (localization with MCA, Broca, Wernicke, etc.)
        msg_lower = user_message.lower()
        correct_signals = [
            "mca", "middle cerebral artery", "broca", "wernicke", "frontal eye field",
            "left hemisphere", "dominant hemisphere", "internal capsule", "motor cortex",
            "left mca", "lateral medullary", "pons", "basilar", "vertebral",
            "vascular territory", "localization", "stroke", "infarct"
        ]
        has_correct_signal = sum(1 for s in correct_signals if s in msg_lower) >= 2
        # If they've given a substantive answer (50+ chars) with correct anatomical terms, treat as likely correct
        likely_correct_heuristic = len(user_message) > 40 and has_correct_signal
        
        # Evaluate student's answer with explicit instructions
        eval_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are evaluating a student's clinical decision in a neuroanatomy case.

Context: {context}
Conversation: {conversation}
Student's answer: {user_message}

CRITICAL: Be LENIENT. If the student correctly identifies:
- Vascular territory (e.g. left MCA, MCA stroke)
- Anatomical localization (Broca's, Wernicke's, motor cortex, frontal eye fields, internal capsule)
- The correct diagnosis (stroke, infarct) with reasonable localization
...then is_correct MUST be true and should_complete should be true if their answer is thorough.

Only mark is_correct=false if they are WRONG (wrong vessel, wrong hemisphere, wrong diagnosis).
If correct: give enthusiastic feedback, set should_complete=true.
If wrong: provide 1-2 GUIDING QUESTIONS (Socratic), set should_complete=false.

Output ONLY valid JSON, no other text:
{{{{
    "is_correct": true or false,
    "feedback": "your response to the student",
    "guiding_questions": ["q1", "q2"] or null,
    "should_complete": true or false
}}}}"""),
            ("human", "Evaluate. Reply with JSON only.")
        ])
        chain = LLMChain(llm=self.llm, prompt=eval_prompt)
        result = chain.run(
            context=session["context"],
            conversation=conversation,
            user_message=user_message
        )
        
        import json
        import re
        parsed = None
        try:
            match = re.search(r'\{[\s\S]*\}', result)
            if match:
                parsed = json.loads(match.group())
        except Exception as e:
            logger.warning(f"Diagnosis eval JSON parse failed: {e}")
        
        if parsed is not None:
            is_correct = parsed.get("is_correct", False)
            
            if is_correct:
                session["correct_decisions"].append(user_message)
            else:
                session["incorrect_decisions"].append(user_message)
            
            if parsed.get("should_complete"):
                session["stage"] = "complete"
                completion = self._complete_session(session)
                return completion
            
            guidance = None
            if not is_correct and parsed.get("guiding_questions"):
                gq = parsed["guiding_questions"]
                guidance = "\n\n".join(gq) if isinstance(gq, list) else str(gq)
            
            return {
                "ai_response": parsed.get("feedback", "Good reasoning."),
                "revealed_information": None,
                "stage": "diagnosis",
                "requires_answer": True if not is_correct else False,
                "question_posed": None,
                "is_correct_path": is_correct,
                "guidance": guidance,
                "hint_given": None,
                "available_hints": session["max_hints"] - session["hints_used"],
                "session_complete": False
            }
        
        # Fallback when JSON parsing fails: use heuristic + simple LLM
        if likely_correct_heuristic:
            session["correct_decisions"].append(user_message)
            session["stage"] = "complete"
            completion = self._complete_session(session)
            return completion
        
        # Last resort: ask simple yes/no, then complete if yes
        try:
            simple_prompt = ChatPromptTemplate.from_messages([
                ("system", """Answer ONLY with a single word: YES or NO.
Given the clinical case and student's answer, is their localization/diagnosis correct?"""),
                ("human", "Case summary: {context}\nStudent: {user_message}")
            ])
            simple_chain = LLMChain(llm=self.llm, prompt=simple_prompt)
            simple_result = simple_chain.run(context=session["context"][:1500], user_message=user_message)
            if "yes" in simple_result.strip().lower():
                session["correct_decisions"].append(user_message)
                session["stage"] = "complete"
                return self._complete_session(session)
        except Exception:
            pass
        
        # Final fallback: do NOT repeat the same generic message; vary it
        return {
            "ai_response": "Your localization sounds reasonable. Can you briefly state the vascular territory and one key anatomical structure involved?",
            "revealed_information": None,
            "stage": "diagnosis",
            "requires_answer": True,
            "question_posed": None,
            "is_correct_path": None,
            "guidance": "Consider: which artery supplies Broca's area, motor cortex, and frontal eye fields?",
            "hint_given": None,
            "available_hints": session["max_hints"] - session["hints_used"],
            "session_complete": False
        }

    def _complete_session(self, session: Dict) -> Dict[str, Any]:
        """Complete the clinical session and provide analysis."""
        conversation = "\n".join([f"{h['role']}: {h['message']}" for h in session["conversation_history"]])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze this completed clinical simulation.

Conversation:
{conversation}

Correct decisions: {correct}
Incorrect decisions: {incorrect}
Hints used: {hints}

Provide comprehensive analysis. Format as JSON:
{{{{
    "performance_summary": "overall assessment",
    "correct_decisions": ["decision 1", "decision 2"],
    "missed_points": ["point 1", "point 2"],
    "clinical_reasoning_score": 0.0-1.0,
    "final_diagnosis_correct": true/false,
    "learning_points": ["point 1", "point 2", "point 3"],
    "recommended_topics": ["topic 1", "topic 2", "topic 3"]
}}}}"""),
            ("human", "Analyze this clinical session")
        ])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run(
            conversation=conversation,
            correct=str(session["correct_decisions"]),
            incorrect=str(session["incorrect_decisions"]),
            hints=session["hints_used"]
        )
        
        import json
        import re
        try:
            match = re.search(r'\{{[\s\S]*\}}', result)
            if match:
                data = json.loads(match.group())
                return {
                    "ai_response": "Clinical simulation complete!",
                    "revealed_information": None,
                    "stage": "complete",
                    "requires_answer": False,
                    "question_posed": None,
                    "is_correct_path": None,
                    "guidance": None,
                    "hint_given": None,
                    "available_hints": 0,
                    "session_complete": True,
                    "completion_data": data
                }
        except Exception:
            pass
        
        # Fallback completion
        score = len(session["correct_decisions"]) / max(len(session["correct_decisions"]) + len(session["incorrect_decisions"]), 1)
        return {
            "ai_response": "Session complete!",
            "revealed_information": None,
            "stage": "complete",
            "requires_answer": False,
            "question_posed": None,
            "is_correct_path": None,
            "guidance": None,
            "hint_given": None,
            "available_hints": 0,
            "session_complete": True,
            "completion_data": {
                "performance_summary": f"You made {len(session['correct_decisions'])} correct decisions.",
                "correct_decisions": session["correct_decisions"],
                "missed_points": session["incorrect_decisions"],
                "clinical_reasoning_score": score,
                "final_diagnosis_correct": score > 0.7,
                "learning_points": ["Review the case", "Study related anatomy", "Practice clinical reasoning"],
                "recommended_topics": ["cranial nerves", "stroke syndromes", "spinal cord injury"]
            }
        }
