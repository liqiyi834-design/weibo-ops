from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import httpx
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import get_settings
from app.schemas.comment import HotTopic
from app.schemas.comment import KnowledgeIngestRequest
from app.services.candidate_pool_service import CandidatePoolService
from app.services.draft_service import DraftService
from app.services.generation_pipeline import GenerationPipeline
from app.services.hot_search_service import HotSearchService
from app.services.knowledge_ingestion_service import KnowledgeIngestionService
from app.services.style_service import StyleService
from app.services.topic_research_service import TopicResearchService
from app.services.topic_selection_service import TopicSelectionService
from app.llm.client import build_llm_client
from app.schemas.comment import GenerateCommentRequest
from app.schemas.comment import GenerateZhihuAnswerRequest


DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "")
STATUS_OPTIONS = ["candidate", "selected", "skipped", "researched"]
DRAFT_STATUS_OPTIONS = ["draft", "reviewed", "rejected", "published_manually"]


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=120.0) as client:
            response = client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def health(self) -> dict:
        return self.request("GET", "/health")

    def create_candidate_pool(self, payload: dict) -> dict:
        return self.request("POST", "/api/topic-candidates/pools", json=payload)

    def list_candidate_pools(self) -> list[dict]:
        return self.request("GET", "/api/topic-candidates/pools")

    def get_candidate_pool(self, pool_id: str) -> dict:
        return self.request("GET", f"/api/topic-candidates/pools/{pool_id}")

    def update_candidate_item(self, pool_id: str, item_id: str, status: str, note: str) -> dict:
        return self.request(
            "PATCH",
            f"/api/topic-candidates/pools/{pool_id}/items/{item_id}",
            json={"status": status, "operator_note": note or None},
        )

    def list_accounts(self) -> list[dict]:
        return self.request("GET", "/api/accounts")["accounts"]

    def list_styles(self) -> list[dict]:
        return self.request("GET", "/api/comment/styles")["styles"]

    def create_draft(self, payload: dict) -> dict:
        return self.request("POST", "/api/drafts", json=payload)

    def create_zhihu_draft(self, payload: dict) -> dict:
        return self.request("POST", "/api/drafts/zhihu", json=payload)

    def list_drafts(self) -> list[dict]:
        return self.request("GET", "/api/drafts")

    def get_draft(self, draft_id: str) -> dict:
        return self.request("GET", f"/api/drafts/{draft_id}")

    def update_draft(self, draft_id: str, payload: dict) -> dict:
        return self.request("PATCH", f"/api/drafts/{draft_id}", json=payload)

    def ingest_knowledge(self, payload: dict) -> dict:
        return self.request("POST", "/api/knowledge/ingest", json=payload)


