import logging

def get_logger(level):
    logger = logging.getLogger(__name__)

    ch = logging.StreamHandler()
    ch.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    logger.setLevel(level)

    return logger