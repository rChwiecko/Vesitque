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
        """Initialize FAISS vector store with fashion guides"""
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
            for pdf_path in self.docs_path.glob('*.pdf'):
                try:
                    st.write(f"- Loading {pdf_path.name}...")
                    loader = PyPDFLoader(str(pdf_path))
                    docs = loader.load()
                    st.write(f"  ✓ Found {len(docs)} pages")
                    all_docs.extend(docs)
                except Exception as e:
                    st.error(f"❌ Error loading {pdf_path}: {e}")

            if not all_docs:
                st.warning("⚠️ No fashion guides found - using basic style rules only")
                return

            # Show chunks being created
            st.write("🔄 Processing documents...")
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
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
        """Get style advice for a specific item"""
        try:
            # Convert string descriptions to dict format
            if isinstance(item_description, str):
                query = item_description
            else:
                # Extract relevant details
                color = item_description.get('color', {}).get('primary', 'Unknown')
                item_type = item_description.get('type', 'Unknown')
                style = item_description.get('fit_and_style', {}).get('style', 'Unknown')
                query = f"How to style a {color} {item_type} in {style} style?"

            st.write("🔍 Query:", query)

            # Get relevant chunks from fashion guides
            used_chunks = []
            if self.vector_store:
                docs = self.vector_store.similarity_search(query, k=3)
                context = "\n\n".join(doc.page_content for doc in docs)
                # Track which parts of the guides were used
                for doc in docs:
                    source = doc.metadata.get('source', 'Unknown source')
                    page = doc.metadata.get('page', 'Unknown page')
                    used_chunks.append(f"From {source}, Page {page}")
            else:
                context = ""
                st.warning("⚠️ No fashion guides loaded - using basic advice only")

            payload = {
                "model": "Meta-Llama-3.1-70B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a professional fashion stylist. Provide specific, 
                        actionable advice using the fashion guide context when available."""
                    },
                    {
                        "role": "user",
                        "content": f"Using this fashion guide information:\n\n{context}\n\nProvide styling advice for: {query}\n\nInclude:\n1. Complete outfit combinations\n2. Occasion-specific tips\n3. Color coordination\n4. Accessory suggestions"
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
                    "sources": used_chunks if used_chunks else ["Basic style rules"]
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