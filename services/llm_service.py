import os
import globals
import ollama
import chromadb
import json
import sqlite3


# Save the host name and port for the server that will be running the Ollama API and the ChromaDB vector database.
# OLLAMA_CHROMA_HOST = "10.162.32.132"  # The server host IP address. Hostname is actually eng-gilm122-02

# Set the variable for the default LLM model
DEFAULT_LLM = 'llama3.2'
# OLLAMA_API_PORT = 11434


# ChromaDB configuration.
CHROMADB_PATH = "D:\\AgWaterLLM\\chroma_database"
CHROMADB_COLLECTION_NAME = "encodings"
# CHROMADB_PORT = 8000

# Set the path to the SQLite database file
DB_PATH = "D:\\Websites\\AgWaterAPI\\sqliteDBs\\agWater.db"


def retrieve_relevant_chunks(query_string, top_n=3):
    """
    Retrieve the most relevant chunks from the Qdrant vector database
    based on the query string.

    Input:
    - query_string (str): The query string to search for in the Qdrant vector database.
    - top_n (int): The number of most relevant chunks to return. Default is 3.

    Output:
    - scored_points (list): A list of the most relevant chunks and their similarity scores.
    """

    # Generate the embedding for the query string using Ollama's embedding model.
    # ChromaDB automatically handles embedding generation, so we can use it directly.

    # Open our ChromaDB vector database
    #chroma_client = chromadb.PersistentClient(path=CHROMADB_PATH)
    chroma_client = chromadb.HttpClient(host="localhost", port=8100)  # Use the HTTP client to connect to ChromaDB. Preferred for production use

    #globals.llm_logger.info(f" - retrieve_relevant_chunks: Connected to ChromaDB collection {CHROMADB_COLLECTION_NAME}")
    chroma_collection = chroma_client.get_collection(name=CHROMADB_COLLECTION_NAME)

    # Search the ChromaDB collection for the most relevant chunks
    query_results = chroma_collection.query(
        query_texts=[query_string],  # The query string to search for. Automatically encoded by ChromaDB
        n_results=top_n,  # The number of most relevant chunks to return
        include=["documents", "metadatas"]  # Include the documents and metadata in the results
    )


    #globals.llm_logger.info(f" - retrieve_relevant_chunks: Query successful! Query results: {query_results}")
    qrd0 = query_results['documents'][0]
    qrm0 = query_results['metadatas'][0]
    #globals.llm_logger.info(f" - Query successful! Number of results: {len(qrd0)}")
    #globals.llm_logger.info(f" - Query results: {qr0[0]}")  # Log the first document returned
    #globals.llm_logger.info(f" - Query metadata: {qrm0}")  # Log the metadata for the first document returned

    _qrd0 = list(qrd0)  # Convert the documents to a list
    _qrm0 = list(qrm0)  # Convert the metadata to a list
    
    scored_points = list(zip(_qrd0, _qrm0))
    #globals.llm_logger.info(f" - scored_points is {scored_points}")

    # With the scored_points gathered, we can now return those points to be
    # used as context for the LLM. We will return the top_n most relevant chunks
    # and their similarity scores.

    return scored_points  # Return the scored points as a list of tuples (document, metadata)


