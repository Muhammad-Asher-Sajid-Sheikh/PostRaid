import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from huggingface_hub import InferenceClient
from PIL import Image

from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

load_dotenv()

# Configure local embedding model for LlamaIndex to avoid OpenAI API key errors
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "PostRaidCollection")

# Initialize singletons for performance
client = client = QdrantClient(path="./qdrant_local_storage") #QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
retriever = index.as_retriever(similarity_top_k=5)

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


@tool
def rag_tool(query: str) -> str:
    """
    Search and retrieve policies, internal documentation, and guidelines.
    Use this tool whenever you need accurate facts regarding internal company rules.

    Args:
        query (str): The search query or question.

    Returns:
        str: Reranked contextual text excerpts from internal documents.
    """
    retrieved_nodes = retriever.retrieve(query)
    if not retrieved_nodes:
        return "No relevant policies or documents were found."

    pairs = [[query, node.node.get_content()] for node in retrieved_nodes]
    scores = reranker.predict(pairs)

    ranked_nodes = sorted(zip(retrieved_nodes, scores), key=lambda x: x[1], reverse=True)
    top_context = "\n\n---\n\n".join(
        [node.node.get_content() for node, score in ranked_nodes[:3]]
    )
    return top_context

current_dir = os.path.dirname(os.path.abspath(__file__))

# Point to Agent/images explicitly
IMAGE_DIR = os.path.join(current_dir, "../images")

def improvisePrompt(prompt_text: str) -> str:
    llm = ChatGoogleGenerativeAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        temperature=0.3
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("user", "You are a professional Prompt Engineer with 10+ years of experience."),
        ("system", "Improvise the prompt: {Prompt} for generating an image using AI.")
    ])

    formatted_prompt = prompt_template.invoke({"Prompt": prompt_text})
    response = llm.invoke(formatted_prompt)
    
    return response.content


@tool
def generate_image(ppt: str, image_name: str) -> str:
    """
    Generate an image based on the given prompt using Hugging Face Inference API.
    Deletes existing images before creating a new one.

    Args:
        ppt (str): The text description of the image to generate.
        image_name (str): The filename to save the image as (e.g., 'output.png').

    Returns:
        str: Message confirming saved image path.
    """
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not token:
        raise ValueError("HUGGINGFACE_API_TOKEN environment variable not set.")

    os.makedirs(IMAGE_DIR, exist_ok=True)
    image_extensions = ('.png', '.jpg', '.jpeg')

    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().endswith(image_extensions):
            os.remove(os.path.join(IMAGE_DIR, filename))

    hf_client = InferenceClient(token=token)
    improved_prompt = improvisePrompt(ppt)
    
    image = hf_client.text_to_image(
        prompt=improved_prompt,
        model=os.getenv("MODEL_NAME", "stabilityai/stable-diffusion-xl-base-1.0")
    )

    save_path = os.path.join(IMAGE_DIR, image_name)
    image.save(save_path)
    return f"Image successfully saved to {save_path}"


@tool
def update_image(ppt: str, source_image_name: str, output_image_name: str, strength: float = 0.6) -> str:
    """
    Update/modify an existing image based on a prompt using Hugging Face's Image-to-Image pipeline.

    Args:
        ppt (str): Description of the updates or modifications to apply.
        source_image_name (str): The filename of the base image inside the images folder.
        output_image_name (str): The filename to save the updated image as.
        strength (float): Transformation intensity from 0.0 to 1.0. Default 0.6.

    Returns:
        str: Message confirming saved image path.
    """
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not token:
        raise ValueError("HUGGINGFACE_API_TOKEN environment variable not set.")

    source_path = os.path.join(IMAGE_DIR, source_image_name)
    if not os.path.exists(source_path):
        return f"Error: Source image '{source_image_name}' not found in {IMAGE_DIR}."

    base_image = Image.open(source_path)
    hf_client = InferenceClient(token=token)
    improved_prompt = improvisePrompt(ppt)

    updated_image = hf_client.image_to_image(
        image=base_image,
        prompt=improved_prompt,
        strength=strength,
        model="stabilityai/stable-diffusion-xl-refiner-1.0"
    )

    output_path = os.path.join(IMAGE_DIR, output_image_name)
    updated_image.save(output_path)
    return f"Updated image successfully saved to {output_path}"


@tool
def delete_image() -> str:
    """
    Delete all previously created images in the storage directory.

    Returns:
        str: Status message indicating whether files were deleted or missing.
    """
    if not os.path.exists(IMAGE_DIR) or not os.listdir(IMAGE_DIR):
        return "No image was found in the directory."

    for filename in os.listdir(IMAGE_DIR):
        file_path = os.path.join(IMAGE_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    return "All images successfully deleted."


# if __name__ == "__main__":
#     print("=== 1. Testing RAG Tool ===")
#     try:
#         rag_result = rag_tool.invoke({"query": "What is software development?"})
#         print("RAG Result:\n", rag_result)
#     except Exception as e:
#         print("RAG Tool Error:", e)

#     print("\n=== 2. Testing Image Generation Tool ===")
#     try:
#         gen_result = generate_image.invoke({
#             "ppt": "A futuristic neon city skyline at night", 
#             "image_name": "test_city.png"
#         })
#         print(gen_result)
#     except Exception as e:
#         print("Image Gen Error:", e)

#     print("\n=== 3. Testing Update Image Tool ===")
#     try:
#         update_result = update_image.invoke({
#             "ppt": "Add flying spaceships in the sky", 
#             "source_image_name": "test_city.png", 
#             "output_image_name": "test_city_updated.png", 
#             "strength": 0.6
#         })
#         print(update_result)
#     except Exception as e:
#         print("Update Image Error:", e)

#     print("\n=== 4. Testing Delete Image Tool ===")
#     try:
#         delete_result = delete_image.invoke({})
#         print(delete_result)
#     except Exception as e:
#         print("Delete Image Error:", e)