class LocalServiceClient:
    def __init__(self):
        self.settings = get_settings()
        self.candidate_pool_service = CandidatePoolService()
        self.draft_service = DraftService()
        self.style_service = StyleService()

    def health(self) -> dict:
        return {"status": "ok", "mode": "local_services"}

    def create_candidate_pool(self, payload: dict) -> dict:
        hot_response = HotSearchService(self.settings).get_weibo_hot_topics(
            limit=payload.get("source_limit", 50)
        )
        topics = [
            HotTopic(
                rank=item.rank,
                keyword=item.keyword,
                hot_value=item.hot_value,
                url=item.url,
                label=item.label,
                source=item.source,
                timestamp=item.timestamp,
            )
            for item in hot_response.items
        ]

        if payload.get("enrich_metrics", False):
            research_service = TopicResearchService(self.settings)
            research_limit = payload.get("research_limit", 10)
            for index, topic in enumerate(topics):
                if index >= research_limit:
                    break
                metrics = research_service.research(topic.keyword)
                topic.read_count = metrics.read_count
                topic.discussion_count = metrics.discussion_count
                topic.sampled_posts_count = metrics.sampled_posts_count
                topic.controversy_score = metrics.controversy_score

        selection = TopicSelectionService().select(
            topics,
            max_results=payload.get("max_results", 10),
        )
        pool = self.candidate_pool_service.save(
            selected=selection.selected,
            source=selection.source,
            title=payload.get("title"),
            notes=selection.notes,
        )
        return pool.model_dump(mode="json")

    def list_candidate_pools(self) -> list[dict]:
        return [pool.model_dump(mode="json") for pool in self.candidate_pool_service.list_pools()]

    def get_candidate_pool(self, pool_id: str) -> dict:
        return self.candidate_pool_service.get(pool_id).model_dump(mode="json")

    def update_candidate_item(self, pool_id: str, item_id: str, status: str, note: str) -> dict:
        pool = self.candidate_pool_service.update_item(
            pool_id=pool_id,
            item_id=item_id,
            status=status,
            operator_note=note or None,
        )
        return pool.model_dump(mode="json")

    def list_accounts(self) -> list[dict]:
        return [account.model_dump(mode="json") for account in self.style_service.list_accounts()]

    def list_styles(self) -> list[dict]:
        return [style.model_dump(mode="json") for style in self.style_service.list_styles()]

    def create_draft(self, payload: dict) -> dict:
        llm = build_llm_client(self.settings)
        pipeline = GenerationPipeline(self.settings, llm)
        generated = pipeline.generate(GenerateCommentRequest(**payload))
        draft = self.draft_service.save(
            generated=generated,
            title=payload.get("title"),
            candidate_pool_id=payload.get("candidate_pool_id"),
            candidate_item_id=payload.get("candidate_item_id"),
        )
        return draft.model_dump(mode="json")

    def create_zhihu_draft(self, payload: dict) -> dict:
        from app.services.zhihu_answer_generator import ZhihuAnswerGenerator

        llm = build_llm_client(self.settings)
        generated = ZhihuAnswerGenerator(self.settings, llm).generate(GenerateZhihuAnswerRequest(**payload))
        draft = self.draft_service.save_zhihu_answer(
            generated=generated,
            title=payload.get("title"),
            candidate_pool_id=payload.get("candidate_pool_id"),
            candidate_item_id=payload.get("candidate_item_id"),
        )
        return draft.model_dump(mode="json")

    def list_drafts(self) -> list[dict]:
        return [draft.model_dump(mode="json") for draft in self.draft_service.list_drafts()]

    def get_draft(self, draft_id: str) -> dict:
        return self.draft_service.get(draft_id).model_dump(mode="json")

    def update_draft(self, draft_id: str, payload: dict) -> dict:
        draft = self.draft_service.update(
            draft_id=draft_id,
            status=payload.get("status"),
            operator_note=payload.get("operator_note"),
            edited_text=payload.get("edited_text"),
        )
        return draft.model_dump(mode="json")

    def ingest_knowledge(self, payload: dict) -> dict:
        result = KnowledgeIngestionService(self.settings).ingest(KnowledgeIngestRequest(**payload))
        return result.model_dump(mode="json")


def main() -> None:
    apply_streamlit_secrets_to_env()
    get_settings.cache_clear()

    st.set_page_config(page_title="HotComment-AI 工作台", layout="wide")
    st.title("HotComment-AI 内容运营工作台")
    st.caption("少数账号的人机协同选题、候选池与草稿工作流。")

    api_base_url = secret_or_env("API_BASE_URL", DEFAULT_API_BASE_URL)
    mode_options = ["本地服务模式", "FastAPI 模式"]
    default_mode = 1 if api_base_url else 0
    mode = st.sidebar.radio("运行模式", mode_options, index=default_mode)
    if mode == "FastAPI 模式":
        api_base_url = st.sidebar.text_input("FastAPI 地址", value=api_base_url or "http://127.0.0.1:8000")
        api = ApiClient(api_base_url)
        st.sidebar.caption("适合 Streamlit 连接独立 FastAPI 后端。")
    else:
        api = LocalServiceClient()
        st.sidebar.caption("适合 Streamlit Community Cloud：直接调用 app/services，不需要独立 FastAPI。")

    with st.sidebar:
        if st.button("检查连接", use_container_width=True):
            run_action(lambda: st.success(api.health()))

    tab_create, tab_pools, tab_drafts, tab_config = st.tabs(["生成候选池", "候选池审核", "草稿箱", "账号与风格"])

    with tab_create:
        render_create_pool(api)

    with tab_pools:
        render_candidate_pools(api)

    with tab_drafts:
        render_drafts(api)

    with tab_config:
        render_config(api)


