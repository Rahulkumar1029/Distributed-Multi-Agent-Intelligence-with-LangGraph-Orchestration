import asyncio
import sys
from dotenv import load_dotenv
from loguru import logger

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams

from pipecat.services.whisper.stt import WhisperSTTService, Model
from pipecat.services.piper.tts import PiperTTSService
from pipecat.transcriptions.language import Language

from pipecat.audio.vad.silero import SileroVADAnalyzer

from pipecat.processors.frame_processor import FrameProcessor
from pipecat.frames.frames import TranscriptionFrame, LLMTextFrame

from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)

from pipecat.transports.local.audio import (
    LocalAudioTransport,
    LocalAudioTransportParams
)

from langchain_community.tools import DuckDuckGoSearchResults
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.groq import GroqSTTService
from bot1_LG_MCP.resources.llms import llm
import os

load_dotenv()

logger.remove()
logger.add(sys.stderr, level="INFO")


class ConsoleLogger(FrameProcessor):

    async def process_frame(self, frame, direction):

        if isinstance(frame, TranscriptionFrame):
            print(f"\nYou: {frame.text}")

        if isinstance(frame, LLMTextFrame):
            print(f"Bot: {frame.text}")

        await self.push_frame(frame, direction)


stt = GroqSTTService(
    api_key=os.getenv("GROQ_API_KEY"),
    model="whisper-large-v3-turbo"
)

tts = PiperTTSService(
    voice_id="en_US-ryan-high",
    sample_rate=48000,
)


search_engine = DuckDuckGoSearchResults()

async def search_tool(params: FunctionCallParams, query: str) -> str:
    return search_engine.run(query)


tools = ToolsSchema(standard_tools=[search_tool])


transport = LocalAudioTransport(
    params=LocalAudioTransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True
    )
)


console = ConsoleLogger()


async def build_pipeline():

    messages = [
        {
            "role": "system",
            "content": "You are a helpful voice AI assistant. Use tools if needed."
        }
    ]

    context = LLMContext(messages, tools)

    user_agg, assistant_agg = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer()
        ),
    )

    pipeline = Pipeline([
        transport.input(),
        stt,
        console,
        user_agg,
        llm,
        console,
        tts,
        transport.output(),
    ])

    return pipeline


async def main():

    pipeline = await build_pipeline()

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    runner = PipelineRunner()

    await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())