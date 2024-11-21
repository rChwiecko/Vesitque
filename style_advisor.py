import logging
import os
from typing import Dict, List, Optional
import streamlit as st
from pathlib import Path
import requests
import json
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

class StyleAdvisor:
    """Style advisor with RAG capabilities for fashion recommendations"""
    def __init__(self, sambanova_api_key: str):
        self.api_key = sambanova_api_key
        self.api_url = 'https://api.sambanova.ai/v1/chat/completions'
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.docs_path = Path('/Users/alexdang/Closet.ai/fashion_docs')
        self.vector_store = None
        self.embeddings = self._load_embedding_model()
        self._initialize_vector_store()

    def _load_embedding_model(self) -> HuggingFaceEmbeddings:
        """Load embeddings model"""
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': 'cpu'}
        )

    def _initialize_vector_store(self) -> None:
        """Initialize FAISS vector store with balanced document representation"""
        try:
            # Check for existing vector store first
            if Path('fashion_vectors.faiss').exists():
                st.write("📚 Loading existing fashion knowledge base...")
                self.vector_store = FAISS.load_local("fashion_vectors", self.embeddings)
                st.success("✓ Loaded existing fashion knowledge base!")
                return

            # If no existing store, create new one with current code
            all_docs = []
            st.write("📚 Loading fashion guides:")
            
            # Load documents with explicit source tracking
            for pdf_path in self.docs_path.glob('*.pdf'):
                try:
                    st.write(f"- Loading {pdf_path.name}...")
                    loader = PyPDFLoader(str(pdf_path))
                    docs = loader.load()
                    # Explicitly set source in metadata
                    for doc in docs:
                        doc.metadata["source"] = pdf_path.name
                    st.write(f"  ✓ Found {len(docs)} pages")
                    all_docs.extend(docs)
                except Exception as e:
                    st.error(f"❌ Error loading {pdf_path}: {e}")

            if not all_docs:
                st.warning("⚠️ No fashion guides found")
                return

            # Split into chunks with source preservation
            st.write("🔄 Processing documents...")
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""],
                keep_separator=True
            )
            chunks = splitter.split_documents(all_docs)
            st.write(f"✓ Created {len(chunks)} text chunks")

            # Create vector store
            st.write("🔄 Creating vector store...")
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            self.vector_store.save_local("fashion_vectors")
            st.success("✓ Fashion knowledge base created!")

        except Exception as e:
            st.error(f"❌ Error initializing vector store: {e}")
            self.vector_store = None

    def get_style_advice(self, item_description: Dict | str) -> Dict[str, str]:
        """Get balanced style advice from all sources"""
        try:
            # Create focused queries
            if isinstance(item_description, str):
                base_query = item_description
                queries = {
                    "general": base_query,
                    "color": f"Color advice for {base_query}",
                    "style": f"Style and outfit combinations for {base_query}"
                }
            else:
                color = item_description.get('color', {}).get('primary', 'Unknown')
                item_type = item_description.get('type', 'Unknown')
                style = item_description.get('fit_and_style', {}).get('style', 'Unknown')
                
                queries = {
                    "color": f"What colors work well with {color} {item_type}? Color theory and combinations.",
                    "style": f"How to style a {item_type} in {style} style? Outfit combinations.",
                    "occasion": f"When and how to wear {color} {item_type}? Occasion-specific advice."
                }

            st.write("🔍 Finding relevant style information...")
            
            # Get chunks from each source for each query type
            all_contexts = []
            used_chunks = []
            
            for query_type, query in queries.items():
                st.write(f"- Finding {query_type} advice...")
                # Get chunks ensuring representation from each source
                docs = []
                for source in self.docs_path.glob('*.pdf'):
                    source_name = source.name
                    # Filter by source and get top chunks
                    source_docs = self.vector_store.similarity_search(
                        query,
                        k=2,  # Get top 2 chunks from each source
                        filter=lambda x: x["source"] == source_name
                    )
                    docs.extend(source_docs)
                
                # Add chunks to context
                for doc in docs:
                    context = doc.page_content
                    source = doc.metadata.get('source', 'Unknown source')
                    page = doc.metadata.get('page', 'Unknown page')
                    all_contexts.append(context)
                    used_chunks.append(f"From {source}, Page {page}")

            # Combine contexts
            combined_context = "\n\n".join(all_contexts)

            # Group sources by document
            source_summary = {}
            for chunk in used_chunks:
                doc = chunk.split("From ")[-1].split(", Page")[0]
                page = chunk.split("Page ")[-1]
                if doc in source_summary:
                    source_summary[doc].add(page)
                else:
                    source_summary[doc] = {page}

            formatted_sources = [
                f"From {doc}, Pages {', '.join(sorted(pages))}"
                for doc, pages in source_summary.items()
            ]

            # Enhanced prompt to use all sources
            payload = {
                "model": "Meta-Llama-3.1-70B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a professional fashion stylist with expertise in both color theory 
                        and style combinations. Synthesize advice from all provided sources to give comprehensive 
                        recommendations, making sure to incorporate both general style guidelines and specific 
                        color advice."""
                    },
                    {
                        "role": "user",
                        "content": f"""Using these fashion guide excerpts:

    {combined_context}

    Provide complete style advice including:
    1. Color combinations and coordination (be specific about shades and combinations)
    2. Complete outfit suggestions
    3. Occasion-specific recommendations
    4. Accessory pairings
    5. Additional styling tips

    Be sure to incorporate both color theory and style advice from all sources."""
                    }
                ],
                "temperature": 0.7
            }

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                return {
                    "styling_tips": content,
                    "sources": formatted_sources
                }
            else:
                raise Exception(f"API Error: {response.status_code}")

        except Exception as e:
            st.error(f"Error getting style advice: {e}")
            return {
                "styling_tips": "Unable to provide style advice at this time.",
                "sources": []
            }

    def get_outfit_recommendations(self, wardrobe_items: List[Dict]) -> Dict:
        """Get outfit recommendations based on available items"""
        try:
            # Create wardrobe summary
            items_summary = ""
            for item in wardrobe_items:
                color = item.get('color', {}).get('primary', 'Unknown')
                item_type = item.get('type', 'Unknown')
                style = item.get('fit_and_style', {}).get('style', 'Unknown')
                items_summary += f"- {color} {item_type} ({style} style)\n"

            payload = {
                "model": "Meta-Llama-3.1-70B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional fashion stylist. Create complete outfit combinations using available items."
                    },
                    {
                        "role": "user",
                        "content": f"Create 3-4 outfit combinations using these items:\n\n{items_summary}\n\nFor each outfit specify:\n1. Occasion\n2. Main pieces\n3. Accessories\n4. Styling notes"
                    }
                ],
                "temperature": 0.7
            }

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                return {
                    "recommendations": content,
                    "sources": ["Wardrobe Analysis"]
                }
            else:
                raise Exception(f"API Error: {response.status_code}")

        except Exception as e:
            st.error(f"Error getting outfit recommendations: {e}")
            return {
                "recommendations": "Unable to generate outfit recommendations at this time.",
                "sources": []
            }