def render_create_pool(api: ApiClient) -> None:
    st.subheader("从今日热搜生成候选池")
    st.write("抓取热搜前 50，AI 评分后保存为候选池。所有候选默认只进入审核状态，不自动生成发布内容。")

    with st.form("create_pool"):
        title = st.text_input("候选池标题", value="今日热搜候选池")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            max_results = st.slider("推荐数量", min_value=3, max_value=10, value=10)
        with col_b:
            source_limit = st.slider("热搜抓取数量", min_value=10, max_value=50, value=50)
        with col_c:
            research_limit = st.slider("二次采样数量", min_value=1, max_value=10, value=10)
        enrich_metrics = st.checkbox("启用二次采样", value=True)
        submitted = st.form_submit_button("生成并保存候选池", use_container_width=True)

    if submitted:
        payload = {
            "title": title,
            "max_results": max_results,
            "source_limit": source_limit,
            "enrich_metrics": enrich_metrics,
            "research_limit": research_limit,
        }

        def action() -> None:
            with st.spinner("正在抓热搜、评分并保存候选池..."):
                pool = api.create_candidate_pool(payload)
            st.session_state["current_pool_id"] = pool["id"]
            st.success(f"候选池已保存：{pool['id']}")
            render_pool_detail(pool)

        run_action(action)


def render_candidate_pools(api: ApiClient) -> None:
    st.subheader("候选池审核")

    if st.button("刷新候选池列表"):
        st.session_state.pop("pools_cache", None)

    def load_pools() -> list[dict]:
        if "pools_cache" not in st.session_state:
            st.session_state["pools_cache"] = api.list_candidate_pools()
        return st.session_state["pools_cache"]

    pools: list[dict] = []
    run_action(lambda: pools.extend(load_pools()))
    if not pools:
        st.info("还没有候选池。先到“生成候选池”创建一个。")
        return

    pool_options = {
        f"{pool['created_at']} | {pool['title']} | {pool['id']}": pool["id"]
        for pool in pools
    }
    default_id = st.session_state.get("current_pool_id")
    option_keys = list(pool_options.keys())
    default_index = 0
    if default_id:
        for index, key in enumerate(option_keys):
            if pool_options[key] == default_id:
                default_index = index
                break

    selected_label = st.selectbox("选择候选池", option_keys, index=default_index)
    pool_id = pool_options[selected_label]

    pool_holder: dict[str, Any] = {}
    run_action(lambda: pool_holder.update(api.get_candidate_pool(pool_id)))
    if not pool_holder:
        return

    render_pool_detail(pool_holder)
    render_status_editor(api, pool_holder)
    render_knowledge_ingestion(api, pool_holder)


