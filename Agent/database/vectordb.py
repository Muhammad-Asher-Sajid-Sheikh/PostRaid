import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.qdrant import QdrantVectorStore

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
# Use underscore and provide a default fallback string
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "MyCollection")

def initialize_vector_db():
    """Loads text into Document objects, splits into nodes, and populates Qdrant."""
    print("Connecting to Qdrant...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    raw_text = '''
The Information Technology (IT) field encompasses the study, design, development, implementation, support, and management of computer-based information systems. At its core, IT deals with both hardware components—such as servers, routers, and physical storage—and software systems, including applications, operating systems, and databases. In the modern global economy, IT serves as the digital backbone of virtually every industry, from healthcare and finance to education and manufacturing.

Software development and engineering remain a central pillar of the IT industry, focusing on designing, coding, testing, and maintaining applications. Engineers use languages like Python, Java, JavaScript, C++, and Go to build everything from mobile apps to enterprise software systems. Alongside software development, cybersecurity plays a critical role in protecting networks, devices, code, and data from unauthorized access, cyberattacks, and data breaches. Cybersecurity specialists rely on penetration testing, security analysis, threat intelligence, and compliance frameworks to keep digital assets secure.

Cloud computing has reshaped how enterprise systems operate by delivering computing services—including servers, storage, databases, networking, and software—over the internet. Major platforms like Amazon Web Services, Microsoft Azure, and Google Cloud allow organizations to scale their operations quickly without investing in heavy physical hardware. Meanwhile, data science and analytics center on collecting, cleaning, analyzing, and interpreting massive volumes of data to help organizations make strategic, data-driven decisions.

Network and systems administration provides the foundation that keeps organizations connected. Network engineers set up, maintain, and troubleshoot physical and virtual networks, infrastructure, and server environments to ensure continuous uptime and operational reliability. Artificial intelligence and machine learning are expanding this foundation by building smart systems capable of performing tasks that typically require human intelligence, such as natural language processing, computer vision, and predictive modeling.

IT support and help desk teams serve as the frontline operational layer, resolving hardware, software, and connectivity issues for enterprise employees and clients. At the data layer, database administrators manage, secure, and optimize systems like PostgreSQL, MySQL, MongoDB, and Oracle to ensure data integrity and rapid access across applications.

High-demand career paths span a wide variety of roles tailored to different technical strengths. Full-stack developers build both front-end user interfaces and back-end server logic for web applications using tools like React, Node.js, and SQL. DevOps engineers bridge software development and IT operations, utilizing Docker, Kubernetes, Jenkins, and Terraform to streamline continuous integration and delivery pipelines. Cybersecurity analysts monitor networks for security breaches, investigate incidents, and enforce security protocols using tools like Wireshark and Splunk.

Cloud architects design and oversee an organization's overall cloud computing strategy and infrastructure migration, while data engineers construct large-scale data pipelines and data warehouses using tools like Apache Spark, Snowflake, and Airflow. UI and UX designers round out software teams by creating intuitive user interfaces and optimizing the overall user experience through wireframing and continuous user testing.

Several major trends are shaping the future of the IT sector. Automation and generative AI are increasingly streamlining routine coding, customer support, and system monitoring tasks, shifting developer roles toward higher-level system architecture and code review. Edge computing processes data closer to where it is generated—such as IoT devices and autonomous vehicles—to reduce latency and bandwidth usage rather than relying solely on centralized cloud servers.

Organizations are also adopting zero trust security architectures based on the principle of "never trust, always verify," requiring strict identity verification for every user and device attempting to access network resources. At the hardware and computing frontier, quantum computing utilizes quantum mechanics to solve complex mathematical and scientific problems at speeds unattainable by classical supercomputers.

Succeeding in the IT field requires a balance of technical and soft skills. On the technical side, proficiency in major programming or scripting languages, a solid understanding of networking concepts like TCP/IP and firewalls, and experience with version control systems like Git are essential. Equally important are soft skills: analytical problem-solving to debug complex system failures, adaptability to learn evolving tech stacks, and clear communication to translate technical concepts for business stakeholders.

'''

    documents = [Document(text=raw_text, metadata={"department": "IT"})]

    splitter = SentenceSplitter(chunk_size=300, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(documents)

    print("Building vector index in Qdrant...")
    VectorStoreIndex(nodes=nodes, storage_context=storage_context)
    print("Indexing complete!")

if __name__ == "__main__":
    initialize_vector_db()