def get_llm_output(parameters):
    """
    This function accepts a user query and uses it to query the Chroma database
    for any relevant information to provide context for the LLM model.
    
    It then uses the Ollama API to generate a response based on the query and
    the retrieved context.
    
    Args:
        user_query (str): The user's question to be processed by the LLM.
        chat_history (list[dict]): A list of previous messages in the chat history.
                                  This is optional and can be used to provide context for the LLM.
        llm_model (str): The name of the LLM model to use. Defaults to DEFAULT_LLM.
        
    Returns:
        str: A JSON string with the LLM's response and a list of referenced documents.
    """
    globals.llm_logger.info(f" - get_llm_output: Called with parameters: {parameters}")

    # Parse the parameters from the request
    user_query = parameters['user_query'].strip()  # Get the user query from the parameters and strip any leading/trailing whitespace
    if not user_query:
        return {"error": "User query cannot be empty"}, 400
    
    chat_history_raw = parameters['chat_history']  # Assuming chat_history is a list of previous messages
    chat_history = []
    for msg in chat_history_raw:
        chat_history.append({"role": "user", "content": msg["question"]})
        chat_history.append({"role": "assistant", "content": msg["answer"]})

    llm_model = parameters['llm_model']  # if 'llm_model' in parameters else DEFAULT_LLM  # Use the specified LLM model or default to DEFAULT_LLM if not provided
    

    globals.llm_logger.info(f" - get_llm_output: User query: {user_query}")
    globals.llm_logger.info(f" - get_llm_output: Chat history: {chat_history}")
    globals.llm_logger.info(f" - get_llm_output: LLM model: {llm_model}")

    #stream = parameters['stream']  # if 'stream' in parameters else False  # Whether to stream the response from the LLM, default is False
    # globals.llm_logger.info("get_llm_output: Retrieving relevant chunks for the user query. Calling retrieve_relevant_chunks()")
    # IMPORTANT: We are using a top_n of 6 to retrieve the most relevant chunks from the Chroma database.
    # This can be adjusted based on the use case and the amount of context needed for the LLM to generate a response.
    # HOWEVER, if we attempt to use too many context chunks, the LLM may not be able to process them all, or may not be able to reference the chat history either.
    # When top_n < 6, the LLM is not provided enough context to generate an informative response.
    context_chunks = retrieve_relevant_chunks(user_query, top_n=10)

    # context_chunks will be a list of tuples (text, metadata) where
    # text is the text chunk and metadata is a dictionary containing
    # the filename and other relevant information.
    # For example, context_chunks = [(text_chunk_1, {'source_file': 'file1.txt'}), (text_chunk_2, {'source_file': 'file2.txt'})]

    # Save the file name for each point in a set to use to generate our references
    referenced_documents = set()

    # Iterate through the retrieved context chunks and store the text and metadata
    # in a list of tuples (text, file_name).
    for _, metadata in context_chunks:
        # Store the text and file name in the list of context chunks
        # The metadata is a dictionary containing the document ID and other relevant information.
        referenced_documents.add(metadata['source_file'])
        #context_chunks.append((text, metadata['source_file']))


    # instruction_prompt = f'''You are a helpful chatbot that only answers questions related to agriculture and water management.
    # Use the previous conversation history and the following pieces of context to answer the question.
    # {'\n'.join([f' - {doc}' for doc, _ in context_chunks])}
    # '''

    # AgWater specific instruction prompt for the chatbot. Still needs further work
    # to ensure that the chatbot only answers questions related to agriculture and water management.
    instruction_prompt = f'''You are a helpful chatbot that only answers questions related to agriculture and water management.
    Use the previous conversation history and the following pieces of context to answer the question. If the answer is not in the context, state that the answer is not available.
    Don't make up any new information and strictly only rely on the sources provided and the chat history:
    {'\n'.join([f' - {doc}' for doc, _ in context_chunks])}
    '''


    #globals.llm_logger.info(f"after setting instruction prompt - user_query={user_query}, llm_model={llm_model}, stream={stream}")

    ollama_messages = chat_history + [
        {'role': 'system', 'content': instruction_prompt},
        {'role': 'user', 'content': user_query}
    ]


    # Use the Ollama API to chat with the chatbot
    response = ollama.chat(
        model = llm_model,  # Use the specified LLM model
        # messages = chat_history + [
        #     {'role': 'system', 'content': instruction_prompt},
        #     {'role': 'user', 'content': user_query},
        # ],
        messages = ollama_messages,
        stream = False,  # Set to True for streaming response
    )

    #
    rds = list(referenced_documents)
    rts, _ = get_titles_from_filenames(rds)  # Get the titles for the referenced documents

    # Check if the response is being streamed or not. If it is being streamed, we need to handle the resulting ChatResponse Generator object
    # if stream:
    #     # If the response is being streamed, we need to handle the ChatResponse Generator object
    #     # and return the responses as they are generated.
    #     for chunk in response:
    #         # globals.llm_logger.info(f" - get_llm_output: Streaming response chunk: {chunk['message']['content']}")
    #         # This implementation does retrieve each chunk of the response as it is generated,
    #         # Return the chunk as a JSON string with the chat response and referenced documents
    #         yield json.dumps({"llm_response": chunk['message']['content'], "done": False})
    #         #yield chunk['message']['content']

    #     globals.llm_logger.info(f" - get_llm_output: returning references for the documents: {rds}")
    #     yield json.dumps({"done": True, "referenced_documents": rds, "referenced_titles": rts})  # Indicate that the streaming is done

    # else:   # If the response is not being streamed, we can return the final response directly
        #globals.llm_logger.info(f" - get_llm_output: Final response: {response['message']['content']}")
    return json.dumps({"content_type": "llm_response", "llm_response": response['message']['content'], "referenced_documents": rds, 'referenced_titles': rts})



