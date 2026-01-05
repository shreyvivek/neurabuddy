"""Semantic chunking with structure-aware splitting and metadata extraction."""

import re
from typing import List, Dict, Any, Optional
import logging
import tiktoken

from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.models.schemas import SystemType, DifficultyLevel

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Chunks documents into semantically meaningful pieces with rich metadata.
    
    Each chunk represents:
    - One anatomical structure
    - One functional pathway
    - One clinical syndrome
    - One vascular territory
    - One cranial nerve
    - One developmental concept
    """
    
    def __init__(self):
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=self._count_tokens,
            separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""]
        )
        
        # Patterns for identifying neuroanatomical structures
        self.structure_patterns = {
            "cranial_nerve": r"(?:CN\s*)?(?:cranial\s+nerve\s+)?(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|1|2|3|4|5|6|7|8|9|10|11|12)\b",
            "nucleus": r"\b(?:nucleus|nuclei)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?",
            "tract": r"\b(?:tract|pathway|fasciculus)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?",
            "cortex": r"\b(?:cortex|cortical|gyrus|sulcus)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?",
            "ganglion": r"\b(?:ganglion|ganglia)\s+[A-Z][a-z]+",
            "thalamus": r"\bthalamus\b",
            "hypothalamus": r"\bhypothalamus\b",
            "brainstem": r"\b(?:brainstem|medulla|pons|midbrain)\b",
            "cerebellum": r"\bcerebellum\b",
        }
        
        # Clinical terms
        self.clinical_patterns = [
            r"\bstroke\b",
            r"\bsyndrome\b",
            r"\blesion\b",
            r"\bdeficit\b",
            r"\bclinical\b",
            r"\bpathology\b",
            r"\bsymptom\b",
        ]
    
    def chunk_document(
        self,
        content: str,
        source_metadata: Dict[str, Any],
        source: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk a document into semantically meaningful pieces with metadata.
        
        Args:
            content: Document text content
            source_metadata: Metadata from document loader
            source: Source identifier (e.g., "Neuroscience Online")
        
        Returns:
            List of chunk dictionaries with content and metadata
        """
        # First, try to split by major sections/headings
        sections = self._split_by_sections(content)
        
        chunks = []
        
        for section in sections:
            # Further split large sections
            section_chunks = self.text_splitter.split_text(section["content"])
            
            for chunk_text in section_chunks:
                if not chunk_text.strip():
                    continue
                
                # Extract metadata for this chunk
                chunk_metadata = self._extract_chunk_metadata(
                    chunk_text,
                    section.get("heading"),
                    source_metadata,
                    source
                )
                
                chunks.append({
                    "content": chunk_text,
                    "metadata": chunk_metadata
                })
        
        logger.info(f"Created {len(chunks)} chunks from document")
        
        return chunks
    
    def _split_by_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Split content by major headings/sections.
        Returns list of dicts with 'content' and optional 'heading'.
        """
        sections = []
        
        # Pattern for headings (numbered sections, all caps, etc.)
        heading_pattern = re.compile(
            r'^(?:\d+\.?\s+)?([A-Z][A-Z\s]{3,}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*$',
            re.MULTILINE
        )
        
        lines = content.split("\n")
        current_section = {"content": "", "heading": None}
        
        for line in lines:
            # Check if line is a heading
            if heading_pattern.match(line.strip()):
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    "content": line + "\n",
                    "heading": line.strip()
                }
            else:
                current_section["content"] += line + "\n"
        
        # Add final section
        if current_section["content"].strip():
            sections.append(current_section)
        
        # If no sections found, return entire content as one section
        if not sections:
            sections.append({"content": content, "heading": None})
        
        return sections
    
    def _extract_chunk_metadata(
        self,
        chunk_text: str,
        heading: Optional[str],
        source_metadata: Dict[str, Any],
        source: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from a chunk of text.
        
        Returns metadata dict with:
        - structure_name
        - system
        - function
        - clinical_relevance
        - difficulty_level
        - source
        - page/section reference
        """
        metadata = {
            "source": source,
            "chunk_text_preview": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
        }
        
        # Extract structure name
        structure_name = self._extract_structure_name(chunk_text, heading)
        metadata["structure_name"] = structure_name
        
        # Classify system
        system = self._classify_system(chunk_text, structure_name)
        metadata["system"] = system
        
        # Extract function (simplified - could use NLP)
        function = self._extract_function(chunk_text)
        metadata["function"] = function
        
        # Check clinical relevance
        clinical_relevance = self._has_clinical_relevance(chunk_text)
        metadata["clinical_relevance"] = clinical_relevance
        
        # Estimate difficulty level
        difficulty = self._estimate_difficulty(chunk_text)
        metadata["difficulty_level"] = difficulty
        
        # Add source metadata
        if "pages" in source_metadata:
            metadata["page_reference"] = source_metadata.get("pages", [])
        if "title" in source_metadata:
            metadata["section_title"] = source_metadata.get("title")
        if heading:
            metadata["section_heading"] = heading
        
        return metadata
    
    def _extract_structure_name(self, text: str, heading: Optional[str]) -> str:
        """Extract the primary anatomical structure name from text."""
        # Check heading first
        if heading:
            # Look for structure names in heading
            for pattern_name, pattern in self.structure_patterns.items():
                match = re.search(pattern, heading, re.IGNORECASE)
                if match:
                    return match.group(0).strip()
        
        # Search in text
        for pattern_name, pattern in self.structure_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first significant match
                match_text = matches[0] if isinstance(matches[0], str) else matches[0][0]
                return match_text.strip()
        
        # Fallback: extract first capitalized noun phrase
        words = text.split()
        for i, word in enumerate(words):
            if word and word[0].isupper() and len(word) > 3:
                # Try to get a 2-3 word phrase
                phrase = " ".join(words[i:i+2])
                return phrase
        
        return "General Neuroanatomy"
    
    def _classify_system(self, text: str, structure_name: str) -> SystemType:
        """Classify the neuroanatomical system."""
        text_lower = text.lower()
        structure_lower = structure_name.lower()
        
        # Check for specific systems
        if any(term in text_lower for term in ["limbic", "hippocampus", "amygdala", "cingulate"]):
            return SystemType.LIMBIC
        elif any(term in text_lower for term in ["brainstem", "medulla", "pons", "midbrain"]):
            return SystemType.BRAINSTEM
        elif any(term in text_lower for term in ["cortex", "cortical", "gyrus", "sulcus", "frontal", "parietal", "temporal", "occipital"]):
            return SystemType.CORTICAL
        elif any(term in text_lower for term in ["cerebellum", "cerebellar"]):
            return SystemType.CEREBELLAR
        elif any(term in text_lower for term in ["spinal", "cord"]):
            return SystemType.SPINAL
        elif any(term in text_lower for term in ["vascular", "artery", "vein", "territory", "stroke"]):
            return SystemType.VASCULAR
        elif "cranial nerve" in text_lower or "CN" in structure_name:
            return SystemType.CRANIAL_NERVE
        elif any(term in text_lower for term in ["developmental", "embryonic", "fetal"]):
            return SystemType.DEVELOPMENTAL
        else:
            return SystemType.OTHER
    
    def _extract_function(self, text: str) -> str:
        """Extract functional description (simplified)."""
        # Look for function-related phrases
        function_patterns = [
            r"(?:is\s+)?responsible\s+for\s+([^\.]+)",
            r"(?:functions?\s+to|functions?\s+as)\s+([^\.]+)",
            r"(?:involved\s+in|plays\s+a\s+role\s+in)\s+([^\.]+)",
        ]
        
        for pattern in function_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Not specified"
    
    def _has_clinical_relevance(self, text: str) -> bool:
        """Check if chunk has clinical relevance."""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in self.clinical_patterns)
    
    def _estimate_difficulty(self, text: str) -> DifficultyLevel:
        """Estimate difficulty level based on text complexity."""
        # Simple heuristic: count technical terms, sentence length, etc.
        technical_terms = [
            "neurotransmitter", "synapse", "receptor", "pathway", "tract",
            "nucleus", "ganglion", "fasciculus", "commissure", "decussation"
        ]
        
        text_lower = text.lower()
        technical_count = sum(1 for term in technical_terms if term in text_lower)
        
        # Count sentences
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # Heuristic scoring
        if technical_count > 5 or avg_sentence_length > 25:
            return DifficultyLevel.ADVANCED
        elif technical_count > 2 or avg_sentence_length > 18:
            return DifficultyLevel.MED
        else:
            return DifficultyLevel.UNDERGRAD
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.tokenizer.encode(text))

