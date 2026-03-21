from h11._abnf import chunk_size
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader

persist_dir="chroma_db"
pdf_path=r"C:\Users\rahul\Desktop\vscode_files\project1\data\ATW-TS-037 AM050K多主栅光伏划焊联体串焊机维护保养手册-EN-V1.1.pdf"


loader=PyPDFLoader(pdf_path)
docs=loader.load()

print(len(docs))

text_splitter=RecursiveCharacterTextSplitter(
    chunk_size=400,chunk_overlap=60
)

chunks=text_splitter.split_documents(docs)
print(len(chunks))

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore=Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=persist_dir
)
vectorstore.persist()

print("Vector store created successfully and len is ",vectorstore._collection.count())