def get_llm_output_stream(parameters):
    """
    This function accepts a user query and uses it to query the Chroma database
    for any relevant information to provide context for the LLM model.
    
    It then uses the Ollama API to generate a response based on the query and
    the retrieved context.
    
    Args:
        user_query (str): The user's question to be processed by the LLM.
        chat_history (list[dict]): A list of previous messages in the chat history.
                                  This is optional and can be used to provide context for the LLM.
        llm_model (str): The name of the LLM model to use. Defaults to DEFAULT_LLM.
        
    Returns:
        str: A JSON string with the LLM's response and a list of referenced documents.
    """
    
    # Parse the parameters from the request
    user_query = parameters['user_query'].strip()  # Get the user query from the parameters and strip any leading/trailing whitespace
    if not user_query:
        return {"error": "User query cannot be empty"}, 400
    
    chat_history_raw = parameters['chat_history']  # Assuming chat_history is a list of previous messages each stored as a dictionary with "question" and "answer" keys
    # IMPORTANT: In order for the LLM to be able to use the chat history, it must be a list of dictionaries that contains the "role" and "content" keys for both
    # user and assistant messages. If the chat history is not in this format, it will not work correctly.
    # {"question": "What is drip irrigation?", "answer": "Drip irrigation is a method of irrigation..."} -> {"role": "user", "content": "What is drip irrigation?"}, {"role": "assistant", "content": "Drip irrigation is a method of irrigation..."}
    chat_history = []
    for msg in chat_history_raw:
        chat_history.append({"role": "user", "content": msg["question"]})
        chat_history.append({"role": "assistant", "content": msg["answer"]})

    llm_model = parameters['llm_model']  # if 'llm_model' in parameters else DEFAULT_LLM  # Use the specified LLM model or default to DEFAULT_LLM if not provided
    
    #stream = parameters['stream']  # if 'stream' in parameters else False  # Whether to stream the response from the LLM, default is False

    # globals.llm_logger.info("get_llm_output: Retrieving relevant chunks for the user query. Calling retrieve_relevant_chunks()")
    # IMPORTANT: We are using a top_n of 3 to retrieve the most relevant chunks from the Chroma database.
    # This can be adjusted based on the use case and the amount of context needed for the LLM to generate a response.
    # HOWEVER, if we attempt to use too many context chunks, the LLM may not be able to process them all, or may not be able to reference the chat history either.
    context_chunks = retrieve_relevant_chunks(user_query, top_n=10)

    # context_chunks will be a list of tuples (text, metadata) where
    # text is the text chunk and metadata is a dictionary containing
    # the filename and other relevant information.
    # For example, context_chunks = [(text_chunk_1, {'source_file': 'file1.txt'}), (text_chunk_2, {'source_file': 'file2.txt'})]

    # Save the file name for each point in a set to use to generate our references
    referenced_documents = set()

    # Iterate through the retrieved context chunks and store the text and metadata
    # in a list of tuples (text, file_name).
    for _, metadata in context_chunks:
        # Store the text and file name in the list of context chunks
        # The metadata is a dictionary containing the document ID and other relevant information.
        referenced_documents.add(metadata['source_file'])
        #context_chunks.append((text, metadata['source_file']))

    # instruction_prompt = f'''You are a helpful chatbot that only answers questions related to agriculture and water management.
    # Use the previous conversation history and the following pieces of context to answer the question.
    # {'\n'.join([f' - {doc}' for doc, _ in context_chunks])}
    # '''

    # AgWater specific instruction prompt for the chatbot. Still needs further work
    # to ensure that the chatbot only answers questions related to agriculture and water management.
    instruction_prompt = f'''You are a helpful chatbot that only answers questions related to agriculture and water management.
    Use only the previous conversation history and the following pieces of context to answer the question. If the answer is not in the context, state that the answer is not available.
    Don't make up any new information and strictly only rely on the sources provided and the chat history:
    {'\n'.join([f' - {doc}' for doc, _ in context_chunks])}
    '''


    #globals.llm_logger.info(f"after setting instruction prompt - user_query={user_query}, llm_model={llm_model}, stream={stream}")

    ollama_messages = chat_history + [
        {'role': 'system', 'content': instruction_prompt},
        {'role': 'user', 'content': user_query}
    ]


    # Use the Ollama API to chat with the chatbot
    response = ollama.chat(
        model = llm_model,  # Use the specified LLM model
        # messages = chat_history + [
        #     {'role': 'system', 'content': instruction_prompt},
        #     {'role': 'user', 'content': user_query},
        # ],
        messages = ollama_messages,
        stream = True,  # Set to True for streaming response
    )

    #
    rds = list(referenced_documents)
    rts, _ = get_titles_from_filenames(rds)  # Get the titles for the referenced documents

    # Check if the response is being streamed or not. If it is being streamed, we need to handle the resulting ChatResponse Generator object
    # if stream:
    # If the response is being streamed, we need to handle the ChatResponse Generator object
    # and return the responses as they are generated.

    yield json.dumps({"content_type": "document_info", "referenced_documents": rds, "referenced_titles": rts}) + "\n"

    for chunk in response:
        # globals.llm_logger.info(f" - get_llm_output: Streaming response chunk: {chunk['message']['content']}")
        # This implementation does retrieve each chunk of the response as it is generated,
        # Return the chunk as a JSON string with the chat response and referenced documents
        yield json.dumps({"content_type": "llm_response", "llm_response": chunk['message']['content']}) + "\n"  # Yield each chunk of the response as a JSON string, including a newline character for proper streaming
        #yield chunk['message']['content']

    #globals.llm_logger.info(f" - get_llm_output: returning references for the documents: {rds}")
    #yield json.dumps({"done": True, "referenced_documents": rds, "referenced_titles": rts})  # Indicate that the streaming is done

    # else:   # If the response is not being streamed, we can return the final response directly
    #globals.llm_logger.info(f" - get_llm_output: Final response: {response['message']['content']}")
    #return json.dumps({"llm_response": response['message']['content'], "referenced_documents": rds, 'referenced_titles': rts, "done": True})



