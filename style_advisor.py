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
            # Define the absolute path for the vector store
            vector_store_dir = Path("/Users/alexdang/Vesitque/fashion_vectors")
            vector_store_path = vector_store_dir / "index.faiss"
            
            # Debug statement to verify the path being checked
            print(f"DEBUG: Checking if vector file exists at {vector_store_path.resolve()}")

            # If the vector store file exists, load it
            if vector_store_path.exists():
                try:
                    print("DEBUG: Vector file found! Loading...")
                    self.vector_store = FAISS.load_local(
                        str(vector_store_dir),
                        self.embeddings,
                        allow_dangerous_deserialization=True  # Add this flag
                    )
                    print("DEBUG: Vector store loaded successfully!")
                    return
                except Exception as e:
                    logging.error(f"❌ Error loading vector store: {e}")
                    st.error("Error loading existing vector store. Creating a new one...")

            # If the file doesn't exist or load fails, create a new one
            print("DEBUG: Vector file not found. Creating a new one...")
            st.write("📚 No existing vector store found. Creating a new one...")
            all_docs = []

            # Load PDFs from the directory
            st.write("📚 Loading fashion guides:")
            for pdf_path in self.docs_path.glob("*.pdf"):
                try:
                    st.write(f"- Loading {pdf_path.name}...")
                    loader = PyPDFLoader(str(pdf_path))
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata["source"] = pdf_path.name
                    st.write(f"  ✓ Found {len(docs)} pages in {pdf_path.name}")
                    all_docs.extend(docs)
                except Exception as e:
                    logging.error(f"Error loading {pdf_path}: {e}")
                    st.error(f"❌ Error loading {pdf_path}: {e}")

            if not all_docs:
                st.warning("⚠️ No fashion guides found to process.")
                return

            # Split documents into chunks
            st.write("🔄 Processing documents...")
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = splitter.split_documents(all_docs)
            st.write(f"✓ Created {len(chunks)} text chunks")

            # Create a new vector store from chunks
            st.write("🔄 Creating vector store...")
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)

            # Save the vector store to disk
            try:
                self.vector_store.save_local(str(vector_store_dir))
                print(f"DEBUG: Vector store created and saved at {vector_store_path.resolve()}")
                logging.info(f"✓ Vector store saved to: {vector_store_path.resolve()}")
                st.success("✓ Fashion knowledge base created and saved!")
            except Exception as e:
                logging.error(f"❌ Error saving vector store: {e}")
                st.error("Error saving vector store.")

        except Exception as e:
            logging.error(f"General error in vector store initialization: {e}")
            st.error(f"❌ Error initializing vector store: {e}")
            self.vector_store = None

    def get_style_advice(self, item_description: Dict | str) -> Dict[str, str]:
        """Get style advice using both style guide and color theory sources"""
        try:
            # Get item details
            if isinstance(item_description, dict):
                item_type = item_description.get('type', 'Unknown')
                item_name = item_description.get('name', item_type)
                color = item_description.get('color', {}).get('primary', 'Unknown')
                style = item_description.get('fit_and_style', {}).get('style', 'Unknown')
            else:
                item_name = item_description
                item_type = item_description
                color = "Unknown"
                style = "Unknown"

            # Separate queries for style guide and color theory
            style_queries = {
                "style": f"How to style a {color} {item_type}? Focus on outfit combinations.",
                "occasion": f"When to wear a {style} {item_type}? Include appropriate settings."
            }
            
            color_queries = {
                "color_theory": f"What colors complement {color}? Color wheel and color theory recommendations.",
                "color_combinations": f"Color combinations and patterns that work with {color} in clothing."
            }
            
            all_contexts = []
            used_chunks = []
            
            # Get style advice from style guide
            for query_type, query in style_queries.items():
                docs = self.vector_store.similarity_search(
                    query,
                    k=2,  # Get top 2 chunks from each source
                    filter=lambda x: x["source"] == "Ultimate-Guide-To-Casual-Mens-Style.pdf"
                )
                
                for doc in docs:
                    context = doc.page_content
                    source = doc.metadata.get('source', 'Unknown source')
                    page = doc.metadata.get('page', 'Unknown page')
                    all_contexts.append(context)
                    used_chunks.append(f"From {source}, Page {page}")
            
            # Get color advice from color guide
            for query_type, query in color_queries.items():
                docs = self.vector_store.similarity_search(
                    query,
                    k=2,  # Get top 2 chunks from each source
                    filter=lambda x: x["source"] == "Color_Men.pdf"
                )
                
                for doc in docs:
                    context = doc.page_content
                    source = doc.metadata.get('source', 'Unknown source')
                    page = doc.metadata.get('page', 'Unknown page')
                    all_contexts.append(context)
                    used_chunks.append(f"From {source}, Page {page}")

            # Combine contexts
            combined_context = "\n\n".join(all_contexts)

            # Format sources
            formatted_sources = [f"📚 {chunk}" for chunk in used_chunks]

            # Updated prompt to specifically reference both style and color advice
            payload = {
                "model": "Meta-Llama-3.1-70B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a fashion advisor combining style recommendations with color theory expertise.
                        Use both the style guide and color theory information to provide comprehensive advice.
                        Focus specifically on the item being discussed and incorporate both practical styling tips
                        and color combination recommendations."""
                    },
                    {
                        "role": "user",
                        "content": f"""Using these fashion and color theory excerpts:

    {combined_context}

    Provide styling advice specifically for this {item_name}:

    Title: Styling Advice for {item_name}

    1. Color Combinations (based on color theory):
    - Recommended color pairings with this {color} piece
    - Color wheel combinations that work well
    - Pattern and texture suggestions

    2. Complete Outfit Ideas:
    - Specific outfit combinations
    - How to dress it up or down
    - Layering suggestions if applicable

    3. Occasions & Settings:
    - Best situations to wear this piece
    - How to style it appropriately

    4. Accessories & Finishing Touches:
    - Complementary accessories
    - Final styling tips

    Base all advice on both the style guides and color theory principles."""
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