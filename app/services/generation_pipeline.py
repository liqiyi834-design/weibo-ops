from pathlib import Path

from app.core.config import Settings
from app.llm.client import BaseLLMClient
from app.rag.embeddings import build_embedding_client
from app.rag.knowledge import KnowledgeLoader
from app.rag.retriever import KeywordRetriever
from app.rag.vector_store import LocalVectorStore, VectorRetriever
from app.schemas.comment import GenerateCommentRequest, GenerateCommentResponse
from app.services.fact_summarizer import FactSummarizer
from app.services.opinion_generator import OpinionGenerator
from app.services.persona_rewriter import PersonaRewriter
from app.services.prompt_loader import PromptLoader
from app.services.safety_checker import SafetyChecker
from app.services.style_service import StyleService
from app.services.topic_classifier import TopicClassifier


class GenerationPipeline:
    def __init__(self, settings: Settings, llm: BaseLLMClient):
        prompts = PromptLoader()
        loader = build_knowledge_loader(Path(settings.knowledge_dir))
        self.keyword_retriever = KeywordRetriever(loader)
        self.vector_store = LocalVectorStore(Path(settings.rag_index_path))
        self.vector_retriever = VectorRetriever(self.vector_store, build_embedding_client(settings))
        self.fact_summarizer = FactSummarizer(llm, prompts)
        self.topic_classifier = TopicClassifier()
        self.opinion_generator = OpinionGenerator(llm, prompts)
        self.persona_rewriter = PersonaRewriter(llm, prompts)
        self.safety_checker = SafetyChecker()
        self.style_service = StyleService()

    def generate(self, request: GenerateCommentRequest) -> GenerateCommentResponse:
        fact_summary = self.fact_summarizer.summarize(request.topic, request.context_text)
        classification = self.topic_classifier.classify(request.topic, request.context_text, fact_summary)
        requested_style = request.style or request.persona
        style, style_notes = self.style_service.resolve_style(
            account_id=request.account_id,
            requested_style=requested_style,
            classification=classification,
        )
        classification.risk_notes.extend(style_notes)
        retrieve_query = f"{request.topic} {request.context_text} {request.account_id} {style} 风格记忆库 写法 节奏"
        retrieved = self._retrieve(retrieve_query) if request.use_rag else []
        opinion = self.opinion_generator.generate(fact_summary, retrieved, classification)
        output = self.persona_rewriter.rewrite(
            fact_summary=fact_summary,
            opinion=opinion,
            classification=classification,
            persona=style,
            emotion_level=request.emotion_level,
        )
        safety = self.safety_checker.check(output, fact_summary, classification)
        final_output = safety.revised_output or output
        return GenerateCommentResponse(
            topic=request.topic,
            account_id=request.account_id,
            style=style,
            fact_summary=fact_summary,
            topic_classification=classification,
            retrieved_knowledge=retrieved,
            opinion=opinion,
            output=final_output,
            safety=safety,
        )

    def _retrieve(self, query: str):
        vector_results = self.vector_retriever.retrieve(query)
        if vector_results:
            return vector_results
        return self.keyword_retriever.retrieve(query)


def build_knowledge_loader(knowledge_dir: Path) -> KnowledgeLoader:
    extra_files = [
        Path("04_人设与风格规则.md"),
        Path("06_草稿生成提示词.md"),
        Path("08_高热博文公开样本研究.md"),
        Path("10_爆款博文写作公式.md"),
        Path("12_事实核查与风险分级.md"),
        Path("24_高互动正文分析标准.md"),
    ]
    return KnowledgeLoader(knowledge_dir, extra_files=extra_files)