def get_llm_output_without_RAG(parameters):
    """
    This function accepts a user query and uses it to query the Chroma database
    for any relevant information. However, this information is NOT provided as context
    to the LLM model. Instead, it simply uses the user query to generate a response
    from the LLM model without any additional context.
    
    THIS FUNCTION IS INTENDED FOR TESTING PURPOSES ONLY AND SHOULD NOT BE USED IN PRODUCTION.
    
    Args:
        user_query (str): The user's question to be processed by the LLM.
        llm_model (str): The name of the LLM model to use. Defaults to DEFAULT_LLM.
        
    Returns:
        str: A JSON string with the LLM's response and a list of the documents most relevant to the user's query.
    """
    
    # Parse the parameters from the request
    user_query = parameters['user_query'].strip()  # Get the user query from the parameters and strip any leading/trailing whitespace
    if not user_query:
        return {"error": "User query cannot be empty"}, 400
    
    #chat_history = parameters['chat_history']  # Assuming chat_history is a list of previous messages
    
    llm_model = parameters['llm_model']  # if 'llm_model' in parameters else DEFAULT_LLM  # Use the specified LLM model or default to DEFAULT_LLM if not provided

    chat_history_raw = parameters['chat_history']  # Assuming chat_history is a list of previous messages each stored as a dictionary with "question" and "answer" keys
    # IMPORTANT: In order for the LLM to be able to use the chat history,
    # it must be a list of dictionaries that contains the "role" and "content" keys for both
    # user and assistant messages. If the chat history is not in this format, it will not work correctly.
    chat_history = []
    for msg in chat_history_raw:
        chat_history.append({"role": "user", "content": msg["question"]})
        chat_history.append({"role": "assistant", "content": msg["answer"]})

    #stream = parameters['stream']  # if 'stream' in parameters else False  # Whether to stream the response from the LLM, default is False

    # globals.llm_logger.info("get_llm_output: Retrieving relevant chunks for the user query. Calling retrieve_relevant_chunks()")
    context_chunks = retrieve_relevant_chunks(user_query, top_n=3)

    # context_chunks will be a list of tuples (text, metadata) where
    # text is the text chunk and metadata is a dictionary containing
    # the filename and other relevant information.
    # For example, context_chunks = [(text_chunk_1, {'source_file': 'file1.txt'}), (text_chunk_2, {'source_file': 'file2.txt'})]

    # Save the file name for each point in a set to use to generate our references
    referenced_documents = set()

    # Iterate through the retrieved context chunks and store the text and metadata
    # in a list of tuples (text, file_name).
    for _, metadata in context_chunks:
        # Store the text and file name in the list of context chunks
        # The metadata is a dictionary containing the document ID and other relevant information.
        referenced_documents.add(metadata['source_file'])
        #context_chunks.append((text, metadata['source_file']))


    # AgWater specific instruction prompt for the chatbot. Still needs further work
    # to ensure that the chatbot only answers questions related to agriculture and water management.
    instruction_prompt = f'''You are a helpful chatbot. Answer the user's question as best as you can.'''
    #globals.llm_logger.info(f"after setting instruction prompt - user_query={user_query}, llm_model={llm_model}, stream={stream}")

    ollama_messages = chat_history + [
        {'role': 'system', 'content': instruction_prompt},
        {'role': 'user', 'content': user_query},
    ]

    # Use the Ollama API to chat with the chatbot
    response = ollama.chat(
        model=llm_model,  # Use the specified LLM model
        # messages=chat_history + [
        #     {'role': 'system', 'content': instruction_prompt},
        #     {'role': 'user', 'content': user_query},
        # ],
        messages=ollama_messages,
        stream=False,  # Set to True for streaming response
    )

    #
    rds=list(referenced_documents)
    rts, _ = get_titles_from_filenames(rds)  # Get the titles for the referenced documents

    # If the response is not being streamed, we can return the final response directly
    #globals.llm_logger.info(f" - get_llm_output: Final response: {response['message']['content']}")
    return json.dumps({"content_type": "llm_response", "llm_response": response['message']['content'], "referenced_documents": rds, 'referenced_titles': rts})



