import os
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from secretkey import openapi_key

# Ensure the OpenAI API key is set correctly
os.environ['OPENAI_API_KEY'] = openapi_key
os.environ['USER_AGENT'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

def load_docs(url):
    loader = WebBaseLoader(url)
    docs = loader.load()
    return docs

def get_text_chunks(docs):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)
    return chunks

def get_vector_store(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(documents=text_chunks, embedding=embeddings)
    retriever = vectorstore.as_retriever()
    return vectorstore, retriever

def format_docs(docs):
    return "\n".join([doc.page_content for doc in docs])

def get_rag_chain(retriever):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    template = """SYSTEM: You are a question-answer bot. 
                 Be factual in your response.
                 Respond to the following question: {question} only from 
                 the below context: {context}. 
                 If you don't know the answer, just say that you don't know.
                 if the {question} is empty, say please enter the question.
               """
    rag_prompt_custom = PromptTemplate.from_template(template)
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt_custom
        | llm
        | StrOutputParser()
    )
    return rag_chain

def gen_answer(url, question):

    docs = load_docs(url)
    chunks = get_text_chunks(docs)
    vectorstore, retriever = get_vector_store(chunks)
    ragchain = get_rag_chain(retriever)
    answer = ragchain.invoke(question)
    del vectorstore

    return answer

