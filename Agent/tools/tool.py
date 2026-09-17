import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from huggingface_hub import InferenceClient
from PIL import Image


from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore


load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# Initialize singletons for performance
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
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
    # 1. Retrieve top-k documents from Qdrant
    retrieved_nodes = retriever.retrieve(query)

    if not retrieved_nodes:
        return "No relevant policies or documents were found."

    # 2. Pair query with node contents for CrossEncoder reranking
    pairs = [[query, node.node.get_content()] for node in retrieved_nodes]
    scores = reranker.predict(pairs)

    # 3. Sort by reranker relevance score
    ranked_nodes = sorted(zip(retrieved_nodes, scores), key=lambda x: x[1], reverse=True)

    # 4. Extract top 3 reranked contexts
    top_context = "\n\n---\n\n".join(
        [node.node.get_content() for node, score in ranked_nodes[:3]]
    )

    return top_context


IMAGE_DIR = "../images"

def improvisePrompt(Prompt):
    llm = ChatGoogleGenerativeAI(
        api_key = os.getenv("GEMINI-API-KEY"),
        model = os.getenv("GEMINI-MODEL"),
        temperature = 0.3
    )

    promptTemplate = ChatPromptTemplate(
        [
            ("User", "You are a professional Prompt Engineer with a 10+ years of experience."),
            ("System", """
            Improvise the prompt : 
            {Prompt} 

            for generating an image using AI.  
            """)
        ]
    )

    prompt = promptTemplate.invoke(Prompt = Prompt)

    response = llm.invoke(prompt)

    return response.text

@tool
def generate_image(ppt: str, image_name: str) -> str:
    """
    Generate an image based on the given prompt using Hugging Face Inference API.
    Deletes existing images before creating a new one.

    Args:
        prompt (str): The text description of the image to generate.
        image_name (str): The filename to save the image as (e.g., 'output.png').

    Returns:
        str: Message confirming saved image path.
    """
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not token:
        raise ValueError("HUGGINGFACE_API_TOKEN environment variable not set.")

    os.makedirs(IMAGE_DIR, exist_ok=True)
    image_extensions = ('.png', '.jpg', '.jpeg')

    # Remove previous images if present
    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().endswith(image_extensions):
            os.remove(os.path.join(IMAGE_DIR, filename))

    client = InferenceClient(token=token)

    prompt = improvisePrompt(ppt)
    
    # Generate image using raw prompt string and a valid model target
    image = client.text_to_image(
        prompt=prompt,
        model= os.getenv("MODEL-NAME")
    )

    save_path = os.path.join(IMAGE_DIR, image_name)
    image.save(save_path)

    return f"Image successfully saved to {save_path}"


@tool
def update_image(ppt: str, source_image_name: str, output_image_name: str, strength: float = 0.6) -> str:
    """
    Update/modify an existing image based on a prompt using Hugging Face's Image-to-Image pipeline.

    Args:
        prompt (str): Description of the updates or modifications to apply.
        source_image_name (str): The filename of the base image inside the images folder (e.g., 'input.png').
        output_image_name (str): The filename to save the updated image as (e.g., 'updated.png').
        strength (float): Transformation intensity from 0.0 (no change) to 1.0 (complete overwrite). Default 0.6.

    Returns:
        str: Message confirming saved image path.
    """
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not token:
        raise ValueError("HUGGINGFACE_API_TOKEN environment variable not set.")

    source_path = os.path.join(IMAGE_DIR, source_image_name)
    if not os.path.exists(source_path):
        return f"Error: Source image '{source_image_name}' not found in {IMAGE_DIR}."

    # Open the existing source image
    base_image = Image.open(source_path)

    client = InferenceClient(token=token)

    prompt = improvisePrompt(ppt)

    # Perform image-to-image modification
    updated_image = client.image_to_image(
        image=base_image,
        prompt=prompt,
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