def get_llm_output_stream_without_RAG(parameters):
    """
    This function accepts a user query and uses it to query the Chroma database
    for any relevant information. However, this information is NOT provided as context
    to the LLM model. Instead, it simply uses the user query to generate a response
    from the LLM model without any additional context.
    
    THIS FUNCTION IS INTENDED FOR TESTING PURPOSES ONLY AND SHOULD NOT BE USED IN PRODUCTION.
    
    Args:
        user_query (str): The user's question to be processed by the LLM.
        llm_model (str): The name of the LLM model to use. Defaults to DEFAULT_LLM.
        
    Returns:
        str: A JSON string with the LLM's response and a list of the documents most relevant to the user's query.
    """
    
    # Parse the parameters from the request
    user_query = parameters['user_query'].strip()  # Get the user query from the parameters and strip any leading/trailing whitespace
    if not user_query:
        return {"error": "User query cannot be empty"}, 400
    
    #chat_history = parameters['chat_history']  # Assuming chat_history is a list of previous messages
    
    llm_model = parameters['llm_model']  # if 'llm_model' in parameters else DEFAULT_LLM  # Use the specified LLM model or default to DEFAULT_LLM if not provided

    chat_history_raw = parameters['chat_history']  # Assuming chat_history is a list of previous messages each stored as a dictionary with "question" and "answer" keys
    # IMPORTANT: In order for the LLM to be able to use the chat history,
    # it must be a list of dictionaries that contains the "role" and "content" keys for both
    # user and assistant messages. If the chat history is not in this format, it will not work correctly.
    chat_history = []
    for msg in chat_history_raw:
        chat_history.append({"role": "user", "content": msg["question"]})
        chat_history.append({"role": "assistant", "content": msg["answer"]})

    #stream = parameters['stream']  # if 'stream' in parameters else False  # Whether to stream the response from the LLM, default is False

    # globals.llm_logger.info("get_llm_output: Retrieving relevant chunks for the user query. Calling retrieve_relevant_chunks()")
    context_chunks = retrieve_relevant_chunks(user_query, top_n=3)

    # context_chunks will be a list of tuples (text, metadata) where
    # text is the text chunk and metadata is a dictionary containing
    # the filename and other relevant information.
    # For example, context_chunks = [(text_chunk_1, {'source_file': 'file1.txt'}), (text_chunk_2, {'source_file': 'file2.txt'})]

    # Save the file name for each point in a set to use to generate our references
    referenced_documents = set()

    # Iterate through the retrieved context chunks and store the text and metadata
    # in a list of tuples (text, file_name).
    for _, metadata in context_chunks:
        # Store the text and file name in the list of context chunks
        # The metadata is a dictionary containing the document ID and other relevant information.
        referenced_documents.add(metadata['source_file'])
        #context_chunks.append((text, metadata['source_file']))


    # AgWater specific instruction prompt for the chatbot. Still needs further work
    # to ensure that the chatbot only answers questions related to agriculture and water management.
    instruction_prompt = f'''You are a helpful chatbot. Answer the user's question as best as you can.'''
    #llm_logger.info(f"after setting instruction prompt - user_query={user_query}, llm_model={llm_model}, stream={stream}")

    ollama_messages = chat_history + [
        {'role': 'system', 'content': instruction_prompt},
        {'role': 'user', 'content': user_query},
    ]

    # Use the Ollama API to chat with the chatbot
    response = ollama.chat(
        model=llm_model,  # Use the specified LLM model
        # messages=chat_history + [
        #     {'role': 'system', 'content': instruction_prompt},
        #     {'role': 'user', 'content': user_query},
        # ],
        messages=ollama_messages,
        stream=True,  # Set to True for streaming response
    )

    #
    rds=list(referenced_documents)
    rts, _ = get_titles_from_filenames(rds)  # Get the titles for the referenced documents

    # If the response is being streamed, we need to handle the ChatResponse Generator object
    # and return the responses as they are generated.
    yield json.dumps({"content_type": "document_info", "referenced_documents": rds, "referenced_titles": rts}) + "\n"  # Indicate that the streaming is done

    for chunk in response:
        # globals.llm_logger.info(f" - get_llm_output: Streaming response chunk: {chunk['message']['content']}")
        # This implementation does retrieve each chunk of the response as it is generated,
        # Return the chunk as a JSON string with the chat response and referenced documents
        yield json.dumps({"content_type": "llm_response", "llm_response": chunk['message']['content']}) + "\n"
        #yield chunk['message']['content']

