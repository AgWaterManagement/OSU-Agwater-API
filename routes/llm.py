import os
import json
import logging
import globals
from flask import Blueprint, request, Response, jsonify, send_file, stream_with_context
from services.llm_service import get_llm_output, get_llm_output_stream, get_llm_output_without_RAG, get_llm_output_stream_without_RAG 
from services.llm_service import get_llm_models, put_llm_source, get_titles_from_filenames, DEFAULT_LLM
from services.llm_service import get_llm_sources, test_llm, test_llm_streaming, put_llm_rating 

bp = Blueprint('llm', __name__)
#        user_query (str): The user's question to be processed by the LLM.
#        llm_model (str): The name of the LLM model to use. Defaults to DEFAULT_LLM.
#        stream (bool): Whether to stream the response from the LLM. Defaults to False.


@bp.route("/llm/test", methods=["POST"])
def llm_test_route():
    """
    Route to test the LLM service.
    """

    globals.llm_logger.info("llm_test_route called")
    # Gather the user's query and other parameters from the request
    query = request.args.get('query', 'What is the capital of France?')
    model = request.args.get('model', DEFAULT_LLM)
    stream = request.args.get('stream', '0')

    # Retrieve the chat history from the request body.
    # The chat history is expected to be a JSON string that can be parsed into a list
    history = request.get_json().get('chat_history', [])

    globals.llm_logger.info(f"llm_test_route: query: {query}, model: {model}, stream: {stream}, history: {history}")

    if stream == '1':
        stream = True
    else:
        stream = False

    if not query:
        return {"error": "Prompt cannot be empty"}, 400
    
    if stream:
        # If streaming is enabled, we need to return a streaming response
        response = test_llm_streaming({
            'user_query': query,
            'llm_model': model,
            #'chat_history': json.loads(chat_history),
            'chat_history': history,
        })
        return Response(response, mimetype='application/json')
        #return Response(stream_with_context(response), mimetype='text/plain')
    else:
        response = test_llm({
            'user_query': query,
            'llm_model': model,
            #'chat_history': json.loads(chat_history),
            'chat_history': history,
        })

        return Response(response, mimetype='application/json')
        #return Response(jsonify(response), mimetype='application/json')


@bp.route("/llm/chat", methods=["POST"])
def llm_chat_route():
    globals.llm_logger.info("llm_chat_route called")
    # Gather the user's query and other parameters from the request
    #query = request.args.get('query', '')
    query = request.get_json().get('query', '')

    # If the user doesn't provide an LLM model to use, default to the one specified in DEFAULT_LLM
    #model = request.args.get('model', DEFAULT_LLM)
    model = request.get_json().get('model', DEFAULT_LLM)

    # Check if the user wants to stream the response
    #stream = request.args.get('stream', '1')
    stream = request.get_json().get('stream', True)
    # if stream == 1:
    #     stream = True
    # else:
    #     stream = False

    # Chat history can be passed as a JSON string in the request body. If no chat history is provided, we default to an empty list.
    # This allows the LLM to maintain context across the entire conversation.
    # More than that, the chat history can easily be saved by the user and reused later to continue the conversation.
    
    # The chat history is expected to be a JSON string that can be parsed into a list
    # Example: [{"question": "What is drip irrigation?", "answer": "Drip irrigation is a method of irrigation..."}]
    # If no chat history is provided, we default to an empty list.
    #chat_history = request.args.get('chat_history', '[]')

    # IMPORTANT: Since the chat history can be quite large, we don't want to pass it as a query parameter.
    # Instead, we expect it to be passed as a JSON string in the request body.
    # This allows us to handle larger chat histories without running into URL length limitations.
    # If the chat history is not provided, we default to an empty list
    history = request.get_json().get('chat_history', [])


    # Check if the user wants to use the RAG (Retrieval-Augmented Generation) feature.
    # If the user doesn't provide a value for RAG, we default to True.
    # This means that the LLM will use the context from the ChromaDB vector database
    # to generate a more informed response.
    use_RAG = request.get_json().get('use_RAG', True)

    # Print the chat history for debugging purposes
    globals.llm_logger.info(f"llm_chat_route: query: {query}, model: {model}, chat_history: {history}, stream: {stream}")

    if not query:
        return {"error": "Prompt cannot be empty"}, 400
    
    # Collect the parameters from the request and combine them into a JSON string to then pass to the LLM service
    #parameters = json.dumps({"user_query": query, "llm_model": model, "stream": stream})

    # Pass the parameters to the LLM service to get the output
    # Assuming parameters is a JSON string, we can parse it directly


    if stream:
        globals.llm_logger.info("Streaming response enabled")
        # If streaming is enabled, we need to return a streaming response
        if use_RAG:
            # If RAG is enabled, we use the get_llm_output_stream function
            globals.llm_logger.info("RAG enabled, using get_llm_output_stream")
            return Response(stream_with_context(get_llm_output_stream({
                'user_query': query,
                'llm_model': model,
                'chat_history': history,
            })), mimetype='application/json')
        else:
            # If RAG is not enabled, we use the get_llm_output_stream_without_RAG function
            globals.llm_logger.info("RAG disabled, using get_llm_output_stream_without_RAG")
            return Response(stream_with_context(get_llm_output_stream_without_RAG({
                'user_query': query,
                'llm_model': model,
                'chat_history': history,
            })), mimetype='application/json') #, content_type='application/json')


    # If streaming is not enabled, we can return a regular response
    else:
        globals.llm_logger.info("Streaming response disabled")
        try:
            if use_RAG:
                # If RAG is enabled, we use the get_llm_output function
                globals.llm_logger.info("RAG enabled, using get_llm_output")
                response = get_llm_output({
                    'user_query': query,
                    'llm_model': model,
                    'chat_history': history,
                })
            else:
                # If RAG is not enabled, we use the get_llm_output_without_RAG function
                globals.llm_logger.info("RAG disabled, using get_llm_output_without_RAG")
                response = get_llm_output_without_RAG({
                    'user_query': query,
                    'llm_model': model,
                    'chat_history': history,
                })

            #json_response = json.loads(response)

            #return {"success": "Success", "response": json_response}, 200
            return Response(response, mimetype='application/json') #, content_type='application/json')

        except Exception as ollama_error:
            return {"error": f"Ollama Error: {str(ollama_error)}"}, 500


