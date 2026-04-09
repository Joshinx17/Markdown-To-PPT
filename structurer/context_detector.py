"""
context_detector.py
───────────────────
Analyzes markdown content to understand document type and context,
enabling context-aware styling and layout selection.

Detects:
  • Document type (technical, business, educational, training, research)
  • Tone (formal, casual, technical, storytelling)
  • Content structure patterns
  • Key topics and domains
"""

from __future__ import annotations

import re
from typing import Optional
from dataclasses import dataclass
from parser.md_parser import ParsedDocument


@dataclass
class DocumentContext:
    """Represents the analyzed context of a document."""
    document_type: str  # 'technical', 'business', 'educational', 'training', 'research', 'general'
    tone: str  # 'formal', 'casual', 'technical', 'storytelling'
    is_technical: bool
    is_business: bool
    is_educational: bool
    has_code: bool
    has_diagrams: bool
    primary_domain: str  # e.g., 'AI', 'Finance', 'Engineering', 'General'
    estimated_audience_level: str  # 'beginner', 'intermediate', 'advanced'
    color_scheme: str  # 'teal', 'blue', 'green', 'purple', 'orange', 'navy'
    suggested_layout_emphasis: str  # 'visual', 'textual', 'data-driven'


def detect_context(doc: ParsedDocument) -> DocumentContext:
    """
    Analyze markdown document structure and content to determine
    purpose, tone, and appropriate styling.
    """
    text_lower = doc.all_text.lower()
    title_lower = doc.title.lower()
    
    # Domain detection
    technical_keywords = {
        'python', 'javascript', 'api', 'database', 'algorithm', 'code',
        'server', 'client', 'network', 'system', 'framework', 'library',
        'docker', 'kubernetes', 'git', 'sql', 'html', 'css', 'react',
        'node', 'typescript', 'java', 'c++', 'rust', 'golang', 'debug',
        'compiler', 'deployment', 'architecture', 'performance'
    }
    
    business_keywords = {
        'revenue', 'profit', 'market', 'sales', 'customer', 'roi',
        'strategy', 'business', 'enterprise', 'financial', 'quarterly',
        'growth', 'investment', 'equity', 'valuation', 'stakeholder',
        'executive', 'board', 'proposal', 'pitch', 'partnership'
    }
    
    educational_keywords = {
        'learning', 'education', 'course', 'tutorial', 'guide', 'introduction',
        'learn', 'teach', 'student', 'lesson', 'chapter', 'module',
        'objective', 'quiz', 'exercise', 'practice', 'fundamentals',
        'basics', 'beginner', 'step-by-step'
    }
    
    ai_keywords = {
        'ai', 'machine learning', 'deep learning', 'neural', 'model',
        'training', 'dataset', 'algorithm', 'classification', 'regression',
        'nlp', 'computer vision', 'transformer', 'llm', 'gpt'
    }
    
    finance_keywords = {
        'stock', 'crypto', 'investment', 'portfolio', 'hedge', 'derivative',
        'risk', 'volatility', 'interest', 'bond', 'market', 'trading'
    }
    
    # Count keyword occurrences
    tech_count = sum(1 for kw in technical_keywords if kw in text_lower)
    business_count = sum(1 for kw in business_keywords if kw in text_lower)
    edu_count = sum(1 for kw in educational_keywords if kw in text_lower)
    ai_count = sum(1 for kw in ai_keywords if kw in text_lower)
    finance_count = sum(1 for kw in finance_keywords if kw in text_lower)
    
    # Determine primary domain
    domain_scores = {
        'AI/ML': ai_count,
        'Finance': finance_count,
        'Technology': tech_count,
        'Business': business_count,
        'Education': edu_count,
    }
    primary_domain = max(domain_scores, key=domain_scores.get)
    
    # Determine document type
    is_technical = tech_count > 5
    is_business = business_count > 5
    is_educational = edu_count > 5
    has_code = '```' in doc.raw_markdown or 'def ' in text_lower or 'function' in text_lower
    
    if is_technical and has_code:
        doc_type = 'technical'
    elif is_business:
        doc_type = 'business'
    elif is_educational:
        doc_type = 'educational'
    elif 'training' in title_lower or 'workshop' in title_lower:
        doc_type = 'training'
    elif 'research' in title_lower or 'study' in title_lower:
        doc_type = 'research'
    else:
        doc_type = 'general'
    
    # Determine tone
    formal_indicators = [
        'therefore', 'furthermore', 'consequently', 'methodology',
        'according to', 'research', 'analysis', 'evidence'
    ]
    casual_indicators = [
        'let\'s', 'think about', 'awesome', 'cool', 'basically',
        'like', 'interesting', 'curious'
    ]
    
    formal_count = sum(1 for phrase in formal_indicators if phrase in text_lower)
    casual_count = sum(1 for phrase in casual_indicators if phrase in text_lower)
    
    if formal_count > casual_count:
        tone = 'formal'
    elif casual_count > formal_count:
        tone = 'casual'
    elif is_technical:
        tone = 'technical'
    else:
        tone = 'storytelling'
    
    # Determine color scheme based on domain and type
    if primary_domain == 'AI/ML':
        color_scheme = 'purple'  # Modern/innovative
    elif primary_domain == 'Finance':
        color_scheme = 'blue'  # Trust/stability
    elif primary_domain == 'Technology':
        color_scheme = 'teal'  # Modern/tech
    elif is_business:
        color_scheme = 'navy'  # Professional/corporate
    elif is_educational:
        color_scheme = 'green'  # Growth/learning
    else:
        color_scheme = 'teal'
    
    # Determine audience level
    if is_educational or 'beginner' in title_lower or 'introduction' in title_lower:
        audience = 'beginner'
    elif 'advanced' in title_lower or 'expert' in title_lower or doc_type == 'research':
        audience = 'advanced'
    else:
        audience = 'intermediate'
    
    # Determine layout emphasis
    has_diagrams = any(x in doc.raw_markdown for x in ['```mermaid', '```ascii', '```plaintext'])
    has_lots_of_data = doc.has_numerical_data and doc.has_tabular_data
    has_code_blocks = doc.raw_markdown.count('```') > 3
    
    if has_code_blocks or has_diagrams:
        layout_emphasis = 'visual'
    elif has_lots_of_data:
        layout_emphasis = 'data-driven'
    else:
        layout_emphasis = 'textual'
    
    return DocumentContext(
        document_type=doc_type,
        tone=tone,
        is_technical=is_technical,
        is_business=is_business,
        is_educational=is_educational,
        has_code=has_code,
        has_diagrams=has_diagrams,
        primary_domain=primary_domain,
        estimated_audience_level=audience,
        color_scheme=color_scheme,
        suggested_layout_emphasis=layout_emphasis,
    )