# This function retrieves the list of LLM models available in Ollama.
def get_llm_models():
    """
    This helper function retrieves the list of LLM models available in Ollama.
    
    Returns:
        models (list[dict]): A list of models available in Ollama, including
                                their names and their parameter sizes.
    """
    ollama_models = ollama.list()['models']
    model_list = []
    for model in ollama_models:
        model_list.append(
            # {
            #     "name": model['model'],
            #     "parameter_size": model['details']['parameter_size']
            # }
            model['model'].split(':')[0]  # Extract the model name before any version tag
        )

    #return ['ollama']
    return model_list


# DEBUGGING: This function is used to test the LLM service by sending a test query to the LLM model
# and returning the response. It is currently commented out to avoid cluttering the API with unused endpoints.
# Uncomment it if you want to test the LLM service directly.

def test_llm(parameters):
    """
    This function tests the LLM service by sending a test query to the LLM model
    and returning the response. 
    
    Returns:
        str: A string containing the response from the LLM model.
    """
    globals.llm_logger.info(f" - test_llm: Querying the LLM model with the following parameters: {parameters}")

    query_string = parameters['user_query'].strip()  # Get the test query string from the parameters
    if not query_string:
        return {"error": "Query string cannot be empty"}, 400
    
    # Parse the provided chat history if it exists and convert it to a list of dictionaries
    # with "role" and "content" keys:

    chat_history_raw = parameters['chat_history']
    chat_history = []

    for msg in chat_history_raw:
        chat_history.append({"role": "user", "content": msg["question"]})
        chat_history.append({"role": "assistant", "content": msg["answer"]})

    globals.llm_logger.info(f" - test_llm: Chat history: {chat_history}")

    globals.llm_logger.info(f" - test_llm: Query string: {query_string}")

    try:
        response = ollama.chat(
            model=DEFAULT_LLM,  # Use the default LLM model
            messages=chat_history + [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': query_string},
            ],
            stream=False,  # Set to True for streaming response
        )
        #globals.llm_logger.info(f" - test_llm: Received response from LLM model: {response}")
        return json.dumps({"llm_response": response['message']['content'], "references": ["These", "are", "test", "documents"]})
        #return response['message']['content']
    
    except Exception as e:
        globals.llm_logger.error(f" - test_llm: Error querying the LLM model: {e}")
        return json.dumps({"error": str(e)}), 500
        #return {"error": str(e)}, 500
    
    # If the response is being streamed, we need to handle the ChatResponse Generator object
    # if stream:
    #     for chunk in response:
    #         #globals.llm_logger.info(f" - test_llm: Streaming response chunk: {chunk['message']['content']}")
    #         yield chunk['message']['content']
    #         #yield json.dumps({"llm_response": chunk['message']['content'], "referenced_documents": ["document 1", "document 2", "document 3"]})
    # else:
    #     #return json.dumps({"llm_response": response['message']['content'], "referenced_documents": ["document 1", "document 2", "document 3"]})
    #     yield "done"