def render_pool_detail(pool: dict) -> None:
    st.markdown(f"**候选池 ID：** `{pool['id']}`")
    st.markdown(f"**标题：** {pool['title']}")

    rows = []
    for index, item in enumerate(pool["items"], 1):
        rows.append(
            {
                "序号": index,
                "状态": item["status"],
                "话题": item["keyword"],
                "微博分": item.get("target_platform_scores", {}).get("weibo", item["score"]),
                "知乎分": item.get("target_platform_scores", {}).get("zhihu"),
                "推荐产线": " / ".join(item.get("recommended_targets") or []),
                "风险": item["risk_level"],
                "热搜排名": item.get("rank"),
                "推荐理由": item["reason"],
                "建议角度": item["recommended_angle"],
                "知乎问题": item.get("zhihu_question_title"),
                "备注": item.get("operator_note"),
                "item_id": item["id"],
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_status_editor(api: ApiClient, pool: dict) -> None:
    st.markdown("### 人工选择")
    item_labels = {
        f"{index}. {item['keyword']} ({item['status']})": item
        for index, item in enumerate(pool["items"], 1)
    }
    selected_item_labels = st.multiselect("选择一个或多个话题", list(item_labels.keys()))
    selected_items = [item_labels[label] for label in selected_item_labels]

    col_a, col_b = st.columns([1, 3])
    with col_a:
        status = st.selectbox(
            "状态",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index("selected"),
        )
    with col_b:
        note = st.text_input("人工备注", value="")

    if st.button("批量更新候选状态", use_container_width=True, disabled=not selected_items):
        def action() -> None:
            updated_pool = pool
            for item in selected_items:
                updated_pool = api.update_candidate_item(pool["id"], item["id"], status, note)
            st.session_state["current_pool_id"] = updated_pool["id"]
            st.session_state.pop("pools_cache", None)
            st.success(f"已更新 {len(selected_items)} 个候选话题。")
            render_pool_detail(updated_pool)

        run_action(action)


def render_knowledge_ingestion(api: ApiClient, pool: dict) -> None:
    st.markdown("### 背景资料入库")
    selected_items = [item for item in pool["items"] if item["status"] in {"selected", "researched"}]
    if not selected_items:
        st.info("先把候选话题标记为 selected，再补充背景资料。")
        return

    item_options = {
        f"{index + 1}. {item['keyword']} ({item['status']})": item
        for index, item in enumerate(selected_items)
    }
    item_label = st.selectbox("话题", list(item_options.keys()), key=f"knowledge_item_{pool['id']}")
    item = item_options[item_label]

    with st.form(f"knowledge_ingest_{pool['id']}_{item['id']}"):
        source_url = st.text_input("来源 URL", value=item.get("url") or "")
        source_title = st.text_input("来源标题", value="")
        credibility = st.selectbox("可信度", ["unknown", "medium", "high", "low"], index=0)
        content = st.text_area("背景资料/摘要/事实点", height=180)
        operator_note = st.text_input("人工备注", value="")
        col_a, col_b = st.columns(2)
        with col_a:
            needs_review = st.checkbox("需要后续核验", value=True)
        with col_b:
            rebuild_index = st.checkbox("保存后重建 RAG", value=True)
        submitted = st.form_submit_button("保存到知识库", use_container_width=True)

    if not submitted:
        return
    if not content.strip():
        st.warning("请先填写背景资料内容。")
        return

    payload = {
        "topic": item["keyword"],
        "content": content,
        "source_url": source_url or None,
        "source_title": source_title or None,
        "credibility": credibility,
        "needs_review": needs_review,
        "candidate_pool_id": pool["id"],
        "candidate_item_id": item["id"],
        "operator_note": operator_note or None,
        "rebuild_index": rebuild_index,
    }

    def action() -> None:
        with st.spinner("正在保存背景资料并更新知识库..."):
            result = api.ingest_knowledge(payload)
        st.success(f"背景资料已入库：{result['path']}")
        if result.get("rebuild_stats"):
            st.json(result["rebuild_stats"])

    run_action(action)


def render_drafts(api: ApiClient) -> None:
    st.subheader("草稿箱")
    st.write("从 selected 候选题生成草稿，保存为待人工审核状态。系统不自动发布。")

    render_create_draft_from_candidate(api)
    st.divider()
    render_draft_list(api)


def render_create_draft_from_candidate(api: ApiClient) -> None:
    st.markdown("### 从已选题生成草稿")

    pools: list[dict] = []
    run_action(lambda: pools.extend(api.list_candidate_pools()))
    if not pools:
        st.info("还没有候选池。先生成候选池并标记 selected。")
        return

    pool_options = {
        f"{pool['created_at']} | {pool['title']} | {pool['id']}": pool["id"]
        for pool in pools
    }
    pool_label = st.selectbox("候选池", list(pool_options.keys()), key="draft_pool_select")
    pool_id = pool_options[pool_label]

    pool_holder: dict[str, Any] = {}
    run_action(lambda: pool_holder.update(api.get_candidate_pool(pool_id)))
    if not pool_holder:
        return

    selected_items = [item for item in pool_holder["items"] if item["status"] == "selected"]
    if not selected_items:
        st.warning("这个候选池还没有 selected 话题。先到“候选池审核”里选择。")
        return

    item_options = {
        f"{index + 1}. {item['keyword']} | {item['score']}/100": item
        for index, item in enumerate(selected_items)
    }
    item_label = st.selectbox("selected 话题", list(item_options.keys()))
    item = item_options[item_label]

    accounts: list[dict] = []
    styles: list[dict] = []
    run_action(lambda: accounts.extend(api.list_accounts()))
    run_action(lambda: styles.extend(api.list_styles()))
    account_options = {f"{account['name']} ({account['id']})": account["id"] for account in accounts}
    style_options = {f"{style['name']} ({style['id']})": style["id"] for style in styles}

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        account_label = st.selectbox("账号", list(account_options.keys()))
    with col_b:
        style_label = st.selectbox("表达风格", list(style_options.keys()))
    with col_c:
        emotion_level = st.slider("情绪强度", min_value=1, max_value=10, value=6)

    default_context = "\n".join(
        [
            f"推荐理由：{item['reason']}",
            f"建议角度：{item['recommended_angle']}",
            "避坑点：" + "；".join(item.get("avoid_points") or []),
        ]
    )
    context_text = st.text_area("补充背景/写作要求", value=default_context, height=140)
    use_rag = st.checkbox("启用 RAG 检索", value=True)

    col_weibo, col_zhihu = st.columns(2)
    create_weibo = col_weibo.button("生成微博草稿", use_container_width=True)
    create_zhihu = col_zhihu.button("生成知乎回答", use_container_width=True)

    if create_weibo:
        payload = {
            "title": item["keyword"],
            "topic": item["keyword"],
            "account_id": account_options[account_label],
            "style": style_options[style_label],
            "emotion_level": emotion_level,
            "use_rag": use_rag,
            "context_text": context_text,
            "candidate_pool_id": pool_holder["id"],
            "candidate_item_id": item["id"],
        }

        def action() -> None:
            with st.spinner("正在生成草稿并保存..."):
                draft = api.create_draft(payload)
            st.success(f"草稿已保存：{draft['id']}")
            render_draft_detail(draft)

        run_action(action)

    if create_zhihu:
        payload = {
            "title": item["keyword"],
            "topic": item["keyword"],
            "question_title": item.get("zhihu_question_title") or f"如何看待{item['keyword']}？",
            "account_id": account_options[account_label],
            "style": style_options[style_label],
            "emotion_level": emotion_level,
            "use_rag": use_rag,
            "context_text": build_zhihu_context(item, context_text),
            "candidate_pool_id": pool_holder["id"],
            "candidate_item_id": item["id"],
        }

        def action() -> None:
            with st.spinner("正在生成知乎回答并保存..."):
                draft = api.create_zhihu_draft(payload)
            st.success(f"知乎回答草稿已保存：{draft['id']}")
            render_draft_detail(draft)

        run_action(action)


def render_draft_list(api: ApiClient) -> None:
    st.markdown("### 已保存草稿")
    if st.button("刷新草稿列表"):
        st.session_state.pop("drafts_cache", None)

    def load_drafts() -> list[dict]:
        if "drafts_cache" not in st.session_state:
            st.session_state["drafts_cache"] = api.list_drafts()
        return st.session_state["drafts_cache"]

    drafts: list[dict] = []
    run_action(lambda: drafts.extend(load_drafts()))
    if not drafts:
        st.info("还没有草稿。")
        return

    platform_options = ["全部"] + sorted({draft.get("platform", "weibo") for draft in drafts})
    type_options = ["全部"] + sorted({draft.get("draft_type", "micro_comment") for draft in drafts})
    status_options = ["全部"] + sorted({draft.get("status", "draft") for draft in drafts})
    col_platform, col_type, col_status = st.columns(3)
    with col_platform:
        selected_platform = st.selectbox("平台筛选", platform_options)
    with col_type:
        selected_type = st.selectbox("类型筛选", type_options)
    with col_status:
        selected_status = st.selectbox("状态筛选", status_options)

    filtered_drafts = [
        draft
        for draft in drafts
        if (selected_platform == "全部" or draft.get("platform", "weibo") == selected_platform)
        and (selected_type == "全部" or draft.get("draft_type", "micro_comment") == selected_type)
        and (selected_status == "全部" or draft.get("status", "draft") == selected_status)
    ]
    st.caption(f"当前显示 {len(filtered_drafts)} / {len(drafts)} 条草稿")
    if not filtered_drafts:
        st.info("当前筛选条件下没有草稿。")
        return

    rows = [
        {
            "标题": draft["title"],
            "话题": draft["topic"],
            "平台": draft.get("platform", "weibo"),
            "类型": draft.get("draft_type", "micro_comment"),
            "状态": draft["status"],
            "风险": draft["risk_level"],
            "风格": draft["style"],
            "发布链接": draft.get("published_url") or "",
            "更新时间": draft["updated_at"],
            "draft_id": draft["id"],
        }
        for draft in filtered_drafts
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    draft_options = {
        f"{draft['updated_at']} | {draft.get('platform', 'weibo')} | {draft.get('draft_type', 'micro_comment')} | {draft['title']} | {draft['id']}": draft["id"]
        for draft in filtered_drafts
    }
    draft_label = st.selectbox("查看/编辑草稿", list(draft_options.keys()))
    draft_id = draft_options[draft_label]

    draft_holder: dict[str, Any] = {}
    run_action(lambda: draft_holder.update(api.get_draft(draft_id)))
    if draft_holder:
        render_draft_detail(draft_holder)
        render_draft_editor(api, draft_holder)


def render_draft_detail(draft: dict) -> None:
    st.markdown(f"**草稿 ID：** `{draft['id']}`")
    st.markdown(f"**话题：** {draft['topic']}")
    st.markdown(
        f"**状态：** {draft['status']} | **平台：** {draft.get('platform', 'weibo')} | "
        f"**类型：** {draft.get('draft_type', 'micro_comment')} | **风险：** {draft['risk_level']} | **风格：** {draft['style']}"
    )

    if draft.get("draft_type") == "zhihu_answer":
        output = draft["zhihu_answer"]["output"]
        st.markdown("#### 知乎回答")
        st.markdown(f"**问题：** {output.get('question_title', '')}")
        st.markdown(f"**标题：** {output.get('answer_title', '')}")
        st.write(output.get("answer_body", ""))
        with st.expander("结构化要点"):
            st.markdown("**开场判断：**")
            st.write(output.get("opening_judgement", ""))
            st.markdown("**背景摘要：**")
            st.write(output.get("background_summary", ""))
            st.markdown("**核心论点：**")
            st.write(output.get("core_argument", ""))
            st.markdown("**支撑点：**")
            for point in output.get("supporting_points", []):
                st.write(f"- {point}")
            st.markdown("**风险提示：**")
            for note in output.get("risk_notes", []):
                st.write(f"- {note}")
    else:
        output = draft["generated"]["output"]
        st.markdown("#### 推荐正文")
        st.write(output.get("short_comment", ""))
        with st.expander("其他版本"):
            st.markdown("**一句话：**")
            st.write(output.get("one_liner", ""))
            st.markdown("**情绪版：**")
            st.write(output.get("emotional_version", ""))
            st.markdown("**理性版：**")
            st.write(output.get("rational_version", ""))
            st.markdown("**阴阳怪气版：**")
            st.write(output.get("ironic_version", ""))
            st.markdown("**评论区回复：**")
            for reply in output.get("comment_replies", []):
                st.write(f"- {reply}")

    if draft.get("edited_text"):
        st.markdown("#### 人工编辑版")
        st.write(draft["edited_text"])
    if draft.get("operator_note"):
        st.markdown("#### 人工备注")
        st.write(draft["operator_note"])
    if draft.get("published_url"):
        st.markdown("#### 人工发布记录")
        published_at = draft.get("published_at")
        if published_at:
            st.write(f"发布时间：{published_at}")
        st.write(draft["published_url"])
        if draft.get("performance_note"):
            st.write(draft["performance_note"])


def render_draft_editor(api: ApiClient, draft: dict) -> None:
    st.markdown("### 审核/编辑")
    col_a, col_b = st.columns([1, 3])
    with col_a:
        status = st.selectbox(
            "草稿状态",
            DRAFT_STATUS_OPTIONS,
            index=DRAFT_STATUS_OPTIONS.index(draft["status"]),
        )
    with col_b:
        note = st.text_input("审核备注", value=draft.get("operator_note") or "")
    edited_text = st.text_area(
        "人工编辑正文",
        value=draft.get("edited_text") or draft_display_text(draft),
        height=260 if draft.get("draft_type") == "zhihu_answer" else 160,
    )
    published_url = st.text_input("人工发布链接", value=draft.get("published_url") or "")
    published_at = st.text_input("人工发布时间", value=draft.get("published_at") or "")
    performance_note = st.text_area("发布数据/复盘备注", value=draft.get("performance_note") or "", height=90)
    if st.button("保存草稿修改", use_container_width=True):
        payload = {
            "status": status,
            "operator_note": note,
            "edited_text": edited_text,
            "published_url": published_url or None,
            "published_at": published_at or None,
            "performance_note": performance_note or None,
        }

        def action() -> None:
            updated = api.update_draft(draft["id"], payload)
            st.session_state.pop("drafts_cache", None)
            st.success("草稿已更新。")
            render_draft_detail(updated)

        run_action(action)


def draft_display_text(draft: dict) -> str:
    if draft.get("draft_type") == "zhihu_answer":
        return draft.get("zhihu_answer", {}).get("output", {}).get("answer_body", "")
    return draft.get("generated", {}).get("output", {}).get("short_comment", "")


def build_zhihu_context(item: dict, context_text: str) -> str:
    parts = [
        context_text,
        "",
        f"知乎回答角度：{item.get('zhihu_answer_angle') or ''}",
        f"知乎适配理由：{item.get('zhihu_reason') or ''}",
    ]
    required_research = item.get("zhihu_required_research") or []
    if required_research:
        parts.append("知乎回答前建议补充资料：")
        parts.extend(f"- {entry}" for entry in required_research)
    return "\n".join(part for part in parts if part is not None)


def render_config(api: ApiClient) -> None:
    st.subheader("账号与表达风格")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 账号")

        def show_accounts() -> None:
            accounts = api.list_accounts()
            for account in accounts:
                with st.expander(f"{account['name']} ({account['id']})", expanded=True):
                    st.write(account["positioning"])
                    st.json(account)

        run_action(show_accounts)

    with col_b:
        st.markdown("### 表达风格")

        def show_styles() -> None:
            styles = api.list_styles()
            for style in styles:
                with st.expander(f"{style['name']} ({style['id']})"):
                    st.write(style.get("description", ""))
                    st.write("适合：" + "、".join(style.get("best_for", [])))

        run_action(show_styles)


def run_action(action) -> None:
    try:
        action()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        st.error(f"后端请求失败：{exc.response.status_code} {detail}")
    except httpx.RequestError as exc:
        st.error(f"无法连接后端：{exc}")
    except Exception as exc:
        st.error(f"操作失败：{exc}")


def secret_or_env(key: str, default: str = "") -> str:
    if key in os.environ:
        return os.environ[key]
    try:
        value = st.secrets.get(key)
        if value is not None:
            return str(value)
    except Exception:
        pass
    return default


def apply_streamlit_secrets_to_env() -> None:
    keys = [
        "LLM_PROVIDER",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
        "USE_OPENAI_EMBEDDINGS",
        "OPENAI_EMBEDDING_MODEL",
        "REQUEST_TIMEOUT_SECONDS",
        "KNOWLEDGE_DIR",
        "RAG_INDEX_PATH",
        "WEIBO_COOKIE",
        "API_BASE_URL",
    ]
    for key in keys:
        if key in os.environ:
            continue
        try:
            value = st.secrets.get(key)
        except Exception:
            value = None
        if value is not None:
            os.environ[key] = str(value)


if __name__ == "__main__":
    main()