@bp.route("/llm/models")
def llm_models_route():
    models = get_llm_models()
    return {"success": True, "models": models}, 200


@bp.route("/llm/submit_source", methods=["POST"])
def llm_submit_source_route():

    """
    Route to submit a new LLM source to the database.
    Expects JSON body with 'title', 'source_locators', and 'tags' (list).
    """
    # Get the title
    title = request.form.get('title')
    if not title:
        return jsonify({'error': 'Missing title'}), 400

    # Get the tags (they come as a JSON string)
    tags_json = request.form.get('tags')
    if not tags_json:
        return jsonify({'error': 'Missing tags'}), 400

    try:
        tags = json.loads(tags_json)
    except Exception as e:
        return jsonify({'error': 'Invalid tags JSON'}), 400

    # Get the file
    file = request.files.get('pdf')
    if not file:
        return jsonify({'error': 'Missing PDF file'}), 400

    return put_llm_source(title, file, tags)


@bp.route("/llm/titles_from_filenames", methods=["GET"])
def llm_titles_from_filenames_route():
    """
    Route to get the title of a source by its locator (filename).
    Expects 'filename' as a query parameter.
    """
    files = []
    filenames = request.args.get('filenames')
    
    if filenames:
        files = filenames.split(',')

    if not filenames:
        return jsonify({'error': 'Missing filename'}), 400

    titles, msg = get_titles_from_filenames(files)

    if titles is None:
        return jsonify({'success': False, 'message': msg}), 500
    
    return jsonify({'success': True,'titles': titles}), 200


@bp.route("/llm/sources", methods=["GET"])
def get_llm_sources_route():
    """
    Route to get all LLM sources.
    """
    result = get_llm_sources()
    return jsonify({"success": True, "sources": result}), 200


@bp.route("/llm/source", methods=["GET"])
def llm_get_source_route():
    """
    Service to return a PDF file by filename as 'application/pdf'.

    Args:
        pdf_filename (str): The name of the PDF file to return.

    Returns:
        Flask response: The PDF file with correct MIME type, or error if not found.
    """
    filename = request.args.get('filename')

    globals.llm_logger.info(f"llm_get_source_route: filename: {filename}")

    # Adjust the path as needed to your PDF storage directory
    pdf_dir = "D:\\AgWaterLLM\\source_materials"
    pdf_path = os.path.join(pdf_dir, filename)

    if not os.path.isfile(pdf_path):
        return {"error": f"File {pdf_path} not found."}, 404

    globals.llm_logger.info(f"llm_get_source_route: Returning PDF file: {pdf_path}")

    # Use Flask's send_file to return the PDF file with the correct MIME type
    # This will also handle setting the correct headers for downloading the file
    # and ensure that the file is served as a binary stream.
    # The mimetype 'application/pdf' is set to indicate that the file is a PDF.
    return send_file(pdf_path, mimetype='application/pdf')


@bp.route("/llm/rating", methods=["POST"])
def llm_put_rating_route():
    """
    Service to return a add a rating to a answer to a prompt
     
    """
    globals.llm_logger.info("llm_put_rating_route called")
    body = request.get_json()
    if not body:
        return {"error": "Request body is required."}, 400

    # Extract parameters from the request body
    # If any of these are missing, we return an error
    # question, answer, rating, and context are all required
    if not isinstance(body, dict):
        return {"error": "Request body must be a JSON object."}, 400

    # Extract parameters from the request body
    # If any of these are missing, we return an error
    if not all(key in body for key in ['question', 'answer', 'rating', 'model', 'comment', 'submitted_by']):
        return {"error": "Missing required parameters."}, 400

    question = body['question']
    answer = body['answer']
    rating = body['rating']
    model = body['model']
    comment = body['comment']
    submitted_by = body['submitted_by']

    # add the rating to a database or some storage
    result = put_llm_rating(question, answer, rating, model, comment, submitted_by)  # returns {"success": True, "message": "LLM rating saved successfully"}
    globals.llm_logger.info(json.dumps(result))
   
    return jsonify(result), 200
