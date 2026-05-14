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
from app.services.candidate_pool_service import CandidatePoolService
from app.services.hot_search_service import HotSearchService
from app.services.style_service import StyleService
from app.services.topic_research_service import TopicResearchService
from app.services.topic_selection_service import TopicSelectionService


DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "")
STATUS_OPTIONS = ["candidate", "selected", "skipped", "researched"]


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


class LocalServiceClient:
    def __init__(self):
        self.settings = get_settings()
        self.candidate_pool_service = CandidatePoolService()
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

    tab_create, tab_pools, tab_config = st.tabs(["生成候选池", "候选池审核", "账号与风格"])

    with tab_create:
        render_create_pool(api)

    with tab_pools:
        render_candidate_pools(api)

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
                "评分": item["score"],
                "风险": item["risk_level"],
                "热搜排名": item.get("rank"),
                "推荐理由": item["reason"],
                "建议角度": item["recommended_angle"],
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
    selected_item_label = st.selectbox("选择话题", list(item_labels.keys()))
    item = item_labels[selected_item_label]

    col_a, col_b = st.columns([1, 3])
    with col_a:
        status = st.selectbox(
            "状态",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(item["status"]),
        )
    with col_b:
        note = st.text_input("人工备注", value=item.get("operator_note") or "")

    if st.button("更新候选状态", use_container_width=True):
        def action() -> None:
            updated_pool = api.update_candidate_item(pool["id"], item["id"], status, note)
            st.session_state["current_pool_id"] = updated_pool["id"]
            st.session_state.pop("pools_cache", None)
            st.success("状态已更新。")
            render_pool_detail(updated_pool)

        run_action(action)


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
