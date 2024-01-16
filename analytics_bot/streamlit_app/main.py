from langchain_experimental.tools.python.tool import PythonAstREPLTool
from helper_functions import get_credentials
from helper_functions.tools.run_sql import run_sql
from helper_functions import config
from helper_functions.extract_intermediate_data import get_intermediate_json
from langchain.chat_models import ChatOpenAI
from typing import Optional, Type, Dict
from langchain.schema.messages import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import AIMessage, HumanMessage
from langchain.agents.initialize import initialize_agent
from langchain.agents.agent_types import AgentType
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.prompts import HumanMessagePromptTemplate
from helper_functions.DBconnector import DBConnector


class AnalysisAgent:
    def __init__(self):

        self.db_connector = DBConnector()
        self.api_key = self.db_connector.get_credentials_object.get_api_key()
        with open(r"./hierarchy.txt", "r") as f:
            self.hierarchy = f.read()

        # set up llm
        self.llm = ChatOpenAI(
            temperature=0,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
            openai_api_key=self.api_key,
            model="gpt-4-1106-preview",
            seed=123,  # set seed for reproducibility,
            request_timeout=900,
        )
        self.tool_kit = [
            run_sql(),
            PythonAstREPLTool(),
        ]

        self.agent = initialize_agent(
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            llm=self.llm,
            tools=self.tool_kit,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )
        self.chat_history = []
        self.all_observations = []
        self.Initial_chat_template = self.get_initial_prompt()

    def get_initial_prompt(self):
        with open(config.content_prompt_directory, "r", encoding="utf-8") as f:
            content_prompt_raw = f.read()
            content_prompt = content_prompt_raw.format(hierarchy=self.hierarchy)
            Initial_chat_template = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(content=content_prompt),
                    MessagesPlaceholder(variable_name="observation_memory"),
                    MessagesPlaceholder(variable_name="memory"),
                    HumanMessagePromptTemplate.from_template("{input}"),
                    # chat history
                ]
            )
            return Initial_chat_template

    def process_message(self, user_message):
        result = self.agent(
            self.Initial_chat_template.format_messages(
                input=user_message,
                memory=self.chat_history,
                observation_memory=self.all_observations,
            )
        )

        self.chat_history.extend(
            [
                HumanMessage(content=user_message),
                AIMessage(content=result["output"]),
            ]
        )
        try:
            downloaded_data = result["intermediate_steps"][0][1].get("data")
            tool_output = result["intermediate_steps"][0][1]
            observation_memory = get_intermediate_json(
                tool_output, keys=["data_directry", "columns"]
            )
            self.all_observations.append(
                AIMessage(content=f"Outputs: {observation_memory}")
            )
        except Exception:
            # i.e if no tool was called we simply move on. idealy we should log this with the full intermediate_steps
            # to be ceratin we are not parsing it incorrectly...
            pass

        all_prompt = result["input"][0].content
        return result["output"]
