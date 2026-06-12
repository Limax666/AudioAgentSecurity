# add parent directory to sys.path
import sys
sys.path.append('.')
import logging
import torch


# =  =  =  =  =  =  =  =  =  =  =  Logging Setup  =  =  =  =  =  =  =  =  =  =  =  =  =
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)

# =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =
class Model(object):

    def __init__(self, model_name_or_path):

        self.dataset_name = None
        self.model_name   = model_name_or_path
        self.device       = "cuda" if torch.cuda.is_available() else "cpu"

        self.load_model()
        logger.info("Loaded model: {}".format(self.model_name))
        logger.info("= = "*20)


    def load_model(self):
        from .model_src.universal_model import universal_model_loader
        universal_model_loader(self)


    def generate(self, input):

        with torch.no_grad():
            from .model_src.universal_model import universal_model_generation
            return universal_model_generation(self, input)