def test_llm_streaming(parameters):
    """
    This function tests the LLM service by sending a test query to the LLM model
    and returning the response in a streaming manner.

    Args:
        parameters (dict): A dictionary containing the parameters for the LLM query.
                           It should contain 'user_query' as a key.

    Yields:
        str: A string containing the response from the LLM model, chunk by chunk.
    """
    globals.llm_logger.info(f" - test_llm_streaming: Querying the LLM model with the following parameters: {parameters}")

    query_string = parameters['user_query'].strip()  # Get the test query string from the parameters
    if not query_string:
        yield json.dumps({"error": "Query string cannot be empty"}), 400


    # Parse the provided chat history if it exists and convert it to a list of dictionaries
    # with "role" and "content" keys:

    chat_history_raw = parameters['chat_history']
    chat_history = []

    for msg in chat_history_raw:
        chat_history.append({"role": "user", "content": msg["question"]})
        chat_history.append({"role": "assistant", "content": msg["answer"]})


    globals.llm_logger.info(f" - test_llm_streaming: Query string: {query_string}")

    try:
        response = ollama.chat(
            model=DEFAULT_LLM,  # Use the default LLM model
            messages=chat_history + [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': query_string},
            ],
            stream=True,  # Set to True for streaming response
        )

        # If the response is being streamed, we need to handle the ChatResponse Generator object
        for chunk in response:
            globals.llm_logger.info(f" - test_llm_streaming: Streaming response chunk: {chunk['message']['content']}")
            yield json.dumps({"llm_response": chunk['message']['content'], "done": chunk['done']}) + "\n"
            #yield chunk['message']['content']  # Yield each chunk of the response as it is generated

        yield json.dumps({"done": True, "references": ["These", "are", "other", "referenced", "documents"]}) + "\n"  # Indicate that the streaming is done
        #yield ["document1", "document2"]  # Example of referenced documents, can be replaced with actual references
            
    except Exception as e:
        globals.llm_logger.error(f" - test_llm_streaming: Error querying the LLM model: {e}")
        yield json.dumps({"error": str(e)}) + "\n"
        #yield {"error": str(e)}, 500



# def generator_test(limit):
#     # Simulate a generator function that yields chunks of data
#     yield f"Starting generator with limit: {limit}\n"

#     # Simulate generating 10 chunks of data
#     for i in range(limit):  # Generate 10 chunks
#         yield f"Chunk {i + 1}\n"

#     yield "Generator completed.\n"


