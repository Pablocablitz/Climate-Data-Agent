from chatbot import Chatbot
import yaml

class EOChatbotTester():
    def __init__(self):
        self.chatbot = chatbot
        self.tests = self.__load_tests()

    def __load_tests(self):
        # Is this correct??
        return yaml.load_all("tests.yaml")

    def run_tests(self):
        pass