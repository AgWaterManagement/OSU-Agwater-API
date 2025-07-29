import logging

# Global logger variables
main_logger = None
llm_logger = None
agrimet_logger = None
articles_logger = None

def init():
    global main_logger, llm_logger, agrimet_logger, articles_logger
    
    # Set up main logging
    logging.basicConfig(
        filename='./logfiles/app.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main_logger = logging.getLogger(__name__)

    # Set up LLM-specific logging
    llm_logger = logging.getLogger('llm')
    llm_handler = logging.FileHandler('./logfiles/llm.log')
    llm_handler.setLevel(logging.INFO)
    llm_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    llm_handler.setFormatter(llm_formatter)
    llm_logger.addHandler(llm_handler)
    llm_logger.setLevel(logging.INFO)
    
    # Set up Agrimet-specific logging
    agrimet_logger = logging.getLogger('agrimet')
    agrimet_handler = logging.FileHandler('./logfiles/agrimet.log')
    agrimet_handler.setLevel(logging.INFO)
    agrimet_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    agrimet_handler.setFormatter(agrimet_formatter)
    agrimet_logger.addHandler(agrimet_handler)
    agrimet_logger.setLevel(logging.INFO)

    # Set up Articles-specific logging
    articles_logger = logging.getLogger('articles')
    articles_handler = logging.FileHandler('./logfiles/articles.log')
    articles_handler.setLevel(logging.INFO)
    articles_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    articles_handler.setFormatter(articles_formatter)
    articles_logger.addHandler(articles_handler)
    articles_logger.setLevel(logging.INFO)


    # Example: Initialize a global variable

    #globals.some_global_variable = "Initialized"
    # Add any other initialization logic here
    #print("Globals initialized.")