def put_llm_source(title, file, tags):
    """
    Inserts a new LLM source record into the AgWater SQLite database.

    Args:
        title (str): The title of the source.
        file (File): The source filenames (e.g., URL or file path).
        tags (list): A list of tags associated with the source.

    Returns:
        dict: Result of the operation.
    """
    UPLOAD_FOLDER='D:\\AgWaterLLM\\uploads'

    if file.content_type != 'application/pdf':
        return json.dumps({"success": False, "message": "Only PDF files are allowed"}), 400

    # Save the PDF file
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        # Create table if it doesn't exist
        c.execute("""
            CREATE TABLE IF NOT EXISTS LLM_Sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                tags TEXT
            )
        """)
        # Insert the record
        c.execute("""
            INSERT INTO LLM_Sources (title, filename, tags)
            VALUES (?, ?, ?)
        """, (title, filename, ','.join(tags)))
        conn.commit()
        file.save(filepath)
        globals.llm_logger.info(f"Successful LLM Source Submission: Title: {title}, Tags: {tags}, File: {filename}")

    except sqlite3.Error as e:
        globals.llm_logger.error(f"DB Error inserting LLM source: {e}")
        return json.dumps({"success": False, "message": str(e)}), 500
    
    except Exception as e:
        globals.llm_logger.error(f"Error inserting LLM source: {e}")
        return json.dumps({"success": False, "message": str(e)}), 500
    
    finally:
        conn.close()
        
    return json.dumps({'success': True, 'message': 'Sourse submission successful'}), 200


def get_titles_from_filenames(filenames):
    """
    Query the LLM_Source table for a given filename and return the corresponding title.

    Args:
        filename (str): The filename string to search for.

    Returns:
        str or None: The title if found, otherwise None.
    """
    conn = sqlite3.connect(DB_PATH)
    titles = []
    try:
        for filename in filenames:
            c = conn.cursor()
            c.execute("SELECT title FROM 'LLM_Sources' WHERE filename = ?", (filename,))
            row = c.fetchone()
            if row is not None and row[0] is not None:
                titles.append(row[0])
            else:
                titles.append(None)  # Append None if title not found for this filename
                
    except sqlite3.Error as e:
        return None, str(e)

    except Exception as e:
        return None, str(e)

    finally:
        conn.close()

    return titles, "success"



def put_llm_rating(question, answer, rating, model, comment, submitted_by):
    """
    Inserts a new LLM rating record into the AgWater SQLite database or replaces an existing one.
    Uses SQL "INSERT OR REPLACE" to handle both insert and update operations.

    Args:
        question (str): The question asked by the user.
        answer (str): The answer provided by the LLM.
        rating (int): The rating given by the user (1-5).
        context (str): The context for the rating.
        comment (str): Optional comment from the user.

    Returns:
        dict: Result of the operation.
    """
    globals.llm_logger.info(f"put_llm_rating called: {question}, {rating}, {model}, {comment}, {submitted_by}")
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        # Create table if it doesn't exist with unique constraint
        c.execute("""
            CREATE TABLE IF NOT EXISTS LLM_Ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                rating INTEGER NOT NULL,
                model TEXT NOT NULL,
                comment TEXT,
                submitted_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(question, answer, model)
            )
        """)
        
        # Use INSERT OR REPLACE to handle both insert and update
        c.execute("INSERT OR REPLACE INTO LLM_Ratings (question, answer, rating, model, comment, submitted_by, updated_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                  (question, answer, rating, model, comment, submitted_by))

        conn.commit()
        globals.llm_logger.info("put_llm_rating successful")

    except sqlite3.Error as e:
        globals.llm_logger.error(f"DB Error inserting/replacing LLM rating: {e}")
        conn.rollback()
        return {"success": False, "message": str(e)}, 500
    
    except Exception as e:
        globals.llm_logger.error(f"Error inserting/replacing LLM rating: {e}")
        conn.rollback()
        return {"success": False, "message": str(e)}, 500
        
    finally:
        conn.close()
           
    return {"success": True, "message": "LLM rating saved successfully"}


def get_llm_sources():
    """
    Retrieves all LLM sources from the AgWater SQLite database.
    Returns:
        list[dict]: A list of dictionaries, each containing 'title', 'filename', and 'tags' for each source.
    """
    globals.llm_logger.info("get_llm_sources called")
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    sources = []
    try:
        c = conn.cursor()
        c.execute("SELECT title, filename, tags FROM LLM_Sources")
        rows = c.fetchall()
        for row in rows:
            sources.append({
                "title": row[0],
                "filename": row[1],
                "tags": row[2].split(',') if row[2] else []
            })
    except sqlite3.Error as e:
        return {"error": str(e)}, 500
    finally:
        conn.close()
    return sources