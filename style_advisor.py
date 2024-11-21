import logging
import os
from typing import Dict, List, Optional
import streamlit as st
from pathlib import Path
import requests
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import torch
import sys
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
class StyleAdvisor:
    """Style advisor with RAG capabilities for fashion recommendations"""
    def __init__(self, sambanova_api_key: str):
        self.api_key = sambanova_api_key
        self.api_url = 'https://api.sambanova.ai/v1/chat/completions'
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.docs_path = Path('fashion_docs')  # Updated to relative path
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
        """Initialize FAISS vector store with both style guide and color theory documents"""
        try:
            vector_store_dir = Path("fashion_vectors")
            
            if vector_store_dir.exists():
                self.vector_store = FAISS.load_local(
                    str(vector_store_dir),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                return

            all_docs = []
            for pdf_path in self.docs_path.glob('*.pdf'):
                try:
                    loader = PyPDFLoader(str(pdf_path))
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata["source"] = pdf_path.name
                    all_docs.extend(docs)
                except Exception as e:
                    logging.error(f"Error loading {pdf_path}: {e}")

            if not all_docs:
                return

            # Split documents into chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = splitter.split_documents(all_docs)

            # Create and save vector store
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            os.makedirs(vector_store_dir, exist_ok=True)
            self.vector_store.save_local(str(vector_store_dir))

        except Exception as e:
            logging.error(f"Error in vector store initialization: {e}")
            self.vector_store = None

    def get_style_advice(self, item_description: Dict | str) -> Dict[str, str]:
        """Get style advice using both style guide and color theory sources"""
        try:
            logging.info(f"Initial item_description: {item_description}")  # Debug log
            
            # Parse item details from ai_analysis if it's a JSON string
            if isinstance(item_description, dict) and 'ai_analysis' in item_description:
                logging.info("Found ai_analysis in item_description")  # Debug log
                try:
                    # Extract JSON content from AI analysis if it exists
                    ai_analysis = item_description['ai_analysis']
                    logging.info(f"Raw AI analysis: {ai_analysis}")  # Debug log
                    
                    if ai_analysis and isinstance(ai_analysis, str) and '```json' in ai_analysis:
                        json_content = ai_analysis.split('```json\n')[1].split('\n```')[0]
                        analysis_data = json.loads(json_content)
                        logging.info(f"Parsed analysis data: {analysis_data}")  # Debug log
                        
                        # Combine item name and analysis data
                        item_description = {
                            **analysis_data,
                            'name': item_description.get('name', ''),
                            'brand': analysis_data.get('brand') or item_description.get('brand', 'Unknown')
                        }
                        logging.info(f"Combined item description: {item_description}")  # Debug log
                except (IndexError, json.JSONDecodeError) as e:
                    logging.error(f"Error parsing AI analysis JSON: {e}")
            
            # Get item details with proper fallbacks
            item_type = item_description.get('type', 'Unknown')
            brand = item_description.get('brand', 'Unknown')
            name = item_description.get('name', f"{brand} {item_type}").strip()
            color_info = item_description.get('color', {})
            primary_color = color_info.get('primary', 'Unknown')
            secondary_colors = color_info.get('secondary', [])
            style_info = item_description.get('fit_and_style', {})
            fit = style_info.get('fit', 'Unknown')
            style = style_info.get('style', 'Unknown')
            material = item_description.get('material', 'Unknown')
            
            logging.info(f"""
            Extracted details:
            - Name: {name}
            - Type: {item_type}
            - Brand: {brand}
            - Primary Color: {primary_color}
            - Secondary Colors: {secondary_colors}
            - Fit: {fit}
            - Style: {style}
            - Material: {material}
            """)  # Debug log

            # Create specific queries using actual item details
            style_queries = {
                "style": f"How to style a {primary_color} {item_type} in {style} style? Material: {material}, Fit: {fit}",
                "occasion": f"When and where to wear a {style} {item_type}? Include appropriate settings."
            }
            
            color_queries = {
                "color_theory": f"What colors complement {primary_color} in fashion? Color wheel and color theory recommendations.",
                "color_combinations": f"Color and pattern combinations for a {primary_color} {item_type}."
            }
            
            all_contexts = []
            used_chunks = []

            # Get relevant chunks from each source
            for queries in [style_queries, color_queries]:
                for query_type, query in queries.items():
                    if self.vector_store:
                        docs = self.vector_store.similarity_search(query, k=2)
                        for doc in docs:
                            context = doc.page_content
                            source = doc.metadata.get('source', 'Unknown source')
                            page = doc.metadata.get('page', 'Unknown page')
                            all_contexts.append(context)
                            used_chunks.append(f"From {source}, Page {page}")

            # Combine contexts
            combined_context = "\n\n".join(all_contexts)

            # Create focused prompt with specific item details
            payload = {
                "model": "Meta-Llama-3.1-70B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a fashion advisor combining style recommendations with color theory expertise.
                        Provide specific advice for the exact item being discussed, using its actual characteristics."""
                    },
                    {
                        "role": "user",
                        "content": f"""Using these fashion and color theory excerpts:

    {combined_context}

    Provide styling advice specifically for this {name}:

    Item Details:
    - Type: {item_type}
    - Primary Color: {primary_color}
    - Secondary Colors: {', '.join(secondary_colors) if secondary_colors else 'None'}
    - Style: {style}
    - Fit: {fit}
    - Material: {material}
    - Brand: {brand}

    Title: Styling Advice for {name}

    1. Color Combinations:
    - Specific colors that complement this {primary_color} piece
    - Pattern and texture combinations that work with {material}

    2. Complete Outfit Ideas:
    - Detailed outfit combinations using this {item_type}
    - How to style it for different occasions

    3. Occasions & Settings:
    - Best situations for this particular piece
    - How to adapt it for various settings

    4. Accessories:
    - Specific accessories that complement this piece
    - Final styling tips

    Base advice on both style guides and color theory principles, considering the specific characteristics of this item."""
                    }
                ],
                "temperature": 0.3
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
                    "sources": [f"📚 {chunk}" for chunk in used_chunks]
                }
            else:
                raise Exception(f"API Error: {response.status_code}")

        except Exception as e:
            logging.error(f"Error getting style advice: {e}")
            return {
                "styling_tips": "Unable to provide style advice at this time.",
                "sources": []
            }